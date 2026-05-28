from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from http import cookies
import base64
import json
import os
import secrets
import sqlite3
import time
from urllib import parse, request


DB = "akshara_portal.db"
APP = "AKSHARA BIET Scholarship Management System"
SESSIONS = {}
DEMO_OTPS = {}

LOGO = """data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 900 520'%3E%3Cdefs%3E%3ClinearGradient id='g' x1='0' y1='0' x2='1' y2='1'%3E%3Cstop stop-color='%23005bd6'/%3E%3Cstop offset='.55' stop-color='%230057b8'/%3E%3Cstop offset='1' stop-color='%23ff5b1a'/%3E%3C/linearGradient%3E%3Cfilter id='s' x='-20%25' y='-20%25' width='140%25' height='140%25'%3E%3CfeDropShadow dx='0' dy='18' stdDeviation='18' flood-color='%2300214d' flood-opacity='.24'/%3E%3C/filter%3E%3C/defs%3E%3Crect width='900' height='520' rx='38' fill='%23f5f9ff'/%3E%3Cg filter='url(%23s)'%3E%3Cpath d='M260 210c70-42 130-42 190 0 60-42 120-42 190 0v105c-72-39-136-39-190 4-54-43-118-43-190-4z' fill='%230066d9'/%3E%3Cpath d='M450 80l34 72 80 11-58 56 14 80-70-38-70 38 14-80-58-56 80-11z' fill='%23ff9b13'/%3E%3Cpath d='M450 150l112 48-112 48-112-48z' fill='%23ff7a00'/%3E%3Cpath d='M386 214v51l64 34 64-34v-51l-64 30z' fill='%23003278'/%3E%3C/g%3E%3Ctext x='450' y='405' text-anchor='middle' font-size='92' font-family='Arial Black,Arial,sans-serif' fill='url(%23g)'%3EAKSHARA%3C/text%3E%3Ctext x='450' y='455' text-anchor='middle' font-size='31' font-family='Arial,sans-serif' fill='%2318273d'%3EBIET Scholarship Management System%3C/text%3E%3C/svg%3E"""

STUDENTS = [
    ("Adithi H", "9000044444", "CSE", "AKS-CS-001", 9.4, 180000),
    ("Sahana K", "9000055555", "ISE", "AKS-IS-002", 9.1, 160000),
    ("Namana", "9000066666", "ECE", "AKS-EC-003", 8.8, 220000),
    ("Sampreethi", "9000077777", "AI&ML", "AKS-AI-004", 9.0, 140000),
    ("Akash R", "9000088888", "Mechanical", "AKS-ME-005", 8.3, 250000),
    ("Gourav H", "9000099999", "Civil", "AKS-CV-006", 8.6, 130000),
    ("Minnu K", "9000100000", "ECE", "AKS-EC-007", 8.9, 190000),
]

PROFESSORS = [
    ("Dr Pradeep N", "9000011111", "admin", "Chairperson"),
    ("Usha C", "9000022222", "reviewer", "Scholarship Reviewer"),
    ("Gowri B", "9000033333", "reviewer", "Academic Reviewer"),
]


def clean_phone(value):
    return "".join(ch for ch in str(value or "") if ch.isdigit())[-10:]


def db():
    connection = sqlite3.connect(DB)
    connection.row_factory = sqlite3.Row
    return connection


def rows(cursor):
    return [dict(row) for row in cursor.fetchall()]


def app_number(app_id):
    return f"AKS-BIET-2026-{int(app_id):05d}"


