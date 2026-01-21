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

st.set_page_config(page_title="Urban Perception Study", layout="centered")

# --- 2. 极致排版 CSS ---
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
    @media (max-width: 640px) {
        .stImage img { max-height: 28vh !important; object-fit: cover; border-radius: 10px; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) { display: flex !important; flex-direction: row !important; justify-content: flex-start !important; gap: 10px !important; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) > div { width: auto !important; min-width: 85px !important; flex: none !important; }
        .bottom-btns button { height: 2.2rem !important; font-size: 0.85rem !important; background-color: #f8f9fa !important; border: 1px solid #ddd !important; padding: 0 10px !important; }
        .select-btn button { height: 3.2em !important; font-weight: bold !important; border: 2px solid #000 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 翻译字典 ---
LANG_DICT = {
    "English": {
        "title": "Subjective Perception of Historic Centre Street Images",
        "intro": "Welcome! This research investigates how historic centres are perceived by different people. Your input will help calibrate models to better understand human-scale urban design.",
        "instr_title": "Instructions:",
        "instr_1": "You will be shown **30 pairs** of street-view images.",
        "instr_2": "Select the one that best fits the description provided.",
        "instr_3": "It takes approximately **5-7 minutes** to complete.",
        "role_title": "Please identify your role:",
        "role_res": "I am a resident (Live or work here)",
        "role_tour": "I am a tourist (Visit or travel here)",
        "q_pre": "Which street looks more ", "q_post": "?",
        "btn_back": "⬅️ Back", "btn_skip": "Skip ⏩", "btn_select": "Select Above",
        "success": "✅ Data synced!", "end_title": "Session Complete", "restart": "Restart"
    },
    "中文": {
        "title": "历史中心街景图像主观感知研究",
        "intro": "欢迎！本项研究旨在调查不同人群对历史中心的感知。您的参与将帮助校准模型，以更好地理解人性化城市设计。",
        "instr_title": "指南：",
        "instr_1": "您将看到 **30 对** 街景图像。",
        "instr_2": "请选择最符合描述的一张。",
        "instr_3": "完成约需 **5-7 分钟**。",
        "role_title": "请选择您的角色：",
        "role_res": "我是当地居民（在此居住或工作）",
        "role_tour": "我是游客（在此游览或旅行）",
        "q_pre": "哪条街道看起来更", "q_post": "？",
        "btn_back": "⬅️ 返回", "btn_skip": "跳过 ⏩", "btn_select": "选择上方图片",
        "success": "✅ 数据已同步！", "end_title": "问卷已完成", "restart": "重新开始"
    },
    "Italiano": {
        "title": "Percezione Soggettiva delle Immagini Stradali del Centro Storico",
        "intro": "Benvenuti! Questa ricerca indaga come i centri storici siano percepiti da diverse persone. Il vostro contributo aiuterà a calibrare i modelli per comprendere meglio il design urbano a misura d'uomo.",
        "instr_title": "Istruzioni:",
        "instr_1": "Vi verranno mostrate **30 coppie** di immagini stradali.",
        "instr_2": "Selezionate quella che meglio si adatta alla descrizione fornita.",
        "instr_3": "Il completamento richiede circa **5-7 minuti**.",
        "role_title": "Si prega di identificare il proprio ruolo:",
        "role_res": "Sono un residente (Vivo o lavoro qui)",
        "role_tour": "Sono un turista (Visita o viaggio qui)",
        "q_pre": "Quale strada sembra più ", "q_post": "?",
        "btn_back": "⬅️ Indietro", "btn_skip": "Salta ⏩", "btn_select": "Seleziona sopra",
        "success": "✅ Dati sincronizzati!", "end_title": "Sessione completata", "restart": "Ricomincia"
    }
}

CAT_TRANS = {
    "English": {"Safe": "safe", "Lively": "lively", "Wealthy": "wealthy", "Beautiful": "beautiful", "Boring": "boring", "Depressing": "depressing"},
    "中文": {"Safe": "安全", "Lively": "活跃", "Wealthy": "高档", "Beautiful": "美丽", "Boring": "乏味", "Depressing": "压抑"},
    "Italiano": {"Safe": "sicura", "Lively": "vivace", "Wealthy": "benestante", "Beautiful": "bella", "Boring": "noiosa", "Depressing": "deprimente"}
}

# --- 4. 辅助函数：获取所有图片并标记案例 ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for img in imgs:
                all_data.append((c, img)) # 存储为 (案例名, 文件名)
    return all_data

# --- 5. 状态管理 ---
if 'lang' not in st.session_state: st.session_state.lang = "English"
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []

if 'question_pool' not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5 
    random.shuffle(pool)
    st.session_state.question_pool = pool

# --- 6. 流程逻辑 ---

if st.session_state.step == "onboarding":
    st.session_state.lang = st.radio("Language", ["English", "中文", "Italiano"], horizontal=True)
    T = LANG_DICT[st.session_state.lang] 
    st.title(f"🏙️ {T['title']}")
    st.markdown(f"**{T['intro']}**\n\n**{T['instr_title']}**\n* {T['instr_1']}\n* {T['instr_2']}\n* {T['instr_3']}")
    st.divider()
    st.subheader(T['role_title'])
    c1, c2 = st.columns(2)
    with c1:
        if st.button(T['role_res']): st.session_state.user_type, st.session_state.step = "Resident", "voting"; st.rerun()
    with c2:
        if st.button(T['role_tour']): st.session_state.user_type, st.session_state.step = "Tourist", "voting"; st.rerun()

elif st.session_state.step == "voting":
    T = LANG_DICT[st.session_state.lang]
    all_img_data = load_all_image_data(IMG_DIR, CASES)
    
    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    st.markdown(f'''<div class="progress-container"><div class="progress-bar" style="width: {percent}%;"></div><div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div></div>''', unsafe_allow_html=True)

    # 全随机抽取 2 张图（允许案例相同）
    if 'pair' not in st.session_state:
        selected_pair = random.sample(all_img_data, 2)
        # 结构：(case_l, img_l, case_r, img_r)
        st.session_state.pair = (selected_pair[0][0], selected_pair[0][1], selected_pair[1][0], selected_pair[1][1])
    
    case_l, img_l, case_r, img_r = st.session_state.pair
    cat_eng = st.session_state.question_pool[st.session_state.vote_count]
    display_cat = CAT_TRANS[st.session_state.lang][cat_eng]

    st.markdown(f'<p class="question-text">{T["q_pre"]}<span class="keyword">{display_cat}</span>{T["q_post"]}</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, case_l, img_l), use_container_width=True)
        if st.button(T['btn_select'], key="L"):
            st.session_state.temp_votes.append({"left_img": f"{case_l}/{img_l}", "right_img": f"{case_r}/{img_r}", "winner": "left", "category": cat_eng, "case_l": case_l, "case_r": case_r})
            st.session_state.vote_count += 1; del st.session_state.pair; st.session_state.step = "end" if st.session_state.vote_count >= TARGET_VOTES else "voting"; st.rerun()
    with col2:
        st.image(os.path.join(IMG_DIR, case_r, img_r), use_container_width=True)
        if st.button(T['btn_select'], key="R"):
            st.session_state.temp_votes.append({"left_img": f"{case_l}/{img_l}", "right_img": f"{case_r}/{img_r}", "winner": "right", "category": cat_eng, "case_l": case_l, "case_r": case_r})
            st.session_state.vote_count += 1; del st.session_state.pair; st.session_state.step = "end" if st.session_state.vote_count >= TARGET_VOTES else "voting"; st.rerun()

    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)
        if st.button(T['btn_back'], disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop(); st.session_state.pair = (last["case_l"], last["left_img"].split('/')[-1], last["case_r"], last["right_img"].split('/')[-1]); st.session_state.vote_count -= 1; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)
        if st.button(T['btn_skip']): del st.session_state.pair; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == "end":
    T = LANG_DICT[st.session_state.lang]
    st.balloons(); final_df = pd.DataFrame(st.session_state.temp_votes); final_df["user_type"], final_df["lang"] = st.session_state.user_type, st.session_state.lang
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        conn.update(worksheet="Sheet1", data=pd.concat([existing_data, final_df], ignore_index=True))
        st.success(T['success'])
    except: st.download_button("Download CSV", final_df.to_csv(index=False), "backup.csv")
    if st.button(T['restart']): st.session_state.clear(); st.rerun()
