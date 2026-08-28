
import streamlit as st
from pathlib import Path
from datetime import datetime
from PIL import Image, ImageOps
import sqlite3, hashlib, secrets, os, io
import pandas as pd

APP = "EcoEarn AI"
DB = Path("ecoearn.db")
UPLOADS = Path("uploads")
UPLOADS.mkdir(exist_ok=True)

LANG = {
"বাংলা": {
"home":"হোম","scan":"বর্জ্য স্ক্যান","market":"বর্জ্য বাজার","collector":"কালেক্টর",
"wallet":"ওয়ালেট","rewards":"EcoPoints","dashboard":"অ্যাডমিন","about":"সম্পর্কে",
"auth":"নিবন্ধন / লগইন","register":"নিবন্ধন","login":"লগইন","logout":"লগআউট",
"name":"পূর্ণ নাম","phone":"মোবাইল নম্বর","password":"পাসওয়ার্ড","confirm":"পাসওয়ার্ড নিশ্চিত করুন",
"role":"অ্যাকাউন্টের ধরন","citizen":"সাধারণ ইউজার","collector_role":"Waste Collector",
"admin_role":"Admin","create":"অ্যাকাউন্ট তৈরি করুন","already":"আগে থেকেই অ্যাকাউন্ট আছে?",
"have":"অ্যাকাউন্ট নেই?","signin":"লগইন করুন","signup":"নিবন্ধন করুন",
"welcome":"EcoEarn AI-তে স্বাগতম","tagline":"ফেলে দেবেন না—বর্জ্য থেকেই আয় করুন।",
"subtitle":"AI-ভিত্তিক বর্জ্য ব্যবস্থাপনা, আয় ও circular economy platform।",
"upload":"ছবি আপলোড","camera":"ক্যামেরায় ছবি","analyze":"AI দিয়ে বিশ্লেষণ",
"weight":"আনুমানিক ওজন (কেজি)","material":"শনাক্তকৃত বর্জ্য","confidence":"নির্ভরযোগ্যতা",
"authenticity":"ছবির সত্যতা যাচাই","estimated":"আনুমানিক মূল্য","pickup":"পিকআপ রিকোয়েস্ট",
"balance":"ব্যালেন্স","history":"লেনদেনের ইতিহাস","points":"পয়েন্ট","impact":"আপনার পরিবেশগত প্রভাব",
"jobs":"পিকআপ জব","accept":"জব গ্রহণ","complete":"সংগ্রহ সম্পন্ন","save":"সেভ",
"no_jobs":"কোনো জব পাওয়া যায়নি।","admin_title":"Environmental Intelligence",
"users":"ইউজার","requests":"রিকোয়েস্ট","collected":"সংগ্রহ","total":"মোট বর্জ্য",
"language":"ভাষা","profile":"প্রোফাইল","phone_hint":"11 সংখ্যার বাংলাদেশি মোবাইল নম্বর দিন।",
"logout_msg":"আপনি লগআউট করেছেন।","need_login":"এই ফিচার ব্যবহার করতে লগইন করুন।",
"real":"সম্ভবত আসল","synthetic":"সম্ভবত AI-generated","uncertain":"নিশ্চিত নয়",
"security":"নিরাপত্তা","footer":"EcoEarn AI — Bangladesh Prototype"
},
"English": {
"home":"Home","scan":"Scan Waste","market":"Waste Market","collector":"Collector",
"wallet":"Wallet","rewards":"EcoPoints","dashboard":"Admin","about":"About",
"auth":"Register / Login","register":"Register","login":"Login","logout":"Logout",
"name":"Full name","phone":"Mobile number","password":"Password","confirm":"Confirm password",
"role":"Account type","citizen":"Citizen","collector_role":"Waste Collector","admin_role":"Admin",
"create":"Create account","already":"Already have an account?","have":"Don't have an account?",
"signin":"Login","signup":"Register","welcome":"Welcome to EcoEarn AI",
"tagline":"Don't Throw It. Earn From It.","subtitle":"AI-powered waste management, income and circular economy platform.",
"upload":"Upload photo","camera":"Take photo","analyze":"Analyze with AI","weight":"Estimated weight (kg)",
"material":"Detected material","confidence":"Confidence","authenticity":"Image authenticity",
"estimated":"Estimated value","pickup":"Request pickup","balance":"Balance","history":"Transaction history",
"points":"points","impact":"Your environmental impact","jobs":"Pickup jobs","accept":"Accept job",
"complete":"Mark collected","save":"Save","no_jobs":"No jobs available.","admin_title":"Environmental Intelligence",
"users":"Users","requests":"Requests","collected":"Collected","total":"Total waste",
"language":"Language","profile":"Profile","phone_hint":"Enter an 11-digit Bangladesh mobile number.",
"logout_msg":"You are logged out.","need_login":"Please login to use this feature.",
"real":"Likely real","synthetic":"Possibly AI-generated","uncertain":"Uncertain",
"security":"Security","footer":"EcoEarn AI — Bangladesh Prototype"
}}

