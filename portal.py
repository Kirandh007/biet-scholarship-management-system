from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import base64, json, os, secrets, sqlite3, time
from urllib import parse, request

DB='akshara_portal.db'
SESSIONS={}
OTPS={}
APP='AKSHARA BIET Scholarship Management System'
LOGO='data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHZpZXdCb3g9IjAgMCA5MDAgNTIwIj48ZGVmcz48bGluZWFyR3JhZGllbnQgaWQ9ImciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj48c3RvcCBzdG9wLWNvbG9yPSIjMDA1YmQ2Ii8+PHN0b3Agb2Zmc2V0PSIuNTUiIHN0b3AtY29sb3I9IiMwMDU3YjgiLz48c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiNmZjViMWEiLz48L2xpbmVhckdyYWRpZW50PjxmaWx0ZXIgaWQ9InMiIHg9Ii0yMCUiIHk9Ii0yMCUiIHdpZHRoPSIxNDAlIiBoZWlnaHQ9IjE0MCUiPjxmZURyb3BTaGFkb3cgZHg9IjAiIGR5PSIxOCIgc3RkRGV2aWF0aW9uPSIxOCIgZmxvb2QtY29sb3I9IiMwMDIxNGQiIGZsb29kLW9wYWNpdHk9Ii4yNCIvPjwvZmlsdGVyPjwvZGVmcz48cmVjdCB3aWR0aD0iOTAwIiBoZWlnaHQ9IjUyMCIgcng9IjM4IiBmaWxsPSIjZjVmOWZmIi8+PGcgZmlsdGVyPSJ1cmwoI3MpIj48cGF0aCBkPSJNMjYwIDIxMGM3MC00MiAxMzAtNDIgMTkwIDAgNjAtNDIgMTIwLTQyIDE5MCAwdjEwNWMtNzItMzktMTM2LTM5LTE5MCA0LTU0LTQzLTExOC00My0xOTAtNHoiIGZpbGw9IiMwMDY2ZDkiLz48cGF0aCBkPSJNNDUwIDgwbDM0IDcyIDgwIDExLTU4IDU2IDE0IDgwLTcwLTM4LTcwIDM4IDE0LTgwLTU4LTU2IDgwLTExeiIgZmlsbD0iI2ZmOWIxMyIvPjxwYXRoIGQ9Ik00NTAgMTUwbDExMiA0OC0xMTIgNDgtMTEyLTQ4eiIgZmlsbD0iI2ZmN2EwMCIvPjxwYXRoIGQ9Ik0zODYgMjE0djUxbDY0IDM0IDY0LTM0di01MWwtNjQgMzB6IiBmaWxsPSIjMDAzMjc4Ii8+PC9nPjx0ZXh0IHg9IjQ1MCIgeT0iNDA1IiB0ZXh0LWFuY2hvcj0ibWlkZGxlIiBmb250LXNpemU9IjkyIiBmb250LWZhbWlseT0iQXJpYWwgQmxhY2ssQXJpYWwsc2Fucy1zZXJpZiIgZmlsbD0idXJsKCNnKSI+QUtTSEFSQTwvdGV4dD48dGV4dCB4PSI0NTAiIHk9IjQ1NSIgdGV4dC1hbmNob3I9Im1pZGRsZSIgZm9udC1zaXplPSIzMSIgZm9udC1mYW1pbHk9IkFyaWFsLHNhbnMtc2VyaWYiIGZpbGw9IiMxODI3M2QiPkJJRVQgU2Nob2xhcnNoaXAgTWFuYWdlbWVudCBTeXN0ZW08L3RleHQ+PC9zdmc+'
STUDENTS=[('Adithi H','9000044444','CSE','AKS-CS-001',9.4,180000),('Sahana K','9000055555','ISE','AKS-IS-002',9.1,160000),('Namana','9000066666','ECE','AKS-EC-003',8.8,220000),('Sampreethi','9000077777','AI&ML','AKS-AI-004',9.0,140000),('Akash R','9000088888','Mechanical','AKS-ME-005',8.3,250000),('Gourav H','9000099999','Civil','AKS-CV-006',8.6,130000),('Minnu K','9000100000','ECE','AKS-EC-007',8.9,190000)]
PROFESSORS=[('Dr Pradeep N','9000011111','admin','Chairperson'),('Usha C','9000022222','reviewer','Scholarship Reviewer'),('Gowri B','9000033333','reviewer','Academic Reviewer')]