def seed():
    with db() as c:
        c.executescript(
            """
            create table if not exists users(id integer primary key, name text, phone text unique, role text, dept text);
            create table if not exists profiles(user_id integer unique, roll text, course text, cgpa real, income integer);
            create table if not exists scholarships(id integer primary key, title text, provider text, amount integer, min_cgpa real, max_income integer, seats integer, deadline text, status text, eligibility text);
            create table if not exists applications(id integer primary key, student_id integer, scholarship_id integer, purpose text, status text, score integer, updated text default current_timestamp, unique(student_id, scholarship_id));
            """
        )
        if c.execute("select count(*) n from users").fetchone()["n"]:
            return
        uid = 1
        for name, phone, role, dept in PROFESSORS:
            c.execute("insert into users values(?,?,?,?,?)", (uid, name, phone, role, dept))
            uid += 1
        for name, phone, course, roll, cgpa, income in STUDENTS:
            c.execute("insert into users values(?,?,?,?,?)", (uid, name, phone, "student", course))
            c.execute("insert into profiles values(?,?,?,?,?)", (uid, roll, course, cgpa, income))
            uid += 1
        scholarships = [
            ("AKSHARA Prime Merit Scholarship", "BIET Scholarship Council", 75000, 8.5, 250000, 35, "31 Aug 2026", "open", "CGPA 8.5+, income below Rs 2.5L, no active backlog."),
            ("AKSHARA Women in Engineering Grant", "BIET Alumni Endowment", 60000, 8.0, 300000, 25, "15 Sep 2026", "open", "Women students with strong academics and leadership record."),
            ("AKSHARA Need Based Assistance", "Student Welfare Office", 50000, 7.5, 180000, 40, "20 Sep 2026", "open", "Verified income certificate and academic continuation proof required."),
        ]
        c.executemany("insert into scholarships(title,provider,amount,min_cgpa,max_income,seats,deadline,status,eligibility) values(?,?,?,?,?,?,?,?,?)", scholarships)
        for sid in range(4, 11):
            scholarship_id = 1 + ((sid - 4) % 3)
            c.execute("insert into applications(student_id,scholarship_id,purpose,status,score) values(?,?,?,?,?)", (sid, scholarship_id, "Requesting academic financial assistance through AKSHARA portal.", "submitted" if sid % 3 else "under_review", 78 + sid))


def twilio_ready():
    return all(os.getenv(k) for k in ("TWILIO_ACCOUNT_SID", "TWILIO_AUTH_TOKEN", "TWILIO_VERIFY_SERVICE_SID"))


