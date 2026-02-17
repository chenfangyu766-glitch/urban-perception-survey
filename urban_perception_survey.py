import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images" 
TARGET_VOTES = 30 
CASES = ["CaseA", "CaseB", "CaseC", "CaseD"] 

st.set_page_config(page_title="Urban Perception Study - UNIBO", page_icon="🏙️", layout="centered")

# --- 2. CSS CUSTOMIZATION ---
st.markdown("""
    <style>
    header {visibility: hidden !important; height: 0px !important;}
    footer {visibility: hidden !important;}
    .main .block-container { padding-top: 0.5rem !important; margin-top: -3.5rem !important; max-width: 98% !important; }
    .progress-container { width: 100%; background-color: #f0f2f6; border-radius: 10px; margin: 5px 0px; position: relative; height: 18px; }
    .progress-bar { background-color: #4CAF50; height: 100%; border-radius: 10px; transition: width 0.3s; }
    .progress-text { position: absolute; width: 100%; text-align: center; top: 0; font-size: 12px; line-height: 18px; font-weight: bold; }
    .question-text { font-size: 1.4rem !important; font-weight: 400; text-align: left !important; margin: 10px 0px !important; color: #1E1E1E; }
    .keyword { font-weight: 700; color: #000; } 
    .privacy-box { background-color: #f9f9f9; padding: 15px; border-radius: 10px; border-left: 5px solid #0056b3; font-size: 0.9rem; margin-bottom: 10px; }
    @media (max-width: 640px) {
        .stImage img { max-height: 28vh !important; object-fit: cover; border-radius: 10px; }
        .bottom-btns button { height: 2.2rem !important; font-size: 0.85rem !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. MULTILINGUAL DICTIONARY (INCLUDING PRIVACY) ---
# Content derived from UNIBO Ethics Committee form [cite: 23, 121, 128, 134]
LANG_DICT = {
    "English": {
        "title": "Perception of Historic Centres Study",
        "intro": "Welcome! This research investigates how historic centres are perceived by residents and tourists.",
        "privacy_title": "Legal Information & Consent",
        "privacy_body": """
            - **Purpose**: Academic research for a PhD thesis at the University of Bologna[cite: 7, 242].
            - **Anonymity**: The survey is natively anonymous. No IP addresses or identifying info are recorded.
            - **Data**: Data is stored securely on UNIBO Microsoft OneDrive servers.
            - **Voluntary**: You can withdraw at any time. Participants must be 18+ years old[cite: 121, 250].
        """,
        "privacy_agree": "I am 18+, I have read the information and I consent to participate.",
        "role_title": "Please identify your role:",
        "role_res": "Resident", "role_tour": "Tourist",
        "q_pre": "Which street looks more ", "q_post": "?",
        "btn_select": "Select Above", "success": "✅ Data synced!", "thank_you": "Thank you for your time!"
    },
    "Italiano": {
        "title": "Percezione dei Centri Storici",
        "intro": "Benvenuti! Questa ricerca indaga la percezione dei centri storici italiani tramite immagini di Street View[cite: 23, 117].",
        "privacy_title": "Informativa e Consenso Informato",
        "privacy_body": """
            - **Scopo**: Ricerca accademica per tesi di dottorato presso l'Alma Mater Studiorum[cite: 7, 242].
            - **Anonimato**: La raccolta è nativamente anonima. Nessun dato identificativo registrato.
            - **Sicurezza**: Dati archiviati in modo sicuro su server OneDrive dell'Ateneo.
            - **Consenso**: Partecipazione volontaria riservata a soggetti maggiorenni (18+)[cite: 121, 250].
        """,
        "privacy_agree": "Dichiaro di essere maggiorenne, ho letto l'informativa e acconsento.",
        "role_title": "Seleziona il tuo ruolo:",
        "role_res": "Residente", "role_tour": "Turista",
        "q_pre": "Quale strada sembra più ", "q_post": "?",
        "btn_select": "Seleziona sopra", "success": "✅ Dati sincronizzati!", "thank_you": "Grazie per il tuo tempo!"
    },
    "中文": {
        "title": "历史中心街景感知研究",
        "intro": "欢迎！本研究由博洛尼亚大学开展，旨在调查居民与游客对历史中心的感知差异 [cite: 23, 100]。",
        "privacy_title": "法律信息与知情同意",
        "privacy_body": """
            - **研究目的**: 博洛尼亚大学博士论文科研项目 [cite: 7, 242]。
            - **匿名性**: 本次调研为原生匿名，系统不会记录您的IP地址或个人信息 。
            - **数据存储**: 数据安全存储于博洛尼亚大学官方微软 OneDrive 服务器 。
            - **参与原则**: 参与完全自愿，可随时退出。参与者须年满18周岁 [cite: 121, 250]。
        """,
        "privacy_agree": "我已年满18周岁，阅读并同意上述隐私条款。",
        "role_title": "请选择您的身份：",
        "role_res": "当地居民", "role_tour": "游客",
        "q_pre": "哪条街道看起来更", "q_post": "？",
        "btn_select": "选择上方图片", "success": "✅ 数据已同步！", "thank_you": "感谢您的参与！"
    }
}

CAT_TRANS = {
    "English": {"Safe": "safe", "Lively": "lively", "Wealthy": "wealthy", "Beautiful": "beautiful", "Boring": "boring", "Depressing": "depressing"},
    "中文": {"Safe": "安全", "Lively": "活跃", "Wealthy": "高档", "Beautiful": "美丽", "Boring": "乏味", "Depressing": "压抑"},
    "Italiano": {"Safe": "sicura", "Lively": "vivace", "Wealthy": "benestante", "Beautiful": "bella", "Boring": "noiosa", "Depressing": "deprimente"}
}

# --- 4. CORE FUNCTIONS ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for img in imgs: all_data.append((c, img))
    return all_data

# --- 5. SESSION STATE ---
if 'lang' not in st.session_state: st.session_state.lang = "Italiano"
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'question_pool' not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool

# --- 6. PAGE LOGIC ---
if st.session_state.step == "onboarding":
    st.session_state.lang = st.radio("Language / Lingua / 语言", ["English", "Italiano", "中文"], horizontal=True)
    T = LANG_DICT[st.session_state.lang] 
    st.title(f"🏙️ {T['title']}")
    st.markdown(f"**{T['intro']}**")
    
    # Privacy Box [cite: 130, 131]
    st.markdown(f'<div class="privacy-box"><b>{T["privacy_title"]}</b><br>{T["privacy_body"]}</div>', unsafe_allow_html=True)
    agree = st.checkbox(T['privacy_agree'])
    
    st.divider()
    st.subheader(T['role_title'])
    c1, c2 = st.columns(2)
    with c1:
        if st.button(T['role_res'], disabled=not agree): 
            st.session_state.user_type, st.session_state.step = "Resident", "voting"; st.rerun()
    with c2:
        if st.button(T['role_tour'], disabled=not agree): 
            st.session_state.user_type, st.session_state.step = "Tourist", "voting"; st.rerun()

elif st.session_state.step == "voting":
    T = LANG_DICT[st.session_state.lang]
    all_img_data = load_all_image_data(IMG_DIR, CASES)
    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    st.markdown(f'''<div class="progress-container"><div class="progress-bar" style="width: {percent}%;"></div><div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div></div>''', unsafe_allow_html=True)

    if 'pair' not in st.session_state:
        pair = random.sample(all_img_data, 2)
        st.session_state.pair = (pair[0][0], pair[0][1], pair[1][0], pair[1][1])
    
    cl, il, cr, ir = st.session_state.pair
    cat_eng = st.session_state.question_pool[st.session_state.vote_count]
    display_cat = CAT_TRANS[st.session_state.lang][cat_eng]
    st.markdown(f'<p class="question-text">{T["q_pre"]}<span class="keyword">{display_cat}</span>{T["q_post"]}</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, cl, il), use_container_width=True)
        if st.button(T['btn_select'], key="L"):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "left", "category": cat_eng, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
    with col2:
        st.image(os.path.join(IMG_DIR, cr, ir), use_container_width=True)
        if st.button(T['btn_select'], key="R"):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "right", "category": cat_eng, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

elif st.session_state.step == "end":
    T = LANG_DICT[st.session_state.lang]
    st.balloons()
    st.title(f"🎉 {T['end_title']}")
    st.subheader(T['thank_you'])
    st.divider()

    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"], final_df["lang"] = st.session_state.user_type, st.session_state.lang
    final_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        conn.update(worksheet="Sheet1", data=pd.concat([existing_data, final_df], ignore_index=True))
        st.success(T['success'])
    except:
        st.download_button("Download CSV Backup", final_df.to_csv(index=False), "backup.csv")
    
    if st.button("Restart / Riprova / 重新开始"): st.session_state.clear(); st.rerun()


