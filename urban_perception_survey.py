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

# 标题参考自伦理申请表 [cite: 23]
st.set_page_config(page_title="Urban Perception Study - UNIBO", page_icon="🏙️", layout="centered")

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
    /* 弹窗内部滚动与间距优化 */
    div[data-testid="stDialog"] .stMarkdown { 
        max-height: 70vh; 
        overflow-y: auto; 
        font-size: 0.95rem; 
        line-height: 1.6; 
        padding: 15px; 
        background: #ffffff;
    }
    @media (max-width: 640px) {
        .stImage img { max-height: 28vh !important; object-fit: cover; border-radius: 10px; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 完整知情告知书内容 (基于 PDF 翻译) ---
# 内容严格对应伦理申请表各章节 [cite: 95, 109, 117, 121, 134]
LANG_DICT = {
    "English": {
        "title": "Subjective Perception of Historic Centre Street Images",
        "intro": "Welcome! This PhD research is led by Prof. Elisa Conticelli at the University of Bologna.",
        "privacy_btn": "📄 View Full Information Sheet (Legal)",
        "privacy_content": """
            ### INFORMATION SHEET & INFORMED CONSENT
            **1. Project Lead**: Prof. Elisa Conticelli (University of Bologna)[cite: 138].
            **2. Objectives**: To understand how people evaluate the quality (pleasantness, safety) of streets in Italian historic centres[cite: 109].
            **3. Participation**: A short online survey (~5 min). You will compare pairs of images from Florence, Ravenna, Bologna, and Ferrara[cite: 117, 132].
            **4. Benefits & Risks**: Voluntary and free. No known risks or discomforts[cite: 251].
            **5. Withdrawal**: Right to withdraw at any time without providing a reason[cite: 125, 131].
            **6. Results**: Right to request information on research findings[cite: 244].
            **7. Anonymity**: Natively anonymous collection. No IP or identifying data recorded[cite: 134, 249]. 
            **8. Contacts**: Prof. Elisa Conticelli (elisa.conticelli@unibo.it) and Fangyu Chen (fangyu.chen2@unibo.it)[cite: 138, 139].
        """,
        "privacy_agree": "I am 18+, I have read the information and I consent to participate[cite: 121, 250].",
        "role_title": "Please identify your role:",
        "role_res": "Resident", "role_tour": "Tourist",
        "q_pre": "Which street looks more ", "q_post": "?",
        "btn_select": "Select Above", "success": "✅ Data synced!", "thank_you": "Thank you!"
    },
    "Italiano": {
        "title": "Percezione Soggettiva dei Centri Storici",
        "intro": "Benvenuti! Questa ricerca è coordinata dalla Prof.ssa Elisa Conticelli dell'Università di Bologna.",
        "privacy_btn": "📄 Leggi Informativa Completa (Legale)",
        "privacy_content": """
            ### SCHEDA INFORMATIVA E CONSENSO INFORMATO
            **1. Responsabile progetto**: Prof.ssa Elisa Conticelli (Università di Bologna)[cite: 138].
            **2. Obiettivi**: Capire come le persone valutano la qualità (piacevolezza, sicurezza) delle strade nei centri storici italiani[cite: 109].
            **3. Partecipazione**: Questionario online (circa 5 min). Confronto di immagini di Firenze, Ravenna, Bologna e Ferrara[cite: 117, 132].
            **4. Benefici e rischi**: Partecipazione volontaria e gratuita. Non comporta rischi o disagi[cite: 251].
            **5. Ritiro**: Diritto di ritirare il consenso in qualsiasi momento senza motivazione[cite: 125, 131].
            **6. Restituzione**: Diritto a richiedere informazioni sui risultati della ricerca[cite: 244].
            **7. Anonimato**: La raccolta è nativamente anonima. Nessun dato identificativo registrato[cite: 134, 249].
            **8. Contatti**: Prof.ssa Elisa Conticelli (elisa.conticelli@unibo.it) e Fangyu Chen (fangyu.chen2@unibo.it)[cite: 138, 139].
        """,
        "privacy_agree": "Dichiaro di essere maggiorenne, ho letto l'informativa e acconsento[cite: 121, 250].",
        "role_title": "Seleziona il tuo ruolo:",
        "role_res": "Residente", "role_tour": "Turista",
        "q_pre": "Quale strada sembra più ", "q_post": "?",
        "btn_select": "Seleziona sopra", "success": "✅ Dati sincronizzati!", "thank_you": "Grazie!"
    },
    "中文": {
        "title": "历史中心街景主观感知研究",
        "intro": "欢迎！本研究由博洛尼亚大学 Elisa Conticelli 教授负责。",
        "privacy_btn": "📄 查看知情告知书全文 (法律声明)",
        "privacy_content": """
            ### 参与者知情告知书与知情同意书
            **1. 项目负责人**：Elisa Conticelli 教授（博洛尼亚大学） [cite: 138]。
            **2. 研究目标**：了解公众如何评价意大利历史中心街道的质量（如宜人性、安全性等） [cite: 109]。
            **3. 参与过程**：完成一份约 5 分钟的在线问卷。对比随机抽取的佛罗伦萨、拉文纳、博洛尼亚和费拉拉的街景照片 [cite: 117, 132]。
            **4. 利益与风险**：自愿且免费参加。不存在已知风险或不便 [cite: 251]。
            **5. 退出权利**：您有权随时中断参与，无需说明理由 [cite: 125, 131]。
            **6. 结果获取**：您有权了解研究的最终学术成果 [cite: 244]。
            **7. 匿名保护**：本研究为原生匿名。系统不记录 IP 地址或身份信息 [cite: 134, 249]。
            **8. 联系方式**：Elisa Conticelli 教授 (elisa.conticelli@unibo.it) 或 陈方宇 (fangyu.chen2@unibo.it) [cite: 138, 139]。
        """,
        "privacy_agree": "我已年满18周岁，阅读并同意上述告知书内容 [cite: 121, 250]。",
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

# --- 5. 弹窗对话框定义 ---
@st.dialog("Research Ethics & Privacy")
def show_privacy_modal(content):
    st.markdown(content)
    if st.button("Close / Chiudi / 关闭"):
        st.rerun()

# --- 6. 状态管理 ---
if 'lang' not in st.session_state: st.session_state.lang = "Italiano"
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'question_pool' not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool

# --- 7. 首页逻辑 ---
if st.session_state.step == "onboarding":
    st.session_state.lang = st.radio("Language / 语言 / Lingua", ["English", "Italiano", "中文"], horizontal=True)
    T = LANG_DICT[st.session_state.lang] 
    
    st.title(f"🏙️ {T['title']}")
    st.markdown(f"**{T['intro']}**")
    st.divider()
    
    # 唤起弹窗查看全文
    if st.button(T['privacy_btn'], use_container_width=True):
        show_privacy_modal(T['privacy_content'])
    
    # 强制勾选
    agree = st.checkbox(T['privacy_agree'])
    
    st.write("") 
    st.subheader(T['role_title'])
    c1, c2 = st.columns(2)
    with c1:
        if st.button(T['role_res'], disabled=not agree, use_container_width=True): 
            st.session_state.user_type, st.session_state.step = "Resident", "voting"; st.rerun()
    with c2:
        if st.button(T['role_tour'], disabled=not agree, use_container_width=True): 
            st.session_state.user_type, st.session_state.step = "Tourist", "voting"; st.rerun()

# --- 8. 投票与数据处理逻辑 (同前) ---
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
        if st.button(T['btn_select'], key="L", use_container_width=True):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "left", "category": cat_eng, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
    with col2:
        st.image(os.path.join(IMG_DIR, cr, ir), use_container_width=True)
        if st.button(T['btn_select'], key="R", use_container_width=True):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "right", "category": cat_eng, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

elif st.session_state.step == "end":
    T = LANG_DICT[st.session_state.lang]
    st.balloons(); st.title(f"🎉 {T['thank_you']}"); st.divider()
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"], final_df["lang"] = st.session_state.user_type, st.session_state.lang
    final_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        conn.update(worksheet="Sheet1", data=pd.concat([existing_data, final_df], ignore_index=True))
        st.success(T['success'])
    except: st.download_button("Download CSV Backup", final_df.to_csv(index=False), "backup_csv")
    if st.button("Restart / Riprova / 重新开始", use_container_width=True): st.session_state.clear(); st.rerun()