def twilio_post(path, data):
    sid = os.getenv("TWILIO_ACCOUNT_SID")
    token = os.getenv("TWILIO_AUTH_TOKEN")
    service = os.getenv("TWILIO_VERIFY_SERVICE_SID")
    body = parse.urlencode(data).encode()
    url = f"https://verify.twilio.com/v2/Services/{service}/{path}"
    req = request.Request(url, data=body, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    auth = base64.b64encode(f"{sid}:{token}".encode()).decode()
    req.add_header("Authorization", f"Basic {auth}")
    with request.urlopen(req, timeout=15) as response:
        return json.loads(response.read().decode())


def send_otp(phone):
    full = "+91" + clean_phone(phone)
    if twilio_ready():
        twilio_post("Verifications", {"To": full, "Channel": "sms"})
        return {"mode": "sms", "message": "OTP sent to your registered mobile number."}
    code = f"{secrets.randbelow(900000) + 100000}"
    DEMO_OTPS[clean_phone(phone)] = (code, time.time() + 300)
    return {"mode": "demo", "message": "Demo OTP generated because Twilio environment variables are not configured.", "dev_otp": code}


def check_otp(phone, code):
    full = "+91" + clean_phone(phone)
    if twilio_ready():
        result = twilio_post("VerificationCheck", {"To": full, "Code": code})
        return result.get("status") == "approved"
    saved = DEMO_OTPS.get(clean_phone(phone))
    return bool(saved and saved[0] == str(code).strip() and saved[1] > time.time())


HTML = """<!doctype html><html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><title>AKSHARA BIET Scholarship Management System</title><style>
:root{--ink:#102033;--muted:#657589;--line:#dbe5ef;--soft:#f4f8fc;--blue:#005bd6;--deep:#08203f;--orange:#ff7a00;--green:#11845b;--red:#c24141;--shadow:0 22px 60px rgba(16,32,51,.13)}*{box-sizing:border-box}body{margin:0;font-family:Inter,Segoe UI,Arial,sans-serif;color:var(--ink);background:#eef4fa}button,input,textarea{font:inherit}button{cursor:pointer}.login{min-height:100vh;display:grid;grid-template-columns:1.12fr .88fr;background:linear-gradient(120deg,rgba(8,32,63,.94),rgba(0,91,214,.72)),url('https://images.unsplash.com/photo-1523240795612-9a054b0db644?auto=format&fit=crop&w=1800&q=80');background-size:cover;background-position:center}.hero{padding:56px 70px;align-self:center;color:white}.hero img{width:min(390px,82vw);background:rgba(255,255,255,.92);border-radius:28px;padding:18px;box-shadow:var(--shadow)}.eyebrow{text-transform:uppercase;letter-spacing:.14em;font-size:12px;font-weight:900;color:#a8d4ff}.hero h1{font-size:clamp(42px,6vw,78px);line-height:1;margin:28px 0 18px;max-width:840px}.hero p{font-size:19px;line-height:1.7;max-width:760px;color:rgba(255,255,255,.86)}.metrics{display:flex;gap:14px;flex-wrap:wrap;margin-top:28px}.metrics span,.badge{border:1px solid rgba(255,255,255,.28);background:rgba(255,255,255,.12);border-radius:999px;padding:12px 15px;font-weight:800}.card{align-self:center;margin:36px 56px;background:white;border-radius:8px;padding:34px;box-shadow:var(--shadow);border:1px solid var(--line)}.card-head{display:flex;gap:16px;align-items:center;margin-bottom:24px}.card-head img,.brand img{width:76px;border-radius:14px;border:1px solid var(--line)}label{display:block;font-weight:850;margin:16px 0 8px}input,textarea{width:100%;border:1px solid #cdd8e4;border-radius:8px;padding:13px 14px;background:white}button.primary{width:100%;border:0;border-radius:8px;background:linear-gradient(135deg,var(--blue),#003f95);color:#fff;font-weight:900;padding:14px;margin-top:14px}.quick{display:grid;grid-template-columns:repeat(3,1fr);gap:8px;margin:18px 0}.quick button{border:1px solid var(--line);background:#f8fbff;border-radius:8px;padding:10px;font-weight:850}.warn{border-left:4px solid var(--orange);background:#fff6ed;padding:13px;border-radius:6px;color:#7a3b00}.error{color:var(--red);font-weight:850}.hidden{display:none}.shell{min-height:100vh}.top{background:#081d38;color:#fff;padding:18px 28px;display:flex;align-items:center;justify-content:space-between;gap:18px}.brand{display:flex;align-items:center;gap:14px}.brand img{background:white}.brand h2{margin:0;font-size:21px}.brand p{margin:3px 0 0;color:#a9bfd7}.logout{border:1px solid rgba(255,255,255,.26);background:transparent;color:white;border-radius:8px;padding:10px 14px}.content{padding:24px;max-width:1440px;margin:auto}.alert{display:flex;justify-content:space-between;gap:12px;align-items:center;background:#fff7ed;border:1px solid #fed7aa;padding:14px 16px;border-radius:8px;margin-bottom:18px}.tabs{display:flex;gap:8px;flex-wrap:wrap;margin:0 0 18px}.tabs button{border:1px solid var(--line);background:white;border-radius:8px;padding:11px 14px;font-weight:900}.tabs button.active{background:var(--deep);color:white}.grid{display:grid;grid-template-columns:repeat(4,1fr);gap:14px}.panel{background:white;border:1px solid var(--line);border-radius:8px;padding:18px;box-shadow:0 10px 28px rgba(16,32,51,.07)}.stat b{font-size:30px}.list{display:grid;gap:12px}.item{background:white;border:1px solid var(--line);border-radius:8px;padding:16px;display:grid;gap:10px}.item-head{display:flex;justify-content:space-between;gap:12px}.pill{border-radius:999px;background:#eaf3ff;color:#084894;padding:6px 10px;font-weight:900;font-size:12px}.ok{background:#e9f8f1;color:var(--green)}.danger{background:#fff0f0;color:var(--red)}.two{display:grid;grid-template-columns:1fr 1fr;gap:18px}.student-row{display:grid;grid-template-columns:1.3fr .8fr .8fr .8fr;gap:12px;align-items:center;border-top:1px solid var(--line);padding:12px 0}.student-row:first-child{border-top:0}@media(max-width:920px){.login,.two,.grid{grid-template-columns:1fr}.hero,.card{margin:0;padding:26px}.quick{grid-template-columns:1fr}.top,.alert,.item-head{align-items:flex-start;flex-direction:column}.student-row{grid-template-columns:1fr}}
</style></head><body><main id="app"></main><script>
const LOGO = "__LOGO__"; let state={user:null,view:"dashboard",data:null}; const app=document.querySelector("#app");
const money=n=>new Intl.NumberFormat("en-IN",{style:"currency",currency:"INR",maximumFractionDigits:0}).format(n||0);
async function api(path,opts={}){const r=await fetch(path,{headers:{"Content-Type":"application/json"},credentials:"same-origin",...opts}); const d=await r.json().catch(()=>({})); if(!r.ok) throw new Error(d.error||"Request failed"); return d}
function login(){app.innerHTML=`<section class="login"><div class="hero"><img src="${LOGO}" alt="AKSHARA BIET logo"><p class="eyebrow">BIET Digital Scholarship Cell</p><h1>AKSHARA BIET Scholarship Management System</h1><p>A full DBMS portal for merit awards, need based aid, OTP secured access, academic review, warning alerts, deadlines, unique application numbers and fund disbursement.</p><div class="metrics"><span>AKS-2026 Unique series</span><span>OTP mobile login</span><span>31 Aug final deadline</span></div></div><form class="card" id="form"><div class="card-head"><img src="${LOGO}" alt=""><div><p class="eyebrow">Secure OTP access</p><h2>Sign in with mobile</h2></div></div><label>Registered mobile number</label><input name="phone" value="9000055555" maxlength="14"><button class="primary" id="send">Send OTP</button><label class="hidden otp">Enter OTP</label><input class="hidden otp" name="otp" maxlength="6" inputmode="numeric"><button class="primary hidden otp" type="button" id="verify">Verify and Login</button><div class="quick"><button type="button" data-phone="9000044444">Adithi H</button><button type="button" data-phone="9000055555">Sahana K</button><button type="button" data-phone="9000011111">Dr Pradeep N</button></div><div class="warn"><b>Warning:</b> Never share OTP, application number, income certificate, bank details or login access.</div><p id="msg" class="error"></p></form></section>`;
document.querySelector("#form").onsubmit=async e=>{e.preventDefault(); const phone=e.target.phone.value; try{const d=await api("/api/request-otp",{method:"POST",body:JSON.stringify({phone})}); document.querySelectorAll(".otp").forEach(x=>x.classList.remove("hidden")); msg.textContent=d.dev_otp?`Demo OTP: ${d.dev_otp}`:d.message}catch(err){msg.textContent=err.message}};
document.querySelector("#verify").onclick=async()=>{try{await api("/api/verify-otp",{method:"POST",body:JSON.stringify({phone:form.phone.value,otp:form.otp.value})}); await load()}catch(err){msg.textContent=err.message}};
document.querySelectorAll("[data-phone]").forEach(b=>b.onclick=()=>form.phone.value=b.dataset.phone)}
async function load(){try{state.data=await api("/api/dashboard"); state.user=state.data.user; render()}catch{login()}}
function shell(body){app.innerHTML=`<section class="shell"><header class="top"><div class="brand"><img src="${LOGO}" alt=""><div><h2>AKSHARA BIET</h2><p>${state.user.name} · ${state.user.role}</p></div></div><button class="logout" id="out">Sign out</button></header><div class="content"><div class="alert"><div><b>Security warning:</b> OTP, bank details, income certificate and application number are confidential.</div><span class="pill danger">Deadline: 31 Aug 2026</span></div><nav class="tabs">${["dashboard","students","scholarships","applications","faculty"].map(v=>`<button class="${state.view==v?"active":""}" data-view="${v}">${v[0].toUpperCase()+v.slice(1)}</button>`).join("")}</nav>${body}</div></section>`; out.onclick=async()=>{await api("/api/logout",{method:"POST"});login()}; document.querySelectorAll("[data-view]").forEach(b=>b.onclick=()=>{state.view=b.dataset.view;render()})}
function render(){const d=state.data; if(state.view=="dashboard")return shell(`<div class="grid"><div class="panel stat"><p>Total Students</p><b>${d.stats.students}</b></div><div class="panel stat"><p>Scholarships</p><b>${d.stats.scholarships}</b></div><div class="panel stat"><p>Applications</p><b>${d.stats.applications}</b></div><div class="panel stat"><p>Approved Value</p><b>${money(d.stats.value)}</b></div></div><h2>Priority Applications</h2><div class="list">${d.apps.map(appCard).join("")}</div>`); if(state.view=="students")return shell(`<div class="panel">${d.students.map(s=>`<div class="student-row"><b>${s.name}</b><span>${s.roll}</span><span>${s.course}</span><span>CGPA ${s.cgpa}</span></div>`).join("")}</div>`); if(state.view=="scholarships")return shell(`<div class="list">${d.scholarships.map(s=>`<div class="item"><div class="item-head"><div><h3>${s.title}</h3><p>${s.provider}</p></div><span class="pill">${money(s.amount)}</span></div><p>${s.eligibility}</p><b>Deadline: ${s.deadline}</b></div>`).join("")}</div>`); if(state.view=="faculty")return shell(`<div class="grid">${d.faculty.map(f=>`<div class="panel"><h3>${f.name}</h3><p>${f.dept}</p><span class="pill">${f.role}</span></div>`).join("")}</div>`); shell(`<div class="list">${d.apps.map(appCard).join("")}</div>`)}
function appCard(a){return `<div class="item"><div class="item-head"><div><h3>${a.app_no}</h3><p>${a.student} · ${a.title}</p></div><span class="pill ${a.status=="approved"?"ok":""}">${a.status}</span></div><p>${a.purpose}</p><b>Score ${a.score}</b></div>`}
load();
</script></body></html>""".replace("__LOGO__", LOGO)


class Handler(BaseHTTPRequestHandler):
    def send_json(self, payload, status=200):
        body = json.dumps(payload).encode()
        self.send_response(status)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def body_json(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

    def current_user(self):
        raw = self.headers.get("Cookie", "")
        jar = cookies.SimpleCookie(raw)
        sid = jar.get("sid")
        uid = SESSIONS.get(sid.value) if sid else None
        if not uid:
            return None
        with db() as c:
            row = c.execute("select * from users where id=?", (uid,)).fetchone()
            return dict(row) if row else None

    def do_GET(self):
        if self.path.startswith("/api/dashboard"):
            user = self.current_user()
            if not user:
                return self.send_json({"error": "Login required"}, 401)
            with db() as c:
                students = rows(c.execute("select u.name,p.* from users u join profiles p on p.user_id=u.id order by u.name"))
                faculty = rows(c.execute("select name,role,dept from users where role!='student'"))
                scholarships = rows(c.execute("select * from scholarships order by deadline"))
                apps = rows(c.execute("select a.*,u.name student,s.title,s.amount from applications a join users u on u.id=a.student_id join scholarships s on s.id=a.scholarship_id order by a.score desc"))
                for a in apps:
                    a["app_no"] = app_number(a["id"])
                stats = {"students": len(students), "scholarships": len(scholarships), "applications": len(apps), "value": sum(a["amount"] for a in apps if a["status"] in ("approved", "paid"))}
                return self.send_json({"user": user, "students": students, "faculty": faculty, "scholarships": scholarships, "apps": apps, "stats": stats})
        self.send_response(200)
        self.send_header("Content-Type", "text/html; charset=utf-8")
        self.end_headers()
        self.wfile.write(HTML.encode())

    def do_POST(self):
        if self.path == "/api/request-otp":
            data = self.body_json()
            ph = clean_phone(data.get("phone"))
            with db() as c:
                user = c.execute("select id from users where phone=?", (ph,)).fetchone()
            if not user:
                return self.send_json({"error": "Mobile number is not registered in AKSHARA BIET portal."}, 404)
            return self.send_json(send_otp(ph))
        if self.path == "/api/verify-otp":
            data = self.body_json()
            ph, code = clean_phone(data.get("phone")), str(data.get("otp", "")).strip()
            if not check_otp(ph, code):
                return self.send_json({"error": "Invalid or expired OTP."}, 401)
            with db() as c:
                user = c.execute("select id from users where phone=?", (ph,)).fetchone()
            sid = secrets.token_urlsafe(24)
            SESSIONS[sid] = user["id"]
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Set-Cookie", f"sid={sid}; Path=/; HttpOnly; SameSite=Lax")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return
        if self.path == "/api/logout":
            self.send_json({"ok": True})
            return
        self.send_json({"error": "Not found"}, 404)


if __name__ == "__main__":
    seed()
    port = int(os.getenv("PORT", "8000"))
    print(f"{APP} running on port {port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