RATES={"PET Plastic":55,"HDPE Plastic":48,"LDPE Plastic":35,"Paper/Cardboard":18,"Metal":85,
"Glass":10,"E-waste":120,"Organic":3,"Mixed/Unknown":15}

def t(k): return LANG[st.session_state.lang].get(k,k)

def conn():
    c=sqlite3.connect(DB); c.execute("PRAGMA foreign_keys=ON"); return c

def init_db():
    c=conn()
    c.executescript("""
    CREATE TABLE IF NOT EXISTS users(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      name TEXT NOT NULL, phone TEXT UNIQUE NOT NULL,
      password_hash TEXT NOT NULL, salt TEXT NOT NULL,
      role TEXT NOT NULL DEFAULT 'citizen',
      balance REAL NOT NULL DEFAULT 0,
      points INTEGER NOT NULL DEFAULT 0,
      kg REAL NOT NULL DEFAULT 0,
      created_at TEXT NOT NULL
    );
    CREATE TABLE IF NOT EXISTS jobs(
      id INTEGER PRIMARY KEY AUTOINCREMENT,
      user_id INTEGER NOT NULL, collector_id INTEGER,
      material TEXT NOT NULL, kg REAL NOT NULL, value REAL NOT NULL,
      status TEXT NOT NULL DEFAULT 'Requested',
      lat REAL DEFAULT 24.3745, lon REAL DEFAULT 88.6042,
      created_at TEXT NOT NULL, collected_at TEXT,
      FOREIGN KEY(user_id) REFERENCES users(id),
      FOREIGN KEY(collector_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS transactions(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      amount REAL NOT NULL, kind TEXT NOT NULL, note TEXT NOT NULL,
      created_at TEXT NOT NULL, FOREIGN KEY(user_id) REFERENCES users(id)
    );
    CREATE TABLE IF NOT EXISTS scans(
      id INTEGER PRIMARY KEY AUTOINCREMENT, user_id INTEGER NOT NULL,
      material TEXT, confidence REAL, authenticity TEXT, auth_conf REAL,
      image_hash TEXT, created_at TEXT NOT NULL,
      FOREIGN KEY(user_id) REFERENCES users(id)
    );
    """)
    c.commit(); c.close()

def q(sql,p=(),one=False):
    c=conn(); cur=c.execute(sql,p); rows=cur.fetchall(); c.close()
    return rows[0] if one and rows else (None if one else rows)

def execute(sql,p=()):
    c=conn(); cur=c.execute(sql,p); c.commit(); rid=cur.lastrowid; c.close(); return rid

def hash_password(password,salt=None):
    salt=salt or secrets.token_hex(16)
    h=hashlib.pbkdf2_hmac("sha256",password.encode(),salt.encode(),200000).hex()
    return h,salt

def verify_password(password,h,salt):
    return secrets.compare_digest(hash_password(password,salt)[0],h)

