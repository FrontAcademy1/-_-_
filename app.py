from fastapi import FastAPI, Form
from fastapi.responses import HTMLResponse
import os

app = FastAPI(title="SPRIX AI Learning Assistant")

HTML = r"""
<!doctype html>
<html lang="ar" dir="rtl">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>SPRIX AI Learning Assistant</title>
<style>
*{box-sizing:border-box}
body{margin:0;font-family:Arial,sans-serif;background:#f5f7fb;color:#172033}
.wrap{min-height:100vh;display:flex;align-items:center;justify-content:center;padding:20px}
.card{width:min(460px,100%);background:white;border-radius:20px;padding:28px;box-shadow:0 12px 40px #0001}
h1{margin:0 0 8px;font-size:28px}
p{color:#687386}
label{display:block;margin:14px 0 7px;font-weight:700}
input{width:100%;padding:14px;border:1px solid #d8deea;border-radius:12px;font-size:16px}
button{width:100%;margin-top:18px;padding:14px;border:0;border-radius:12px;background:#2563eb;color:white;font-size:16px;font-weight:700}
.msg{margin-top:16px;padding:12px;border-radius:10px;background:#eef4ff}
.ok{background:#ecfdf3;color:#166534}
.err{background:#fef2f2;color:#991b1b}
.small{font-size:13px}
</style>
</head>
<body>
<div class="wrap">
<div class="card">
<h1>SPRIX AI Learning Assistant</h1>
<p>مساعد تعليمي محلي للتجربة والتطوير.</p>
<form method="post" action="/login">
<label>كود الطالب</label>
<input name="student_code" autocomplete="username" required>
<label>كلمة المرور</label>
<input name="password" type="password" autocomplete="current-password" required>
<button type="submit">تسجيل الدخول</button>
</form>
<div class="msg small">
هذا الإصدار لا يسجّل الدخول تلقائيًا إلى أي منصة خارجية ولا يرسل بيانات الحساب إليها.
</div>
</div>
</div>
</body>
</html>
"""

@app.get("/", response_class=HTMLResponse)
async def home():
    return HTML

@app.post("/login", response_class=HTMLResponse)
async def login(student_code: str = Form(...), password: str = Form(...)):
    # Demo/local authentication only.
    # Replace this with your own database authentication if needed.
    if not student_code.strip() or not password:
        return HTMLResponse(
            HTML.replace(
                '<div class="msg small">',
                '<div class="msg err">أدخل كود الطالب وكلمة المرور.</div><div class="msg small">'
            ),
            status_code=400,
        )

    safe_code = student_code.replace("<", "&lt;").replace(">", "&gt;")
    dashboard = f"""
    <!doctype html><html lang="ar" dir="rtl"><meta charset="utf-8">
    <meta name="viewport" content="width=device-width,initial-scale=1">
    <title>لوحة الطالب</title>
    <style>
    body{{font-family:Arial;background:#f5f7fb;margin:0;padding:25px}}
    .card{{max-width:700px;margin:auto;background:white;padding:25px;border-radius:18px;box-shadow:0 10px 30px #0001}}
    </style>
    <div class="card">
      <h1>مرحبًا 👋</h1>
      <p>تم تسجيل الدخول محليًا.</p>
      <p><b>كود الطالب:</b> {safe_code}</p>
      <hr>
      <h2>المساعد التعليمي</h2>
      <p>يمكنك هنا إضافة الدروس والأسئلة والشرح والتقييم الخاص بتطبيقك.</p>
      <a href="/">العودة</a>
    </div>
    """
    return HTMLResponse(dashboard)

@app.get("/health")
async def health():
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.getenv("PORT", "8001")))
