import os,re,httpx
from playwright.async_api import async_playwright
SPRIX='https://sprixportal.jp/'
AI_BASE=os.getenv('AI_BASE_URL','https://api.openai.com/v1').rstrip('/')
AI_KEY=os.getenv('AI_API_KEY',''); AI_MODEL=os.getenv('AI_MODEL','')
HEADLESS=os.getenv('HEADLESS','false').lower()=='true'
class BrowserAgent:
 def __init__(self): self.pw=self.browser=self.context=self.page=None; self.logged_in=False; self.selected=None; self.last_question=''; self.last_answer=''; self.logs=[]
 def log(self,x): self.logs=(self.logs+[x])[-50:]
 async def ensure_browser(self):
  if self.page and not self.page.is_closed(): return
  self.pw=await async_playwright().start(); self.browser=await self.pw.chromium.launch(headless=HEADLESS)
  self.context=await self.browser.new_context(viewport={'width':1440,'height':1000}); self.page=await self.context.new_page()
 async def login(self,student_id,password):
  try:
   await self.ensure_browser(); await self.page.goto(SPRIX,wait_until='domcontentloaded',timeout=30000)
   links=await self.page.locator('a').evaluate_all("els=>els.map(a=>({text:(a.innerText||'').trim(),href:a.href})).filter(x=>x.href)")
   target=next((x['href'] for x in links if 'qureo' in x['href'].lower()),None)
   if not target: return {'ok':False,'error':'لم أجد رابط منصة البرمجة في بوابة SPRIX.'}
   await self.page.goto(target,wait_until='domcontentloaded',timeout=30000)
   pw=self.page.locator('input[type="password"]').first; await pw.wait_for(state='visible',timeout=10000)
   inputs=self.page.locator("input:not([type='password']):not([type='hidden'])"); user=None
   for i in range(await inputs.count()):
    if await inputs.nth(i).is_visible(): user=inputs.nth(i); break
   if not user: return {'ok':False,'error':'لم أجد خانة كود الطالب.'}
   await user.fill(student_id); await pw.fill(password)
   buttons=self.page.locator('button,input[type="submit"]'); clicked=False
   for i in range(await buttons.count()):
    b=buttons.nth(i)
    if not await b.is_visible(): continue
    s=((await b.inner_text())+' '+str(await b.get_attribute('aria-label'))+' '+str(await b.get_attribute('value'))).lower()
    if any(k in s for k in ['login','sign in','تسجيل','دخول']): await b.click(); clicked=True; break
   if not clicked: await pw.press('Enter')
   await self.page.wait_for_timeout(2500)
   body=(await self.page.locator('body').inner_text())[:12000].lower()
   if any(k in body for k in ['captcha','recaptcha','two-factor','verification code','رمز التحقق']): return {'ok':False,'error':'يوجد تحقق إضافي. أكمله يدويًا؛ لا يتم تجاوزه.'}
   self.logged_in=True; self.log('تم تسجيل الدخول.'); return {'ok':True,'sections':await self.discover_sections()}
  except Exception as e: return {'ok':False,'error':str(e)}
 async def discover_sections(self):
  if not self.page or self.page.is_closed(): return []
  links=await self.page.locator('a').evaluate_all("els=>els.map(a=>({text:(a.innerText||'').trim(),href:a.href})).filter(x=>x.href&&x.text)")
  keys=['البرمجة','تكنولوجيا','التثقيف المالي','منصة','learning','programming','finance','qureo']; out=[]; seen=set()
  for x in links:
   if any(k.lower() in (x['text']+' '+x['href']).lower() for k in keys) and x['href'] not in seen:
    seen.add(x['href']); out.append({'name':re.sub(r'\\s+',' ',x['text'])[:100],'url':x['href']})
  return out[:30]
 async def select_section(self,url):
  if not self.logged_in:return {'ok':False,'error':'سجل الدخول أولًا.'}
  try:
   await self.page.goto(url,wait_until='domcontentloaded',timeout=30000); await self.page.wait_for_timeout(1200); self.selected=url
   return {'ok':True,'url':self.page.url,'title':await self.page.title()}
  except Exception as e:return {'ok':False,'error':str(e)}
 async def get_question(self):
  best=''
  for sel in ["[role='main']",'main','article','.question',"[class*='question']"]:
   try:
    loc=self.page.locator(sel)
    for i in range(min(await loc.count(),5)):
     if await loc.nth(i).is_visible():
      t=(await loc.nth(i).inner_text()).strip()
      if len(t)>len(best): best=t
   except: pass
  if len(best)<20: best=(await self.page.locator('body').inner_text())[:12000]
  return re.sub(r'\\n{3,}','\\n\\n',best).strip()
 async def solve_current(self):
  if not self.page or self.page.is_closed(): return {'ok':False,'error':'لا توجد جلسة متصفح.'}
  q=await self.get_question(); self.last_question=q
  if not AI_KEY or not AI_MODEL: return {'ok':True,'question':q,'answer':'','message':'ضع AI_API_KEY وAI_MODEL في .env.'}
  try:
   async with httpx.AsyncClient(timeout=60) as c:
    r=await c.post(AI_BASE+'/chat/completions',headers={'Authorization':'Bearer '+AI_KEY},json={'model':AI_MODEL,'temperature':0.1,'messages':[{'role':'system','content':'أنت مدرس يساعد الطالب على فهم السؤال وحله. اذكر الإجابة بوضوح مع شرح مختصر.'},{'role':'user','content':q}]}); r.raise_for_status(); ans=r.json()['choices'][0]['message']['content'].strip()
   self.last_answer=ans; self.log('تم حل السؤال بالـAI.'); return {'ok':True,'question':q,'answer':ans,'url':self.page.url}
  except Exception as e:return {'ok':False,'error':f'AI error: {e}','question':q}
 def status(self): return {'ok':True,'logged_in':self.logged_in,'url':self.page.url if self.page and not self.page.is_closed() else None,'selected':self.selected,'question':self.last_question,'answer':self.last_answer,'logs':self.logs}
 async def close(self):
  for obj,method in [(self.context,'close'),(self.browser,'close'),(self.pw,'stop')]:
   try:
    if obj: await getattr(obj,method)()
   except: pass
  self.page=self.context=self.browser=self.pw=None; self.logged_in=False