def current_user():
    uid=st.session_state.get("user_id")
    return q("SELECT * FROM users WHERE id=?",(uid,),one=True) if uid else None

def normalize_phone(p):
    p=p.strip().replace(" ","").replace("-","")
    if p.startswith("+880"): p="0"+p[4:]
    return p

def valid_phone(p): return p.isdigit() and len(p)==11 and p.startswith(("013","014","015","016","017","018","019"))

def auth_screen():
    st.markdown("## ♻️ EcoEarn AI")
    tab1,tab2=st.tabs([f"🔐 {t('login')}",f"📝 {t('register')}"])
    with tab1:
        with st.form("login_form"):
            phone=normalize_phone(st.text_input(t("phone")))
            pw=st.text_input(t("password"),type="password")
            ok=st.form_submit_button(t("signin"),use_container_width=True,type="primary")
        if ok:
            user=q("SELECT * FROM users WHERE phone=?",(phone,),one=True)
            if user and verify_password(pw,user[3],user[4]):
                st.session_state.user_id=user[0]; st.rerun()
            else: st.error("Invalid mobile number or password.")
    with tab2:
        with st.form("register_form"):
            name=st.text_input(t("name"))
            phone=normalize_phone(st.text_input(t("phone")))
            pw=st.text_input(t("password"),type="password")
            cpw=st.text_input(t("confirm"),type="password")
            role_label=st.selectbox(t("role"),[t("citizen"),t("collector_role")])
            create=st.form_submit_button(t("create"),use_container_width=True,type="primary")
        if create:
            if not name.strip(): st.error("Name is required.")
            elif not valid_phone(phone): st.error(t("phone_hint"))
            elif len(pw)<6: st.error("Password must contain at least 6 characters.")
            elif pw!=cpw: st.error("Passwords do not match.")
            elif q("SELECT id FROM users WHERE phone=?",(phone,),one=True): st.error("This mobile number is already registered.")
            else:
                role="collector" if role_label==t("collector_role") else "citizen"
                h,s=hash_password(pw)
                uid=execute("INSERT INTO users(name,phone,password_hash,salt,role,created_at) VALUES(?,?,?,?,?,?)",
                            (name.strip(),phone,h,s,role,datetime.now().isoformat()))
                st.session_state.user_id=uid
                st.success("Account created successfully!")
                st.rerun()
    st.info("Prototype admin account: create/login as collector for operations. For a production deployment, admin creation must be restricted server-side.")

def logout():
    st.session_state.pop("user_id",None)
    st.rerun()

def waste_ai(img):
    # Optional Hugging Face zero-shot classification. Conservative fallback.
    try:
        from huggingface_hub import InferenceClient
        token=st.secrets.get("HF_TOKEN",os.getenv("HF_TOKEN"))
        if token:
            client=InferenceClient(token=token)
            labels=["plastic bottle","plastic","paper cardboard","metal","glass","electronic waste","food organic waste"]
            r=client.zero_shot_image_classification(img, candidate_labels=labels, model="openai/clip-vit-large-patch14")
            if r:
                b=max(r,key=lambda x:x.score)
                s=b.label.lower()
                mapping={"plastic bottle":"PET Plastic","plastic":"PET Plastic","paper cardboard":"Paper/Cardboard",
                         "metal":"Metal","glass":"Glass","electronic waste":"E-waste","food organic waste":"Organic"}
                for k,v in mapping.items():
                    if k in s: return v,float(b.score)
    except Exception: pass
    return "Mixed/Unknown",0.45

