import streamlit as st
from pathlib import Path
from datetime import datetime
import sqlite3, hashlib, json, os, math, re
from PIL import Image, ImageOps
import pandas as pd

# Optional AI providers
try:
    from huggingface_hub import InferenceClient
except Exception:
    InferenceClient = None

APP_NAME = "EcoEarn AI"
DB_PATH = Path("ecoearn.db")
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

LANG = {
    "English": {
        "tagline": "Don't Throw It. Earn From It.",
        "subtitle": "AI-powered waste-to-income and circular economy platform for Bangladesh.",
        "home": "Home", "scan": "Scan Waste", "market": "Waste Market",
        "collector": "Collector", "wallet": "Wallet", "rewards": "EcoPoints",
        "dashboard": "Admin Dashboard", "about": "About",
        "login": "Login / Register", "language": "Language",
        "upload": "Upload a real waste photo", "camera": "Take a photo",
        "analyze": "Analyze Waste", "result": "AI Analysis",
        "authenticity": "Image Authenticity", "estimated": "Estimated Value",
        "pickup": "Request Pickup", "no_image": "Please upload or capture an image first.",
        "demo": "Demo mode is active. Add a Hugging Face token in Streamlit Secrets for stronger AI detection.",
        "real": "Likely real", "synthetic": "Possibly AI-generated",
        "uncertain": "Uncertain", "confidence": "Confidence",
        "weight": "Estimated weight (kg)", "material": "Detected material",
        "price": "Indicative price/kg", "range": "Estimated total",
        "name": "Name", "phone": "Phone", "save": "Save",
        "points": "points", "balance": "Balance", "history": "History",
        "welcome": "Welcome to EcoEarn AI", "stats": "Your impact",
        "kg": "kg recycled", "income": "earned", "requests": "pickup requests",
        "secure": "Safety & anti-fraud", "footer": "EcoEarn AI — Prototype for Bangladesh",
        "login_hint": "Use any name and phone for the prototype.",
        "collector_jobs": "Available pickup jobs", "accept": "Accept Job",
        "complete": "Mark Collected", "admin": "Environmental Intelligence",
        "hotspot": "Waste hotspots", "total_waste": "Total collected",
        "users": "Users", "jobs": "Jobs", "recycled": "Recycled",
    },
    "বাংলা": {
        "tagline": "ফেলে দেবেন না—বর্জ্য থেকেই আয় করুন।",
        "subtitle": "বাংলাদেশের জন্য AI-ভিত্তিক বর্জ্য থেকে আয় ও circular economy platform।",
        "home": "হোম", "scan": "বর্জ্য স্ক্যান", "market": "বর্জ্য বাজার",
        "collector": "কালেক্টর", "wallet": "ওয়ালেট", "rewards": "EcoPoints",
        "dashboard": "অ্যাডমিন ড্যাশবোর্ড", "about": "সম্পর্কে",
        "login": "লগইন / রেজিস্টার", "language": "ভাষা",
        "upload": "আসল বর্জ্যের ছবি আপলোড করুন", "camera": "ক্যামেরায় ছবি তুলুন",
        "analyze": "বর্জ্য বিশ্লেষণ করুন", "result": "AI বিশ্লেষণ",
        "authenticity": "ছবির সত্যতা", "estimated": "আনুমানিক মূল্য",
        "pickup": "পিকআপ রিকোয়েস্ট", "no_image": "প্রথমে ছবি আপলোড বা ক্যামেরায় তুলুন।",
        "demo": "Demo mode চালু আছে। আরও শক্তিশালী AI detection-এর জন্য Streamlit Secrets-এ Hugging Face token দিন।",
        "real": "সম্ভবত আসল", "synthetic": "সম্ভবত AI-generated",
        "uncertain": "নিশ্চিত নয়", "confidence": "Confidence",
        "weight": "আনুমানিক ওজন (কেজি)", "material": "শনাক্তকৃত বর্জ্য",
        "price": "আনুমানিক মূল্য/কেজি", "range": "আনুমানিক মোট মূল্য",
        "name": "নাম", "phone": "ফোন", "save": "সেভ",
        "points": "পয়েন্ট", "balance": "ব্যালেন্স", "history": "ইতিহাস",
        "welcome": "EcoEarn AI-তে স্বাগতম", "stats": "আপনার প্রভাব",
        "kg": "কেজি রিসাইকেল", "income": "আয়", "requests": "পিকআপ রিকোয়েস্ট",
        "secure": "নিরাপত্তা ও anti-fraud", "footer": "EcoEarn AI — বাংলাদেশের জন্য Prototype",
        "login_hint": "Prototype-এর জন্য যেকোনো নাম ও ফোন ব্যবহার করুন।",
        "collector_jobs": "উপলব্ধ পিকআপ", "accept": "জব গ্রহণ",
        "complete": "সংগ্রহ সম্পন্ন", "admin": "Environmental Intelligence",
        "hotspot": "Waste hotspot", "total_waste": "মোট সংগ্রহ",
        "users": "ইউজার", "jobs": "জব", "recycled": "রিসাইকেল",
    }
}

