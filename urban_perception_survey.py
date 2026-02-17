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

st.set_page_config(page_title="Subjective Perception of Historic Centre Street Images", page_icon="🏙️", layout="centered")

# --- 2. 极致排版 CSS (完全保留你的原始样式) ---
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
    /* 弹窗内容滚动美化 */
    div[data-testid="stDialog"] .stMarkdown { max-height: 65vh; overflow-y: auto; font-size: 0.95rem; line-height: 1.5; padding: 10px; }
    @media (max-width: 640px) {
        .stImage img { max-height: 28vh !important; object-fit: cover; border-radius: 10px; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) { display: flex !important; flex-direction: row !important; justify-content: flex-start !important; gap: 10px !important; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) > div { width: auto !important; min-width: 85px !important; flex: none !important; }
        .bottom-btns button { height: 2.2rem !important; font-size: 0.85rem !important; background-color: #f8f9fa !important; color: #666 !important; border: 1px solid #ddd !important; padding: 0 10px !important; }
        .select-btn button { height: 3.2em !important; font-weight: bold !important; border: 2px solid #000 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 翻译字典 (集成 PDF 原文内容) ---
LANG_DICT = {
    "English": {
        "title": "Subjective Perception of Historic Centre Street Images",
        "intro": "Welcome! This research investigates how historic centres are perceived. Your input helps calibrate our models.",
        "privacy_btn": "📄 View Information Sheet",
        "privacy_content": """
            **1. Project Lead**: Prof. Elisa Conticelli (University of Bologna).
            **2. Objectives**: To understand how people evaluate the quality of streets in Italian historic centres.
            **3. Participation**: A short online survey (~5 min) comparing image pairs from Florence, Ravenna, Bologna, and Ferrara.
            **4. Benefits & Risks**: Voluntary and free. No known risks or discomforts.
            **5. Withdrawal**: Right to withdraw at any time without providing a reason.
            **6. Results**: Right to request information on research findings.
            **7. Anonymity**: Natively anonymous. No IP or identifying data recorded.
            **8. Contacts**: Prof. Elisa Conticelli (elisa.conticelli@unibo.it) and Fangyu Chen (fangyu.chen2@unibo.it).
        """,
        "privacy_agree": "I am 18+, I have read the information and I consent to participate.",
        "instr_title": "Instructions:",
        "instr_1": "You will be shown **30 pairs** of street-view images.",
        "instr_2": "Select the one that best fits the description.",
        "instr_3": "It takes about **5 minutes**.",
        "role_title": "Please identify your role:",
        "role_res": "Resident", "role_tour": "Tourist",
        "q_pre": "Which street looks more ", "q_post": "?",
        "btn_back": "⬅️ Back", "btn_skip": "Skip ⏩", "btn_select": "Select Above",
        "success": "✅ Data synced!", "end_title": "Completed", "thank_you": "Thank you for your time!", "restart": "Restart"
    },
    "中文": {
        "title": "历史中心街景主观感知研究",
        "intro": "欢迎！本项研究旨在调查人们对历史中心的感知。您的参与将帮助我们校准模型。",
        "privacy_btn": "📄 查看知情告知书全文",
        "privacy_content": """
            **1. 项目负责人**：Elisa Conticelli 教授（博洛尼亚大学）。
            **2. 研究目标**：了解公众如何评价意大利历史中心街道的空间质量。
            **3. 参与过程**：完成一份约 5 分钟的在线问卷，对比随机抽取的佛罗伦萨、拉文纳、博洛尼亚和费拉拉的街景照片。
            **4. 利益与风险**：自愿且免费参加。不存在已知风险或不便。
            **5. 退出权利**：您有权随时中断参与，无需说明理由。
            **6. 结果获取**：您有权了解研究的最终学术成果。
            **7. 匿名保护**：本研究为原生匿名。系统不记录 IP 地址或身份信息。
            **8. 联系方式**：Elisa Conticelli 教授 (elisa.conticelli@unibo.it) 或 陈方宇 (fangyu.chen2@unibo.it)。
        """,
        "privacy_agree": "我已年满18周岁，阅读并同意上述告知书内容。",
        "instr_title": "指南：",
        "instr_1": "您将看到 **30 对** 街景图像。",
        "instr_2": "请选择最符合描述的一张。",
        "instr_3": "完成约需 **5 分钟**。",
        "role_title": "请选择您的角色：",
        "role_res": "当地居民", "role_tour": "游客",
        "q_pre": "哪条街道看起来更", "q_post": "？",
        "btn_back": "⬅️ 返回", "btn_skip": "跳过 ⏩", "btn_select": "选择上方图片",
        "success": "✅ 数据已同步！", "end_title": "问卷已完成", "thank_you": "感谢您的参与！", "restart": "重新开始"
    },
    "Italiano": {
        "title": "Percezione Soggettiva delle Immagini Stradali del Centro Storico",
        "intro": "Benvenuti! Questa ricerca indaga la percezione dei centri storici. Il vostro contributo aiuta a calibrare i nostri modelli.",
        "privacy_btn": "📄 Leggi Informativa Completa",
        "privacy_content": """
            **1. Responsabile progetto**: Prof.ssa Elisa Conticelli (Università di Bologna).
            **2. Obiettivi**: Capire come le persone valutano la qualità delle strade nei centri storici italiani.
            **3. Partecipazione**: Questionario online (circa 5 min). Confronto di immagini di Firenze, Ravenna, Bologna e Ferrara.
            **4. Benefici e rischi**: La partecipazione è volontaria e gratuita. Non comporta rischi o disagi.
            **5. Ritiro**: Diritto di ritirare il consenso in qualsiasi momento senza motivazione.
            **6. Restituzione**: Diritto a richiedere informazioni sui risultati della ricerca.
            **7. Anonimato**: La raccolta è nativamente anonima. Non vengono registrati indirizzi IP o dati identificativi.
            **8. Contatti**: Prof.ssa Elisa Conticelli (elisa.conticelli@unibo.it) e Fangyu Chen (fangyu.chen2@unibo.it).
        """,
        "privacy_agree": "Dichiaro di essere maggiorenne, ho letto l'informativa e acconsento.",
        "instr_title": "Istruzioni:",
        "instr_1": "Vi verranno mostrate **30 coppie** di immagini.",
        "instr_2": "Selezionate quella che meglio si adatta alla descrizione.",
        "instr_3": "Richiede circa **5 minuti**.",
        "role_title": "Seleziona il tuo ruolo:",
        "role_res": "Residente", "role_tour": "Turista",
        "q_pre": "Quale strada sembra più ", "q_post": "?",
        "btn_back": "⬅️ Indietro", "btn_skip": "Salta ⏩", "btn_select": "Seleziona sopra",
        "success": "✅ Dati sincronizzati!", "end_title": "Completato", "thank_you": "Grazie per il tuo tempo!", "restart": "Ricomincia"
    }
}

CAT_TRANS = {
    "English": {"Safe": "safe", "Lively": "lively", "Wealthy": "wealthy", "Beautiful": "beautiful", "Boring": "boring", "Depressing": "depressing"},
    "中文": {"Safe": "安全", "Lively": "活跃", "Wealthy": "高档", "Beautiful": "美丽", "Boring": "乏味", "Depressing": "压抑"},
    "Italiano": {"Safe": "sicura", "Lively": "vivace", "Wealthy": "benestante", "Beautiful": "bella", "Boring": "noiosa", "Depressing": "deprimente"}
}

# --- 4. 核心功能 ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for img in imgs: all_data.append((c, img))
    return all_data

# --- 5. 弹窗对话框函数 ---
@st.dialog("Information Sheet / Informativa")
def show_privacy_modal(content):
    st.markdown(content)
    if st.button("Close / Chiudi / 关闭"):
        st.rerun()

# --- 6. 状态管理 ---
if 'lang' not in st.session_state: st.session_state.lang = "English"
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'question_pool' not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool

# --- 7. 逻辑流 ---
if st.session_state.step == "onboarding":
    st.session_state.lang = st.radio("Language", ["English", "中文", "Italiano"], horizontal=True)
    T = LANG_DICT[st.session_state.lang] 
    st.title(f"🏙️ {T['title']}")
    st.markdown(f"{T['intro']}\n\n**{T['instr_title']}**\n* {T['instr_1']}\n* {T['instr_2']}\n* {T['instr_3']}")
    
    st.divider()
    
    # 弹窗按钮
    if st.button(T['privacy_btn']):
        show_privacy_modal(T['privacy_content'])
    
    # 同意勾选
    agree = st.checkbox(T['privacy_agree'])
    
    st.subheader(T['role_title'])
    c1, c2 = st.columns(2)
    with c1:
        if st.button(T['role_res'], disabled=not agree): st.session_state.user_type, st.session_state.step = "Resident", "voting"; st.rerun()
    with c2:
        if st.button(T['role_tour'], disabled=not agree): st.session_state.user_type, st.session_state.step = "Tourist", "voting"; st.rerun()

elif st.session_state.step == "voting":
    # --- 完全保留你原始的投票逻辑 ---
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
    # --- 完全保留你原始的结束逻辑 ---
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
        st.error("Sync Error")
        st.download_button("Download CSV", final_df.to_csv(index=False), "backup.csv")
    
    if st.button(T['restart']): st.session_state.clear(); st.rerun()