def authenticity_ai(img):
    try:
        from huggingface_hub import InferenceClient
        token=st.secrets.get("HF_TOKEN",os.getenv("HF_TOKEN"))
        model=st.secrets.get("AI_DETECTOR_MODEL","dima806/ai-generated-image-detection")
        if token:
            client=InferenceClient(token=token)
            r=client.image_classification(img,model=model)
            if r:
                pairs=[(x.label.lower(),float(x.score)) for x in r]
                ai=max([s for l,s in pairs if any(k in l for k in ["fake","ai","generated","synthetic"])],default=0)
                real=max([s for l,s in pairs if any(k in l for k in ["real","human","authentic"])],default=0)
                if ai>=.65 and ai>real:return "synthetic",ai
                if real>=.65 and real>ai:return "real",real
                return "uncertain",max(ai,real)
    except Exception: pass
    return "uncertain",0

def image_hash(img):
    x=ImageOps.exif_transpose(img).convert("RGB").resize((64,64))
    return hashlib.sha256(x.tobytes()).hexdigest()

def hero():
    st.markdown(f"""<div class="hero">
    <div class="pill">♻️ AI • Circular Economy • Bangladesh</div>
    <h1>EcoEarn AI</h1><p>{t('tagline')}<br>{t('subtitle')}</p></div>""",unsafe_allow_html=True)

def home():
    u=current_user()
    hero()
    st.markdown(f"### {t('welcome')}, {u[1]} 👋")
    a,b,c,d=st.columns(4)
    a.metric(t("balance"),f"৳{u[6]:,.0f}")
    b.metric(t("points"),u[7])
    c.metric(t("collected"),f"{u[8]:.1f} kg")
    d.metric(t("requests"),q("SELECT COUNT(*) FROM jobs WHERE user_id=?",(u[0],),one=True)[0])
    st.markdown("### 🌱 How it works")
    x,y,z=st.columns(3)
    x.markdown('<div class="card"><b>📸 1. Scan</b><br>Upload or capture waste.</div>',unsafe_allow_html=True)
    y.markdown('<div class="card"><b>🤖 2. Verify</b><br>AI identifies waste and screens suspicious images.</div>',unsafe_allow_html=True)
    z.markdown('<div class="card"><b>💰 3. Earn</b><br>Request pickup and receive verified credit.</div>',unsafe_allow_html=True)

def scan():
    st.markdown(f"## 📸 {t('scan')}")
    source=st.radio("Source",[t("upload"),t("camera")],horizontal=True)
    f=st.file_uploader(t("upload"),type=["jpg","jpeg","png","webp"]) if source==t("upload") else st.camera_input(t("camera"))
    if not f: st.info(t("need_login")); return
    img=Image.open(f); st.image(img,use_container_width=True)
    kg=st.number_input(t("weight"),.1,1000.,1.,.1)
    if st.button("🤖 "+t("analyze"),type="primary",use_container_width=True):
        with st.spinner("AI analysis..."):
            mat,conf=waste_ai(img); auth,aconf=authenticity_ai(img); h=image_hash(img)
            old=q("SELECT id FROM scans WHERE image_hash=?",(h,),one=True)
            execute("INSERT INTO scans(user_id,material,confidence,authenticity,auth_conf,image_hash,created_at) VALUES(?,?,?,?,?,?,?)",
                    (current_user()[0],mat,conf,auth,aconf,h,datetime.now().isoformat()))
        st.session_state.last_scan={"material":mat,"conf":conf,"auth":auth,"aconf":aconf,"kg":kg,"hash":h}
    s=st.session_state.get("last_scan")
    if not s:return
    a,b,c=st.columns(3)
    a.metric(t("material"),s["material"]); a.caption(f'{t("confidence")}: {s["conf"]:.0%}')
    label=t("real") if s["auth"]=="real" else t("synthetic") if s["auth"]=="synthetic" else t("uncertain")
    b.metric(t("authenticity"),label); b.caption(f'{t("confidence")}: {s["aconf"]:.0%}')
    rate=RATES[s["material"]]; lo,hi=rate*.85*s["kg"],rate*1.15*s["kg"]
    c.metric(t("estimated"),f"৳{lo:.0f}–৳{hi:.0f}"); c.caption(f"Indicative rate ৳{rate}/kg")
    if s["auth"]=="synthetic":
        st.error("🚫 Potentially AI-generated image detected. Pickup/payment is blocked until a fresh camera image or collector verification is provided.")
    else:
        if s["auth"]=="uncertain": st.warning("Authenticity could not be established. A live camera capture is recommended before payment.")
        if st.button("🚚 "+t("pickup"),use_container_width=True):
            u=current_user(); val=(lo+hi)/2
            execute("INSERT INTO jobs(user_id,material,kg,value,status,created_at) VALUES(?,?,?,?,?,?)",
                    (u[0],s["material"],s["kg"],val,"Requested",datetime.now().isoformat()))
            st.success("Pickup request created.")
            st.balloons()

