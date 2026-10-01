from pathlib import Path
from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from dotenv import load_dotenv
from browser_agent import BrowserAgent
load_dotenv()
app=FastAPI(title='SPRIX AI Learning Assistant')
app.mount('/static',StaticFiles(directory='static'),name='static')
agent=BrowserAgent()
@app.get('/',response_class=HTMLResponse)
async def home(): return Path('templates/index.html').read_text(encoding='utf-8')
@app.post('/api/login')
async def login(student_id:str=Form(...),password:str=Form(...)): return await agent.login(student_id.strip(),password)
@app.get('/api/sections')
async def sections(): return {'ok':True,'sections':await agent.discover_sections()}
@app.post('/api/select-section')
async def select_section(url:str=Form(...)): return await agent.select_section(url)
@app.post('/api/solve')
async def solve(): return await agent.solve_current()
@app.get('/api/status')
async def status(): return agent.status()
@app.post('/api/stop')
async def stop(): await agent.close(); return {'ok':True}
@app.get('/health')
async def health(): return {'ok':True}