def ph(x): return ''.join(c for c in str(x or '') if c.isdigit())[-10:]
def con():
    c=sqlite3.connect(DB); c.row_factory=sqlite3.Row; return c
def rows(cur): return [dict(r) for r in cur.fetchall()]
def appno(i): return f'AKS-BIET-2026-{int(i):05d}'

def seed():
    with con() as c:
        c.executescript('''create table if not exists users(id integer primary key, name text, phone text unique, role text, dept text);
        create table if not exists profiles(user_id integer unique, roll text, course text, cgpa real, income integer);
        create table if not exists scholarships(id integer primary key, title text, provider text, amount integer, min_cgpa real, max_income integer, seats integer, deadline text, status text, eligibility text);
        create table if not exists applications(id integer primary key, student_id integer, scholarship_id integer, purpose text, status text, score integer, updated text default current_timestamp, unique(student_id,scholarship_id));''')
        if c.execute('select count(*) n from users').fetchone()['n']: return
        uid=1
        for name,phone,role,dept in PROFESSORS:
            c.execute('insert into users values(?,?,?,?,?)',(uid,name,phone,role,dept)); uid+=1
        for name,phone,course,roll,cgpa,income in STUDENTS:
            c.execute('insert into users values(?,?,?,?,?)',(uid,name,phone,'student',course))
            c.execute('insert into profiles values(?,?,?,?,?)',(uid,roll,course,cgpa,income)); uid+=1
        sch=[('AKSHARA Prime Merit Scholarship','BIET Scholarship Council',75000,8.5,250000,35,'31 Aug 2026','open','CGPA 8.5+, income below Rs 2.5L, no active backlog.'),('AKSHARA Women in Engineering Grant','BIET Alumni Endowment',60000,8.0,300000,25,'15 Sep 2026','open','Women students with strong academics and leadership record.'),('AKSHARA Need Based Assistance','Student Welfare Office',50000,7.5,180000,40,'20 Sep 2026','open','Verified income certificate and academic proof required.')]
        c.executemany('insert into scholarships(title,provider,amount,min_cgpa,max_income,seats,deadline,status,eligibility) values(?,?,?,?,?,?,?,?,?)',sch)
        for sid in range(4,11): c.execute('insert into applications(student_id,scholarship_id,purpose,status,score) values(?,?,?,?,?)',(sid,1+((sid-4)%3),'Requesting academic financial assistance through AKSHARA portal.','submitted' if sid%3 else 'under_review',78+sid))

def ensure_user(phone):
    phone=ph(phone)
    if len(phone)!=10: return None
    with con() as c:
        u=c.execute('select id from users where phone=?',(phone,)).fetchone()
        if not u:
            c.execute('insert into users(name,phone,role,dept) values(?,?,?,?)',(f'New Student {phone[-4:]}',phone,'student','Pending Verification'))
            u=c.execute('select id from users where phone=?',(phone,)).fetchone()
        return dict(u)

def twilio_ready(): return all(os.getenv(k) for k in ('TWILIO_ACCOUNT_SID','TWILIO_AUTH_TOKEN','TWILIO_VERIFY_SERVICE_SID'))
def twilio_post(path,data):
    sid=os.getenv('TWILIO_ACCOUNT_SID'); token=os.getenv('TWILIO_AUTH_TOKEN'); service=os.getenv('TWILIO_VERIFY_SERVICE_SID')
    req=request.Request(f'https://verify.twilio.com/v2/Services/{service}/{path}',data=parse.urlencode(data).encode(),method='POST')
    req.add_header('Content-Type','application/x-www-form-urlencoded')
    req.add_header('Authorization','Basic '+base64.b64encode(f'{sid}:{token}'.encode()).decode())
    with request.urlopen(req,timeout=15) as r: return json.loads(r.read().decode())