MATERIALS = {
    "PET Plastic": 55, "HDPE Plastic": 48, "LDPE Plastic": 35,
    "Paper/Cardboard": 18, "Metal": 85, "Glass": 10,
    "E-waste": 120, "Organic": 3, "Mixed/Unknown": 15
}

def T(key):
    return LANG[st.session_state.lang].get(key, key)

def init_db():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript("""
    CREATE TABLE IF NOT EXISTS users(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT, phone TEXT UNIQUE, role TEXT DEFAULT 'citizen',
        balance REAL DEFAULT 0, points INTEGER DEFAULT 0, kg REAL DEFAULT 0
    );
    CREATE TABLE IF NOT EXISTS jobs(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, material TEXT, kg REAL, value REAL,
        status TEXT DEFAULT 'Requested', collector_id INTEGER,
        lat REAL DEFAULT 24.3745, lon REAL DEFAULT 88.6042,
        created_at TEXT
    );
    CREATE TABLE IF NOT EXISTS transactions(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER, amount REAL, kind TEXT, note TEXT, created_at TEXT
    );
    """)
    con.commit(); con.close()

def db(query, params=(), fetch=False):
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor(); cur.execute(query, params)
    out = cur.fetchall() if fetch else None
    con.commit(); con.close()
    return out

def get_user():
    if "user_id" not in st.session_state: return None
    rows = db("SELECT * FROM users WHERE id=?", (st.session_state.user_id,), True)
    return rows[0] if rows else None

def ensure_demo_user():
    row = db("SELECT id FROM users WHERE phone=?", ("01700000000",), True)
    if row:
        st.session_state.user_id = row[0][0]
        return
    db("INSERT INTO users(name,phone,role) VALUES(?,?,?)",
       ("Demo Citizen","01700000000","citizen"))
    st.session_state.user_id = db("SELECT id FROM users WHERE phone=?", ("01700000000",), True)[0][0]

def image_hash(img):
    img2 = ImageOps.exif_transpose(img).convert("RGB").resize((32,32))
    return hashlib.sha256(img2.tobytes()).hexdigest()

def hf_client():
    token = None
    try:
        token = st.secrets.get("HF_TOKEN")
    except Exception:
        token = os.getenv("HF_TOKEN")
    if InferenceClient and token:
        return InferenceClient(token=token)
    return None