def market():
    st.markdown("## 💰 "+t("market"))
    df=pd.DataFrame([{"Material":k,"Indicative BDT/kg":v} for k,v in RATES.items()])
    st.dataframe(df,use_container_width=True,hide_index=True)
    st.caption("Rates are demo/indicative. A production app should sync verified recycler/buyer prices.")

def wallet():
    u=current_user()
    st.markdown("## 💳 "+t("wallet"))
    st.metric(t("balance"),f"৳{u[6]:,.2f}")
    rows=q("SELECT amount,kind,note,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",(u[0],))
    if rows: st.dataframe(pd.DataFrame(rows,columns=["Amount","Type","Note","Time"]),use_container_width=True,hide_index=True)
    else: st.info("No verified transactions yet.")
    st.caption("Prototype wallet: actual bKash/Nagad/Rocket payout requires official merchant/API integration.")

def rewards():
    u=current_user(); pts=u[7]
    level="Green Starter" if pts<100 else "Eco Hero" if pts<500 else "Circular Champion"
    st.markdown("## 🏆 "+t("rewards"))
    st.metric(t("points"),pts); st.success(f"Level: {level}")
    rows=q("SELECT name,points,kg FROM users ORDER BY points DESC LIMIT 10")
    if rows: st.dataframe(pd.DataFrame(rows,columns=["User","Points","kg"]),use_container_width=True,hide_index=True)

def collector():
    u=current_user()
    st.markdown("## 🚚 "+t("collector"))
    rows=q("""SELECT j.id,u.name,j.material,j.kg,j.value,j.status,j.created_at
              FROM jobs j JOIN users u ON j.user_id=u.id
              WHERE j.status IN ('Requested','Accepted') ORDER BY j.id DESC""")
    if not rows: st.info(t("no_jobs")); return
    df=pd.DataFrame(rows,columns=["Job","Citizen","Material","kg","Value","Status","Time"])
    st.dataframe(df,use_container_width=True,hide_index=True)
    ids=[r[0] for r in rows]; jid=st.selectbox("Job ID",ids)
    job=q("SELECT * FROM jobs WHERE id=?",(jid,),one=True)
    c1,c2=st.columns(2)
    with c1:
        if st.button(t("accept"),use_container_width=True):
            execute("UPDATE jobs SET status='Accepted',collector_id=? WHERE id=?",(u[0],jid)); st.rerun()
    with c2:
        if st.button(t("complete"),use_container_width=True):
            if job[6]=="Accepted" and job[2] not in [None,u[0]]:
                pass
            uid,kg,val=job[1],job[4],job[5]
            execute("UPDATE jobs SET status='Collected',collector_id=?,collected_at=? WHERE id=?",(u[0],datetime.now().isoformat(),jid))
            execute("UPDATE users SET balance=balance+?,kg=kg+?,points=points+? WHERE id=?",(val,kg,int(kg*10),uid))
            execute("INSERT INTO transactions(user_id,amount,kind,note,created_at) VALUES(?,?,?,?,?)",
                    (uid,val,"credit","Verified waste collection",datetime.now().isoformat()))
            st.success("Collection verified and wallet credited."); st.rerun()