def send_otp(phone):
    phone=ph(phone)
    if twilio_ready():
        twilio_post('Verifications',{'To':'+91'+phone,'Channel':'sms'})
        return {'mode':'sms','message':'OTP sent to your mobile number.'}
    code=str(secrets.randbelow(900000)+100000); OTPS[phone]=(code,time.time()+300)
    return {'mode':'demo','message':'Twilio env not configured, demo OTP generated.','dev_otp':code}
def ok_otp(phone,code):
    phone=ph(phone)
    if twilio_ready(): return twilio_post('VerificationCheck',{'To':'+91'+phone,'Code':str(code) or ''}).get('status')=='approved'
    saved=OTPS.get(phone); return bool(saved and saved[0]==str(code).strip() and saved[1]>time.time())

HTML='''<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AKSHARA BIET Scholarship Management System</title><style>
*{box-sizing:border-box}body{margin:0;font-family:Segoe UI,Arial,sans-serif;color:#071a33;background:#eef4fb}button,input{font:inherit}button{cursor:pointer}.login{min-height:100vh;display:grid;grid-template-columns:1.2fr .8fr;background:linear-gradient(120deg,#12386d,#3e91e7);color:#fff}.hero{align-self:center;padding:64px 80px}.hero img{width:330px;max-width:82vw;background:#fff;border-radius:18px;padding:14px;box-shadow:0 24px 55px #08234f55}.hero h1{font-size:76px;line-height:1.02;margin:28px 0}.hero p{font-size:24px;line-height:1.5}.metrics{display:flex;gap:14px;flex-wrap:wrap}.metrics span{border:1px solid #ffffff55;background:#ffffff18;padding:14px 18px;font-weight:800}.card{align-self:center;margin:40px 70px;background:#fff;color:#071a33;padding:32px;border-radius:8px;box-shadow:0 22px 60px #08234f44}.head{display:flex;gap:18px;align-items:center}.head img,.brand img{width:86px;background:#fff;border-radius:12px;border:1px solid #dbe5ef}.eyebrow{color:#ff6b00;text-transform:uppercase;font-weight:900;letter-spacing:.08em}label{display:block;font-weight:800;margin:22px 0 8px}input{width:100%;padding:16px;border:1px solid #d5e0ea}button.primary{width:100%;padding:16px;border:0;background:linear-gradient(135deg,#06306c,#0767d8);color:white;font-weight:900;margin-top:18px}.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:10px;margin:18px 0}.quick button{border:1px solid #dbe5ef;background:#f8fbff;padding:13px;font-weight:900}.warn{border:1px solid #ffc36e;background:#fff7eb;color:#7b3c00;padding:14px}.error{font-weight:800;color:#c0392b}.hidden{display:none}.top{display:flex;justify-content:space-between;align-items:center;background:#071a33;color:#fff;padding:18px 28px}.brand{display:flex;gap:15px;align-items:center}.brand h2{margin:0}.brand p{margin:3px 0;color:#b9cce2}.logout{background:transparent;color:#fff;border:1px solid #ffffff55;padding:10px 14px}.content{max-width:1400px;margin:auto;padding:24px}.alert{background:#fff7eb;border:1px solid #ffc36e;padding:14px;margin-bottom:18px}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin-bottom:18px}.tabs button{border:1px solid #dbe5ef;background:#fff;padding:12px 16px;font-weight:900}.tabs .active{background:#071a33;color:#fff}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.panel,.item{background:#fff;border:1px solid #dbe5ef;padding:18px;border-radius:8px;box-shadow:0 10px 25px #10203312}.stat b{font-size:34px}.list{display:grid;gap:12px}.row{display:grid;grid-template-columns:1.3fr .8fr .8fr .8fr;gap:12px;border-top:1px solid #dbe5ef;padding:12px 0}.row:first-child{border-top:0}.pill{display:inline-block;border-radius:999px;background:#eaf3ff;color:#084894;padding:6px 10px;font-weight:900}@media(max-width:900px){.login,.grid{grid-template-columns:1fr}.hero,.card{margin:0;padding:28px}.hero h1{font-size:46px}.quick,.row{grid-template-columns:1fr}}
</style></head><body><main id="app"></main><script>
const LOGO='__LOGO__', app=document.querySelector('#app'); let state={view:'dashboard'}; const money=n=>new Intl.NumberFormat('en-IN',{style:'currency',currency:'INR',maximumFractionDigits:0}).format(n||0);
async function api(p,o={}){let r=await fetch(p,{headers:{'Content-Type':'application/json'},credentials:'same-origin',...o});let d=await r.json().catch(()=>({}));if(!r.ok)throw Error(d.error||'Request failed');return d}
function login(){app.innerHTML=`<section class="login"><div class="hero"><img src="${LOGO}" alt="AKSHARA"><p class="eyebrow">BIET Digital Scholarship Cell</p><h1>AKSHARA BIET Scholarship Management System</h1><p>Professional DBMS portal for merit awards, need-based aid, OTP access, review, verification and fund disbursement.</p><div class="metrics"><span>AKS-2026 unique numbers</span><span>OTP mobile login</span><span>31 Aug final deadline</span></div></div><form class="card" id="f"><div class="head"><img src="${LOGO}" alt="AKSHARA"><div><p class="eyebrow">Secure OTP Access</p><h2>Sign in with mobile</h2></div></div><label>Registered or new mobile number</label><input name="phone" value="9000055555" maxlength="14"><button class="primary">Send OTP</button><label class="otp hidden">Enter OTP</label><input class="otp hidden" name="otp" maxlength="6"><button type="button" class="primary otp hidden" id="verify">Verify and Login</button><div class="quick"><button type="button" data-p="9000044444">Adithi</button><button type="button" data-p="9000055555">Sahana</button><button type="button" data-p="9000011111">Principal</button></div><div class="warn"><b>Warning:</b> Do not share OTP, application number, income certificate, bank details or login access.</div><p id="msg" class="error"></p></form></section>`; f.onsubmit=async e=>{e.preventDefault();try{let d=await api('/api/request-otp',{method:'POST',body:JSON.stringify({phone:f.phone.value})});document.querySelectorAll('.otp').forEach(x=>x.classList.remove('hidden'));msg.textContent=d.dev_otp?'Demo OTP: '+d.dev_otp:d.message}catch(x){msg.textContent=x.message}}; verify.onclick=async()=>{try{await api('/api/verify-otp',{method:'POST',body:JSON.stringify({phone:f.phone.value,otp:f.otp.value})});load()}catch(x){msg.textContent=x.message}};document.querySelectorAll('[data-p]').forEach(b=>b.onclick=()=>f.phone.value=b.dataset.p)}
async function load(){try{state.data=await api('/api/dashboard');render()}catch{login()}}
function shell(body){let u=state.data.user;app.innerHTML=`<header class="top"><div class="brand"><img src="${LOGO}"><div><h2>AKSHARA BIET</h2><p>${u.name} - ${u.role}</p></div></div><button class="logout" id="out">Sign out</button></header><div class="content"><div class="alert"><b>Security warning:</b> OTP, bank details, income certificate and application number are confidential. <span class="pill">Deadline: 31 Aug 2026</span></div><nav class="tabs">${['dashboard','students','scholarships','applications','faculty'].map(v=>`<button class="${state.view==v?'active':''}" data-v="${v}">${v[0].toUpperCase()+v.slice(1)}</button>`).join('')}</nav>${body}</div>`;out.onclick=async()=>{await api('/api/logout',{method:'POST'});login()};document.querySelectorAll('[data-v]').forEach(b=>b.onclick=()=>{state.view=b.dataset.v;render()})}
function render(){let d=state.data;if(state.view=='dashboard')return shell(`<div class="grid"><div class="panel stat"><p>Students</p><b>${d.stats.students}</b></div><div class="panel stat"><p>Scholarships</p><b>${d.stats.scholarships}</b></div><div class="panel stat"><p>Applications</p><b>${d.stats.applications}</b></div><div class="panel stat"><p>Approved Value</p><b>${money(d.stats.value)}</b></div></div><h2>Priority Applications</h2><div class="list">${d.apps.map(card).join('')}</div>`);if(state.view=='students')return shell(`<div class="panel">${d.students.map(s=>`<div class="row"><b>${s.name}</b><span>${s.roll}</span><span>${s.course}</span><span>CGPA ${s.cgpa}</span></div>`).join('')}</div>`);if(state.view=='scholarships')return shell(`<div class="list">${d.scholarships.map(s=>`<div class="item"><h3>${s.title}</h3><p>${s.provider}</p><span class="pill">${money(s.amount)}</span><p>${s.eligibility}</p><b>Deadline: ${s.deadline}</b></div>`).join('')}</div>`);if(state.view=='faculty')return shell(`<div class="grid">${d.faculty.map(f=>`<div class="panel"><h3>${f.name}</h3><p>${f.dept}</p><span class="pill">${f.role}</span></div>`).join('')}</div>`);shell(`<div class="list">${d.apps.map(card).join('')}</div>`)}
function card(a){return `<div class="item"><h3>${a.app_no}</h3><p>${a.student} - ${a.title}</p><span class="pill">${a.status}</span><p>${a.purpose}</p><b>Score ${a.score}</b></div>`}load();
</script></body></html>'''.replace('__LOGO__',LOGO)