def ai_waste_classification(img):
    """Cloud-friendly zero-shot image classification. Falls back to filename/visual-neutral demo."""
    client = hf_client()
    labels = list(MATERIALS.keys())
    if client:
        try:
            result = client.image_classification(
                img,
                model="openai/clip-vit-base-patch32"
            )
            if result:
                best = max(result, key=lambda x: x.score)
                label = best.label
                # Match model wording to our supported material labels.
                mapping = {
                    "plastic bottle":"PET Plastic", "plastic":"PET Plastic",
                    "bottle":"PET Plastic", "paper":"Paper/Cardboard",
                    "cardboard":"Paper/Cardboard", "metal":"Metal",
                    "glass":"Glass", "electronic device":"E-waste",
                    "food":"Organic", "organic":"Organic"
                }
                for k,v in mapping.items():
                    if k.lower() in label.lower():
                        return v, float(best.score)
        except Exception:
            pass
    # Safe prototype fallback: don't pretend certainty.
    return "Mixed/Unknown", 0.45

def ai_authenticity(img):
    """
    Authenticity gate. A definitive AI-image verdict requires a dedicated detector.
    If HF_TOKEN is configured, call a configurable image detector endpoint.
    Otherwise use a conservative uncertainty result rather than falsely claiming certainty.
    """
    client = hf_client()
    if client:
        detector_model = None
        try:
            detector_model = st.secrets.get("AI_DETECTOR_MODEL")
        except Exception:
            detector_model = os.getenv("AI_DETECTOR_MODEL")
        detector_model = detector_model or "dima806/ai-generated-image-detection"
        try:
            result = client.image_classification(img, model=detector_model)
            if result:
                pairs = [(r.label.lower(), float(r.score)) for r in result]
                ai_score = max([s for l,s in pairs if any(k in l for k in ["fake","ai","generated","synthetic"])], default=0.0)
                real_score = max([s for l,s in pairs if any(k in l for k in ["real","human","authentic"])], default=0.0)
                if ai_score > real_score and ai_score >= 0.65:
                    return "synthetic", ai_score
                if real_score > ai_score and real_score >= 0.65:
                    return "real", real_score
                return "uncertain", max(ai_score, real_score)
        except Exception:
            pass
    return "uncertain", 0.0

def price_for(material, kg):
    rate = MATERIALS.get(material, MATERIALS["Mixed/Unknown"])
    low, high = rate*0.85, rate*1.15
    return low*kg, high*kg, rate