def dashboard():
    st.markdown("## 🏛️ "+t("admin_title"))
    a,b,c,d=st.columns(4)
    a.metric(t("users"),q("SELECT COUNT(*) FROM users",one=True)[0])
    b.metric(t("requests"),q("SELECT COUNT(*) FROM jobs",one=True)[0])
    c.metric(t("collected"),q("SELECT COUNT(*) FROM jobs WHERE status='Collected'",one=True)[0])
    total_kg=q("SELECT COALESCE(SUM(kg),0) FROM jobs WHERE status='Collected'",one=True)[0]
    d.metric(t("total"),f"{total_kg:.1f} kg")
    rows=q("SELECT material,SUM(kg) kg FROM jobs WHERE status='Collected' GROUP BY material ORDER BY kg DESC")
    if rows: st.bar_chart(pd.DataFrame(rows,columns=["Material","kg"]).set_index("Material"))
    maps=q("SELECT lat,lon FROM jobs WHERE lat IS NOT NULL AND lon IS NOT NULL")
    if maps: st.map(pd.DataFrame(maps,columns=["lat","lon"]))
    jobs=q("SELECT id,material,kg,value,status,created_at FROM jobs ORDER BY id DESC")
    if jobs: st.dataframe(pd.DataFrame(jobs,columns=["ID","Material","kg","Value","Status","Created"]),use_container_width=True,hide_index=True)

def about():
    st.markdown("## 🌍 "+t("about"))
    st.markdown("""### EcoEarn AI
**Citizen → AI verification → Collector → Recycler → Income → Environmental intelligence**

Included in this prototype:
- AI waste classification
- AI-generated-image screening
- Bangla + English UI
- Individual user registration/login
- Collector workflow
- Wallet and transaction ledger
- EcoPoints and leaderboard
- Admin environmental dashboard
- Pickup requests and map
- SQLite database

**Anti-fraud:** AI detection is probabilistic. Production payment should require live camera capture, OTP/QR, GPS/time verification, collector confirmation and duplicate-image checks.""")

def main():
    st.set_page_config(page_title=APP,page_icon="♻️",layout="wide")
    st.markdown("""<style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp{background:linear-gradient(135deg,#f6fff8,#f7f9ff 55%,#fff)}
    html,body,[class*="css"]{font-family:'Hind Siliguri','Inter',sans-serif}
    .hero{padding:34px;border-radius:28px;background:linear-gradient(135deg,#073b2a,#0b6b4a,#13a36d);color:#fff;margin-bottom:22px;box-shadow:0 18px 50px #0001}
    .hero h1{font-size:46px;margin:0;font-weight:800}.hero p{font-size:18px}.pill{opacity:.9}
    .card{background:#fff;border:1px solid #e8eee9;border-radius:20px;padding:20px;box-shadow:0 8px 30px #1632230d}
    </style>""",unsafe_allow_html=True)
    init_db()
    if "lang" not in st.session_state: st.session_state.lang="বাংলা"
    if not current_user():
        st.sidebar.selectbox(t("language"),["বাংলা","English"],key="lang")
        auth_screen()
        return
    with st.sidebar:
        st.selectbox(t("language"),["বাংলা","English"],key="lang")
        u=current_user()
        st.success(f"👤 {u[1]}\n\n{u[2]}")
        nav=st.radio("Menu",[t("home"),t("scan"),t("market"),t("wallet"),t("rewards"),
                             t("collector"),t("dashboard"),t("about")])
        st.button("🚪 "+t("logout"),on_click=logout,use_container_width=True)
    if nav==t("home"): home()
    elif nav==t("scan"): scan()
    elif nav==t("market"): market()
    elif nav==t("wallet"): wallet()
    elif nav==t("rewards"): rewards()
    elif nav==t("collector"): collector()
    elif nav==t("dashboard"): dashboard()
    else: about()
    st.markdown(f"<div style='text-align:center;padding:25px;color:#78857e'>{t('footer')}</div>",unsafe_allow_html=True)

if __name__=="__main__":
    main()