class H(BaseHTTPRequestHandler):
    def js(self,p,status=200):
        b=json.dumps(p).encode(); self.send_response(status); self.send_header('Content-Type','application/json'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def data(self): return json.loads(self.rfile.read(int(self.headers.get('Content-Length',0))) or b'{}')
    def user(self):
        sid=cookies.SimpleCookie(self.headers.get('Cookie','')).get('sid')
        uid=SESSIONS.get(sid.value) if sid else None
        if not uid: return None
        with con() as c:
            r=c.execute('select * from users where id=?',(uid,)).fetchone(); return dict(r) if r else None
    def do_GET(self):
        if self.path.startswith('/api/dashboard'):
            u=self.user()
            if not u: return self.js({'error':'Login required'},401)
            with con() as c:
                students=rows(c.execute('select u.name,p.* from users u join profiles p on p.user_id=u.id order by u.name'))
                faculty=rows(c.execute("select name,role,dept from users where role!='student'"))
                scholarships=rows(c.execute('select * from scholarships order by deadline'))
                apps=rows(c.execute('select a.*,u.name student,s.title,s.amount from applications a join users u on u.id=a.student_id join scholarships s on s.id=a.scholarship_id order by a.score desc'))
            for a in apps: a['app_no']=appno(a['id'])
            return self.js({'user':u,'students':students,'faculty':faculty,'scholarships':scholarships,'apps':apps,'stats':{'students':len(students),'scholarships':len(scholarships),'applications':len(apps),'value':sum(a['amount'] for a in apps if a['status'] in ('approved','paid'))}})
        b=HTML.encode(); self.send_response(200); self.send_header('Content-Type','text/html; charset=utf-8'); self.send_header('Content-Length',str(len(b))); self.end_headers(); self.wfile.write(b)
    def do_POST(self):
        if self.path=='/api/request-otp':
            d=self.data(); u=ensure_user(d.get('phone'))
            if not u: return self.js({'error':'Enter a valid 10 digit mobile number.'},400)
            return self.js(send_otp(d.get('phone')))
        if self.path=='/api/verify-otp':
            d=self.data(); phone=ph(d.get('phone'))
            if not ok_otp(phone,d.get('otp')): return self.js({'error':'Invalid or expired OTP.'},401)
            u=ensure_user(phone); sid=secrets.token_urlsafe(24); SESSIONS[sid]=u['id']; self.send_response(200); self.send_header('Content-Type','application/json'); self.send_header('Set-Cookie',f'sid={sid}; Path=/; HttpOnly; SameSite=Lax'); self.end_headers(); self.wfile.write(b'{"ok":true}'); return
        if self.path=='/api/logout': return self.js({'ok':True})
        self.js({'error':'Not found'},404)

if __name__=='__main__':
    seed(); port=int(os.getenv('PORT','8000')); print(f'{APP} running on port {port}'); ThreadingHTTPServer(('0.0.0.0',port),H).serve_forever()