def css():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Hind+Siliguri:wght@400;500;600;700&family=Inter:wght@400;500;600;700;800&display=swap');
    .stApp {background: linear-gradient(135deg,#f6fff8 0%,#f5f7ff 55%,#ffffff 100%);}
    html,body,[class*="css"] {font-family:'Hind Siliguri','Inter',sans-serif;}
    .hero {padding:34px 34px 28px;border-radius:28px;background:linear-gradient(135deg,#073b2a,#0b6b4a 55%,#13a36d);color:white;box-shadow:0 18px 50px rgba(0,80,50,.18);margin-bottom:22px;}
    .hero h1 {font-size:46px;line-height:1.05;margin:0;font-weight:800;}
    .hero p {font-size:18px;opacity:.92;margin:12px 0 0;}
    .pill {display:inline-block;padding:7px 12px;border-radius:999px;background:rgba(255,255,255,.15);margin-bottom:14px;font-size:13px;}
    .card {background:white;border:1px solid #e8eee9;border-radius:20px;padding:20px;box-shadow:0 8px 30px rgba(22,50,35,.06);height:100%;}
    .metric {font-size:30px;font-weight:800;color:#075c42;}
    .small {color:#68756f;font-size:13px;}
    .good {background:#e9fff4;border-left:5px solid #12a66b;padding:12px;border-radius:12px;}
    .warn {background:#fff8e7;border-left:5px solid #e6a300;padding:12px;border-radius:12px;}
    .bad {background:#fff0f0;border-left:5px solid #d83a3a;padding:12px;border-radius:12px;}
    .section {font-size:26px;font-weight:800;margin:18px 0 12px;color:#12382b;}
    .footer {text-align:center;color:#78857e;padding:28px 0 10px;font-size:13px;}
    </style>
    """, unsafe_allow_html=True)

def login():
    with st.sidebar:
        st.subheader(T("login"))
        st.caption(T("login_hint"))
        name = st.text_input(T("name"), value="Abir")
        phone = st.text_input(T("phone"), value="01700000000")
        role = st.selectbox("Role", ["citizen","collector","admin"])
        if st.button(T("save"), use_container_width=True):
            rows = db("SELECT id FROM users WHERE phone=?", (phone,), True)
            if rows:
                uid = rows[0][0]
                db("UPDATE users SET name=?, role=? WHERE id=?", (name,role,uid))
            else:
                db("INSERT INTO users(name,phone,role) VALUES(?,?,?)",(name,phone,role))
                uid = db("SELECT id FROM users WHERE phone=?", (phone,), True)[0][0]
            st.session_state.user_id = uid
            st.rerun()

def home():
    user = get_user()
    st.markdown(f"""
    <div class="hero">
      <div class="pill">♻️ AI • Circular Economy • Bangladesh</div>
      <h1>{APP_NAME}</h1>
      <p>{T("tagline")}<br>{T("subtitle")}</p>
    </div>
    """, unsafe_allow_html=True)
    st.markdown(f'<div class="section">{T("welcome")}</div>', unsafe_allow_html=True)
    c1,c2,c3,c4 = st.columns(4)
    vals = [(user[6],T("kg")), (user[4], "৳ "+T("income")), (user[5],T("points")), (len(db("SELECT id FROM jobs WHERE user_id=?",(user[0],),True)),T("requests"))]
    for c,(v,l) in zip([c1,c2,c3,c4],vals):
        with c:
            st.markdown(f'<div class="card"><div class="metric">{v}</div><div class="small">{l}</div></div>',unsafe_allow_html=True)
    st.markdown(f'<div class="section">{T("stats")}</div>',unsafe_allow_html=True)
    a,b,c = st.columns(3)
    with a: st.markdown('<div class="card"><b>📸 AI Scan</b><br>Detect material, estimate value and screen suspicious images.</div>',unsafe_allow_html=True)
    with b: st.markdown('<div class="card"><b>🚚 Smart Pickup</b><br>Connect citizens with nearby collectors and optimize routes.</div>',unsafe_allow_html=True)
    with c: st.markdown('<div class="card"><b>🏛️ Government Intelligence</b><br>Track collection, hotspots and recycling impact.</div>',unsafe_allow_html=True)

def scan():
    st.markdown(f'<div class="section">📸 {T("scan")}</div>',unsafe_allow_html=True)
    source = st.radio("Source", [T("upload"), T("camera")], horizontal=True)
    file = st.file_uploader(T("upload"), type=["jpg","jpeg","png","webp"]) if source == T("upload") else st.camera_input(T("camera"))
    if not file:
        st.info(T("no_image")); return
    img = Image.open(file)
    st.image(img, caption="Input", use_container_width=True)
    kg = st.number_input(T("weight"), min_value=0.1, max_value=1000.0, value=1.0, step=0.1)
    if st.button("🤖 "+T("analyze"), type="primary", use_container_width=True):
        with st.spinner("AI analyzing..."):
            material, mconf = ai_waste_classification(img)
            auth, aconf = ai_authenticity(img)
            low, high, rate = price_for(material, kg)
        st.markdown(f'<div class="section">{T("result")}</div>',unsafe_allow_html=True)
        x,y,z = st.columns(3)
        with x:
            st.markdown(f'<div class="card"><b>{T("material")}</b><div class="metric">{material}</div><div class="small">{T("confidence")}: {mconf:.0%}</div></div>',unsafe_allow_html=True)
        with y:
            label = T("real") if auth=="real" else T("synthetic") if auth=="synthetic" else T("uncertain")
            cls = "good" if auth=="real" else "bad" if auth=="synthetic" else "warn"
            st.markdown(f'<div class="card"><b>{T("authenticity")}</b><div class="{cls}" style="margin-top:12px">{label}<br>{T("confidence")}: {aconf:.0%}</div></div>',unsafe_allow_html=True)
        with z:
            st.markdown(f'<div class="card"><b>{T("range")}</b><div class="metric">৳{low:.0f}–৳{high:.0f}</div><div class="small">৳{rate}/kg • {kg:.1f} kg</div></div>',unsafe_allow_html=True)
        if auth == "synthetic":
            st.error("🚫 This image appears potentially AI-generated. For anti-fraud protection, pickup/payment should require a fresh camera photo or collector verification.")
            return
        if auth == "uncertain":
            st.warning(T("demo"))
        if st.button("🚚 "+T("pickup"), use_container_width=True):
            user = get_user()
            value = (low+high)/2
            db("""INSERT INTO jobs(user_id,material,kg,value,status,created_at)
                  VALUES(?,?,?,?,?,?)""",(user[0],material,kg,value,"Requested",datetime.now().isoformat()))
            db("UPDATE users SET points=points+? WHERE id=?",(max(1,int(kg*10)),user[0]))
            st.success("Pickup request created successfully.")
            st.balloons()

def market():
    st.markdown(f'<div class="section">💰 {T("market")}</div>',unsafe_allow_html=True)
    data = [{"Material":k,"Indicative BDT/kg":v,"Eco status":"Recyclable" if k!="Organic" else "Compostable"} for k,v in MATERIALS.items()]
    st.dataframe(pd.DataFrame(data), use_container_width=True, hide_index=True)
    st.caption("Indicative rates only. Final price must be verified at collection/recycler level.")

def wallet():
    user=get_user()
    st.markdown(f'<div class="section">💳 {T("wallet")}</div>',unsafe_allow_html=True)
    st.metric(T("balance"),f"৳{user[4]:.2f}")
    rows=db("SELECT amount,kind,note,created_at FROM transactions WHERE user_id=? ORDER BY id DESC",(user[0],),True)
    if rows:
        st.dataframe(pd.DataFrame(rows,columns=["Amount","Type","Note","Time"]),use_container_width=True,hide_index=True)
    else: st.info("No transactions yet.")

def rewards():
    user=get_user()
    st.markdown(f'<div class="section">🏆 {T("rewards")}</div>',unsafe_allow_html=True)
    pts=user[5]
    level = "Green Starter" if pts<100 else "Eco Hero" if pts<500 else "Circular Champion"
    st.markdown(f'<div class="card"><div class="metric">{pts} {T("points")}</div><b>{level}</b><br><span class="small">Earn points by verified recycling and responsible disposal.</span></div>',unsafe_allow_html=True)

def collector():
    user=get_user()
    st.markdown(f'<div class="section">🚚 {T("collector")}</div>',unsafe_allow_html=True)
    rows=db("""SELECT jobs.id,users.name,jobs.material,jobs.kg,jobs.value,jobs.status,jobs.created_at
               FROM jobs JOIN users ON jobs.user_id=users.id
               WHERE jobs.status IN ('Requested','Accepted') ORDER BY jobs.id DESC""",(),True)
    if not rows:
        st.info("No open jobs."); return
    df=pd.DataFrame(rows,columns=["Job","Citizen","Material","kg","Value","Status","Time"])
    st.dataframe(df,use_container_width=True,hide_index=True)
    jobid=st.number_input("Job ID",min_value=int(df["Job"].min()),max_value=int(df["Job"].max()),step=1)
    c1,c2=st.columns(2)
    with c1:
        if st.button(T("accept"),use_container_width=True):
            db("UPDATE jobs SET status='Accepted',collector_id=? WHERE id=?",(user[0],jobid)); st.rerun()
    with c2:
        if st.button(T("complete"),use_container_width=True):
            row=db("SELECT user_id,kg,value FROM jobs WHERE id=?",(jobid,),True)
            if row:
                uid,kg,value=row[0]
                db("UPDATE jobs SET status='Collected',collector_id=? WHERE id=?",(user[0],jobid))
                db("UPDATE users SET balance=balance+?,kg=kg+?,points=points+? WHERE id=?",(value,kg,int(kg*20),uid))
                db("INSERT INTO transactions(user_id,amount,kind,note,created_at) VALUES(?,?,?,?,?)",(uid,value,"credit","Verified waste collection",datetime.now().isoformat()))
                st.success("Collection completed and citizen wallet credited.")
                st.rerun()

def dashboard():
    st.markdown(f'<div class="section">🏛️ {T("admin")}</div>',unsafe_allow_html=True)
    users=db("SELECT COUNT(*) FROM users",(),True)[0][0]
    jobs=db("SELECT COUNT(*) FROM jobs",(),True)[0][0]
    kg=db("SELECT COALESCE(SUM(kg),0) FROM jobs WHERE status='Collected'",(),True)[0][0]
    a,b,c=st.columns(3)
    a.metric(T("users"),users); b.metric(T("jobs"),jobs); c.metric(T("total_waste"),f"{kg:.1f} kg")
    st.subheader("Waste activity")
    rows=db("""SELECT material, SUM(kg) kg, COUNT(*) jobs
               FROM jobs GROUP BY material ORDER BY kg DESC""",(),True)
    if rows:
        st.bar_chart(pd.DataFrame(rows,columns=["Material","kg","jobs"]).set_index("Material")["kg"])
    st.subheader("Pickup map data")
    rows=db("SELECT id,material,kg,value,lat,lon,status,created_at FROM jobs ORDER BY id DESC",(),True)
    if rows:
        df=pd.DataFrame(rows,columns=["id","material","kg","value","lat","lon","status","created_at"])
        st.map(df[["lat","lon"]])
        st.dataframe(df,use_container_width=True,hide_index=True)

def about():
    st.markdown(f'<div class="section">🌍 {T("about")}</div>',unsafe_allow_html=True)
    st.markdown("""
    <div class="card">
    <h3>EcoEarn AI</h3>
    <p><b>Citizen → AI verification → Collector → Recycler → Income → Government intelligence.</b></p>
    <ul>
      <li>AI waste classification</li>
      <li>AI-generated image screening / authenticity gate</li>
      <li>Indicative local waste pricing</li>
      <li>Smart pickup workflow</li>
      <li>Wallet, points and transaction history</li>
      <li>Collector operations</li>
      <li>Government/admin environmental dashboard</li>
      <li>Bangla + English interface</li>
    </ul>
    <p><b>Important:</b> AI image-authenticity detection is a probabilistic security layer, not legal proof. High-risk cases should require live camera capture, OTP/QR verification and collector confirmation.</p>
    </div>
    """,unsafe_allow_html=True)

def main():
    st.set_page_config(page_title=APP_NAME,page_icon="♻️",layout="wide",initial_sidebar_state="expanded")
    css(); init_db()
    if "lang" not in st.session_state: st.session_state.lang="বাংলা"
    with st.sidebar:
        st.session_state.lang=st.selectbox(T("language"),["বাংলা","English"],index=0 if st.session_state.lang=="বাংলা" else 1)
        st.markdown("---")
        nav=st.radio("Navigate",[
            T("home"),T("scan"),T("market"),T("collector"),T("wallet"),T("rewards"),T("dashboard"),T("about")
        ])
    login()
    if not get_user(): ensure_demo_user()
    mapping={T("home"):home,T("scan"):scan,T("market"):market,T("collector"):collector,
             T("wallet"):wallet,T("rewards"):rewards,T("dashboard"):dashboard,T("about"):about}
    mapping[nav]()
    st.markdown(f'<div class="footer">{T("footer")} • {datetime.now().year}</div>',unsafe_allow_html=True)

if __name__=="__main__":
    main()
