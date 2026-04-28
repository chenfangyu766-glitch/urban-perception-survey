import streamlit as st
import pandas as pd
import os
import random
import uuid
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images"
TARGET_VOTES = 30
CASES = ["CaseA", "CaseB", "CaseC", "CaseD"]

st.set_page_config(
    page_title="Subjective Perception of Historic Centre Street Images",
    page_icon="🏙️",
    layout="centered"
)

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

# --- 3. 翻译字典 ---
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

            **7. Anonymity**: The survey is anonymous. Only basic demographic information, including gender, age group, and participant role, is collected. No IP address or identifying data is recorded.

            **8. Contacts**: Prof. Elisa Conticelli (elisa.conticelli@unibo.it) and Fangyu Chen (fangyu.chen2@unibo.it).
        """,
        "privacy_agree": "I am 18+, I have read the information and I consent to participate.",

        "instr_title": "Instructions:",
        "instr_1": "You will be shown **30 pairs** of street-view images.",
        "instr_2": "Select the one that best fits the description.",
        "instr_3": "It takes about **5 minutes**.",
        "instr_4": "If you cannot decide, or if the two images look equally safe, lively, boring, etc., please use **Skip**.",

        "gender_title": "Please select your gender:",
        "gender_placeholder": "Please select",
        "gender_options": {
            "Male": "Male",
            "Female": "Female"
        },

        "age_title": "Please select your age group:",
        "age_placeholder": "Please select",
        "age_options": {
            "18-29": "18–29",
            "30-44": "30–44",
            "45-59": "45–59",
            "60+": "60 or above"
        },

        "role_title": "Please identify your role:",
        "role_res": "Resident",
        "role_tour": "Tourist",

        "q_pre": "Which street looks more ",
        "q_post": "?",
        "btn_back": "⬅️ Back",
        "btn_skip": "Skip ⏩",
        "btn_select": "Select Above",
        "success": "✅ Data synced!",
        "end_title": "Completed",
        "thank_you": "Thank you for your time!",
        "restart": "Restart"
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

            **7. 匿名保护**：本研究为匿名问卷，仅收集性别、年龄组和参与者身份类型等基础人口统计信息。系统不记录 IP 地址或身份识别信息。

            **8. 联系方式**：Elisa Conticelli 教授 (elisa.conticelli@unibo.it) 或 陈方宇 (fangyu.chen2@unibo.it)。
        """,
        "privacy_agree": "我已年满18周岁，阅读并同意上述告知书内容。",

        "instr_title": "指南：",
        "instr_1": "您将看到 **30 对** 街景图像。",
        "instr_2": "请选择最符合描述的一张。",
        "instr_3": "完成约需 **5 分钟**。",
        "instr_4": "如果您无法判断，或认为两张图片在安全、活跃、乏味等方面差异不明显，请点击 **跳过**。",

        "gender_title": "请选择您的性别：",
        "gender_placeholder": "请选择",
        "gender_options": {
            "Male": "男性",
            "Female": "女性"
        },

        "age_title": "请选择您的年龄组：",
        "age_placeholder": "请选择",
        "age_options": {
            "18-29": "18–29岁",
            "30-44": "30–44岁",
            "45-59": "45–59岁",
            "60+": "60岁及以上"
        },

        "role_title": "请选择您的角色：",
        "role_res": "当地居民",
        "role_tour": "游客",

        "q_pre": "哪条街道看起来更",
        "q_post": "？",
        "btn_back": "⬅️ 返回",
        "btn_skip": "跳过 ⏩",
        "btn_select": "选择上方图片",
        "success": "✅ 数据已同步！",
        "end_title": "问卷已完成",
        "thank_you": "感谢您的参与！",
        "restart": "重新开始"
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

            **7. Anonimato**: Il questionario è anonimo. Vengono raccolte solo informazioni demografiche di base, tra cui genere, fascia d'età e ruolo del partecipante. Non vengono registrati indirizzi IP o dati identificativi.

            **8. Contatti**: Prof.ssa Elisa Conticelli (elisa.conticelli@unibo.it) e Fangyu Chen (fangyu.chen2@unibo.it).
        """,
        "privacy_agree": "Dichiaro di essere maggiorenne, ho letto l'informativa e acconsento.",

        "instr_title": "Istruzioni:",
        "instr_1": "Vi verranno mostrate **30 coppie** di immagini.",
        "instr_2": "Selezionate quella che meglio si adatta alla descrizione.",
        "instr_3": "Richiede circa **5 minuti**.",
        "instr_4": "Se non riuscite a decidere, o se le due immagini sembrano ugualmente sicure, vivaci, noiose, ecc., usate **Salta**.",

        "gender_title": "Seleziona il tuo genere:",
        "gender_placeholder": "Seleziona",
        "gender_options": {
            "Male": "Maschio",
            "Female": "Femmina"
        },

        "age_title": "Seleziona la tua fascia d'età:",
        "age_placeholder": "Seleziona",
        "age_options": {
            "18-29": "18–29",
            "30-44": "30–44",
            "45-59": "45–59",
            "60+": "60 o più"
        },

        "role_title": "Seleziona il tuo ruolo:",
        "role_res": "Residente",
        "role_tour": "Turista",

        "q_pre": "Quale strada sembra più ",
        "q_post": "?",
        "btn_back": "⬅️ Indietro",
        "btn_skip": "Salta ⏩",
        "btn_select": "Seleziona sopra",
        "success": "✅ Dati sincronizzati!",
        "end_title": "Completato",
        "thank_you": "Grazie per il tuo tempo!",
        "restart": "Ricomincia"
    }
}

CAT_TRANS = {
    "English": {
        "Safe": "safe",
        "Lively": "lively",
        "Wealthy": "wealthy",
        "Beautiful": "beautiful",
        "Boring": "boring",
        "Depressing": "depressing"
    },
    "中文": {
        "Safe": "安全",
        "Lively": "活跃",
        "Wealthy": "高档",
        "Beautiful": "美丽",
        "Boring": "乏味",
        "Depressing": "压抑"
    },
    "Italiano": {
        "Safe": "sicura",
        "Lively": "vivace",
        "Wealthy": "benestante",
        "Beautiful": "bella",
        "Boring": "noiosa",
        "Depressing": "deprimente"
    }
}

# --- 4. 核心功能 ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [
                f for f in os.listdir(path)
                if f.lower().endswith(('.jpg', '.jpeg', '.png'))
            ]
            for img in imgs:
                all_data.append((c, img))
    return all_data


# --- 5. 弹窗对话框函数 ---
@st.dialog("Information Sheet / Informativa")
def show_privacy_modal(content):
    st.markdown(content)
    if st.button("Close / Chiudi / 关闭"):
        st.rerun()


# --- 6. 快照式保存函数 ---
def build_current_votes_df(completed=False):
    """
    将当前受访者的有效答案整理成 DataFrame。
    每次保存的是当前 temp_votes 的完整快照。
    """
    current_df = pd.DataFrame(st.session_state.temp_votes)

    if current_df.empty:
        return current_df

    current_df.insert(0, "participant_id", st.session_state.participant_id)
    current_df.insert(1, "response_index", range(1, len(current_df) + 1))

    current_df["gender"] = st.session_state.get("gender", "")
    current_df["age_group"] = st.session_state.get("age_group", "")
    current_df["user_type"] = st.session_state.get("user_type", "")
    current_df["lang"] = st.session_state.get("lang", "")
    current_df["completed"] = completed
    current_df["vote_count"] = len(current_df)
    current_df["last_synced_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return current_df


def sync_current_votes(completed=False):
    """
    覆盖式同步当前受访者的数据。
    逻辑：
    1. 读取 Google Sheet 现有数据；
    2. 删除同一个 participant_id 的旧记录；
    3. 写入当前 temp_votes 的最新快照。
    """
    conn = st.connection("gsheets", type=GSheetsConnection)
    existing_data = conn.read(worksheet="Sheet1", ttl=0)

    if existing_data is None:
        existing_data = pd.DataFrame()

    existing_data = existing_data.copy()

    # 删除当前受访者旧记录，避免返回重选造成重复
    if "participant_id" in existing_data.columns:
        existing_data = existing_data[
            existing_data["participant_id"].astype(str) != str(st.session_state.participant_id)
        ]

    current_df = build_current_votes_df(completed=completed)

    if current_df.empty:
        updated_data = existing_data
    else:
        updated_data = pd.concat([existing_data, current_df], ignore_index=True)

    conn.update(worksheet="Sheet1", data=updated_data)


# --- 7. 状态管理 ---
if 'lang' not in st.session_state:
    st.session_state.lang = "English"

if 'step' not in st.session_state:
    st.session_state.step = "onboarding"

if 'vote_count' not in st.session_state:
    st.session_state.vote_count = 0

if 'temp_votes' not in st.session_state:
    st.session_state.temp_votes = []

if 'participant_id' not in st.session_state:
    st.session_state.participant_id = str(uuid.uuid4())

if 'question_pool' not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool


# --- 8. 逻辑流 ---
if st.session_state.step == "onboarding":
    st.session_state.lang = st.radio(
        "Language",
        ["English", "中文", "Italiano"],
        horizontal=True
    )

    T = LANG_DICT[st.session_state.lang]

    st.title(f"🏙️ {T['title']}")

    st.markdown(
        f"{T['intro']}\n\n"
        f"**{T['instr_title']}**\n"
        f"* {T['instr_1']}\n"
        f"* {T['instr_2']}\n"
        f"* {T['instr_3']}\n"
        f"* {T['instr_4']}"
    )

    st.divider()

    # 弹窗按钮
    if st.button(T['privacy_btn']):
        show_privacy_modal(T['privacy_content'])

    # 同意勾选
    agree = st.checkbox(T['privacy_agree'])

    # 性别
    gender = st.selectbox(
        T["gender_title"],
        options=["", "Male", "Female"],
        format_func=lambda x: T["gender_placeholder"] if x == "" else T["gender_options"][x],
        key="gender_input"
    )

    # 年龄组
    age_group = st.selectbox(
        T["age_title"],
        options=["", "18-29", "30-44", "45-59", "60+"],
        format_func=lambda x: T["age_placeholder"] if x == "" else T["age_options"][x],
        key="age_input"
    )

    basic_info_completed = agree and gender != "" and age_group != ""

    st.subheader(T['role_title'])

    c1, c2 = st.columns(2)

    with c1:
        if st.button(T['role_res'], disabled=not basic_info_completed):
            st.session_state.gender = gender
            st.session_state.age_group = age_group
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"
            st.rerun()

    with c2:
        if st.button(T['role_tour'], disabled=not basic_info_completed):
            st.session_state.gender = gender
            st.session_state.age_group = age_group
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"
            st.rerun()


elif st.session_state.step == "voting":
    # --- 完全保留原始投票页面布局 ---
    T = LANG_DICT[st.session_state.lang]

    all_img_data = load_all_image_data(IMG_DIR, CASES)

    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    st.markdown(
        f'''
        <div class="progress-container">
            <div class="progress-bar" style="width: {percent}%;"></div>
            <div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div>
        </div>
        ''',
        unsafe_allow_html=True
    )

    if 'pair' not in st.session_state:
        pair = random.sample(all_img_data, 2)
        st.session_state.pair = (
            pair[0][0],
            pair[0][1],
            pair[1][0],
            pair[1][1]
        )

    cl, il, cr, ir = st.session_state.pair

    cat_eng = st.session_state.question_pool[st.session_state.vote_count]
    display_cat = CAT_TRANS[st.session_state.lang][cat_eng]

    st.markdown(
        f'<p class="question-text">{T["q_pre"]}<span class="keyword">{display_cat}</span>{T["q_post"]}</p>',
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)

    with col1:
        st.image(os.path.join(IMG_DIR, cl, il), use_container_width=True)

        if st.button(T['btn_select'], key="L"):
            st.session_state.temp_votes.append({
                "left_img": f"{cl}/{il}",
                "right_img": f"{cr}/{ir}",
                "winner": "left",
                "category": cat_eng,
                "case_l": cl,
                "case_r": cr
            })

            st.session_state.vote_count += 1
            del st.session_state.pair

            completed_now = st.session_state.vote_count >= TARGET_VOTES

            try:
                sync_current_votes(completed=completed_now)
            except Exception as e:
                st.session_state["sync_error"] = str(e)

            if completed_now:
                st.session_state.step = "end"

            st.rerun()

    with col2:
        st.image(os.path.join(IMG_DIR, cr, ir), use_container_width=True)

        if st.button(T['btn_select'], key="R"):
            st.session_state.temp_votes.append({
                "left_img": f"{cl}/{il}",
                "right_img": f"{cr}/{ir}",
                "winner": "right",
                "category": cat_eng,
                "case_l": cl,
                "case_r": cr
            })

            st.session_state.vote_count += 1
            del st.session_state.pair

            completed_now = st.session_state.vote_count >= TARGET_VOTES

            try:
                sync_current_votes(completed=completed_now)
            except Exception as e:
                st.session_state["sync_error"] = str(e)

            if completed_now:
                st.session_state.step = "end"

            st.rerun()

    st.write("")

    b1, b2 = st.columns(2)

    with b1:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)

        if st.button(T['btn_back'], disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()

            st.session_state.pair = (
                last["case_l"],
                last["left_img"].split('/')[-1],
                last["case_r"],
                last["right_img"].split('/')[-1]
            )

            st.session_state.vote_count -= 1

            try:
                sync_current_votes(completed=False)
            except Exception as e:
                st.session_state["sync_error"] = str(e)

            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)

        if st.button(T['btn_skip']):
            del st.session_state.pair
            st.rerun()

        st.markdown('</div>', unsafe_allow_html=True)


elif st.session_state.step == "end":
    # --- 结束页 ---
    T = LANG_DICT[st.session_state.lang]

    st.balloons()
    st.title(f"🎉 {T['end_title']}")
    st.subheader(T['thank_you'])
    st.divider()

    final_df = build_current_votes_df(completed=True)

    try:
        sync_current_votes(completed=True)
        st.success(T['success'])

    except Exception as e:
        st.error("Sync Error")
        st.download_button(
            "Download CSV",
            final_df.to_csv(index=False),
            "backup.csv"
        )

    if st.button(T['restart']):
        st.session_state.clear()
        st.rerun()
