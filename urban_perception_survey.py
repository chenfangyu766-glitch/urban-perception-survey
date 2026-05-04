import streamlit as st
import pandas as pd
import os
import random
import uuid
import gspread
from datetime import datetime
from google.oauth2.service_account import Credentials

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images"
TARGET_VOTES = 30
CASES = ["CaseA", "CaseB", "CaseC", "CaseD"]
EVENT_WORKSHEET_NAME = "Events"

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
        "instr_4": "If the two images look equally suitable, please use **Skip**.",

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
        "instr_4": "如果两张图片看起来差不多，请点击 **跳过**。",

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
        "instr_4": "Se le due immagini sembrano ugualmente adatte, usate **Salta**.",

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

# --- 4. Google Sheet event log columns ---
EVENT_COLUMNS = [
    "event_id",
    "participant_id",
    "event_seq",
    "event_type",
    "timestamp",
    "lang",
    "gender",
    "age_group",
    "user_type",
    "question_number",
    "response_index",
    "vote_count",
    "skip_count",
    "completed",
    "category",
    "left_img",
    "right_img",
    "winner",
    "case_l",
    "case_r",
    "removed_response_index",
    "removed_category",
    "removed_left_img",
    "removed_right_img",
    "removed_winner",
    "removed_case_l",
    "removed_case_r"
]

# --- 5. 核心功能 ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [
                f for f in os.listdir(path)
                if f.lower().endswith((".jpg", ".jpeg", ".png"))
            ]
            for img in imgs:
                all_data.append((c, img))
    return all_data


def image_key(item):
    return f"{item[0]}/{item[1]}"


def get_new_pair(all_img_data):
    """
    尽量避免同一个受访者重复看到同一张图片。
    如果未使用图片不足 2 张，则自动回退到全图库随机抽取。
    """
    used = set(st.session_state.used_images)

    candidates = [
        item for item in all_img_data
        if image_key(item) not in used
    ]

    if len(candidates) >= 2:
        pair = random.sample(candidates, 2)
    else:
        pair = random.sample(all_img_data, 2)

    st.session_state.used_images.extend([
        image_key(pair[0]),
        image_key(pair[1])
    ])

    return pair


# --- 6. 弹窗对话框函数 ---
@st.dialog("Information Sheet / Informativa")
def show_privacy_modal(content):
    st.markdown(content)
    if st.button("Close / Chiudi / 关闭"):
        st.rerun()


# --- 7. Google Sheets append-only event log ---
@st.cache_resource
def get_events_worksheet():
    """
    使用 Google Sheets API 的 append_rows。
    这比每次读取整个 Sheet 再 update 更适合多人同时填写。
    """
    config = dict(st.secrets["connections"]["gsheets"])

    spreadsheet_value = (
        config.get("spreadsheet")
        or config.get("spreadsheet_url")
        or config.get("url")
    )

    credential_keys = [
        "type",
        "project_id",
        "private_key_id",
        "private_key",
        "client_email",
        "client_id",
        "auth_uri",
        "token_uri",
        "auth_provider_x509_cert_url",
        "client_x509_cert_url",
        "universe_domain"
    ]

    creds_info = {
        k: config[k]
        for k in credential_keys
        if k in config
    }

    if "private_key" in creds_info:
        creds_info["private_key"] = creds_info["private_key"].replace("\\n", "\n")

    scopes = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]

    credentials = Credentials.from_service_account_info(
        creds_info,
        scopes=scopes
    )

    client = gspread.authorize(credentials)

    if spreadsheet_value.startswith("http"):
        spreadsheet = client.open_by_url(spreadsheet_value)
    else:
        try:
            spreadsheet = client.open_by_key(spreadsheet_value)
        except Exception:
            spreadsheet = client.open(spreadsheet_value)

    try:
        worksheet = spreadsheet.worksheet(EVENT_WORKSHEET_NAME)
    except gspread.WorksheetNotFound:
        worksheet = spreadsheet.add_worksheet(
            title=EVENT_WORKSHEET_NAME,
            rows=1000,
            cols=len(EVENT_COLUMNS)
        )
        worksheet.append_row(EVENT_COLUMNS)

    header = worksheet.row_values(1)
    if not header:
        worksheet.append_row(EVENT_COLUMNS)

    return worksheet


def make_event(
    event_type,
    category="",
    left_img="",
    right_img="",
    winner="",
    case_l="",
    case_r="",
    response_index="",
    question_number="",
    completed=False,
    removed_vote=None
):
    """
    生成一条事件记录。
    event_type 可以是：
    start / vote / skip / back
    """
    st.session_state.event_seq += 1

    event = {
        "event_id": str(uuid.uuid4()),
        "participant_id": st.session_state.participant_id,
        "event_seq": st.session_state.event_seq,
        "event_type": event_type,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "lang": st.session_state.get("lang", ""),
        "gender": st.session_state.get("gender", ""),
        "age_group": st.session_state.get("age_group", ""),
        "user_type": st.session_state.get("user_type", ""),
        "question_number": question_number,
        "response_index": response_index,
        "vote_count": st.session_state.get("vote_count", 0),
        "skip_count": st.session_state.get("skip_count", 0),
        "completed": completed,
        "category": category,
        "left_img": left_img,
        "right_img": right_img,
        "winner": winner,
        "case_l": case_l,
        "case_r": case_r,
        "removed_response_index": "",
        "removed_category": "",
        "removed_left_img": "",
        "removed_right_img": "",
        "removed_winner": "",
        "removed_case_l": "",
        "removed_case_r": ""
    }

    if removed_vote is not None:
        event["removed_response_index"] = removed_vote.get("response_index", "")
        event["removed_category"] = removed_vote.get("category", "")
        event["removed_left_img"] = removed_vote.get("left_img", "")
        event["removed_right_img"] = removed_vote.get("right_img", "")
        event["removed_winner"] = removed_vote.get("winner", "")
        event["removed_case_l"] = removed_vote.get("case_l", "")
        event["removed_case_r"] = removed_vote.get("case_r", "")

    return event


def append_events(events):
    """
    append-only 写入 Google Sheet。
    使用 RAW，避免 Google Sheet 自动转换时间或数字格式。
    """
    if not events:
        return

    worksheet = get_events_worksheet()
    rows = [
        [event.get(col, "") for col in EVENT_COLUMNS]
        for event in events
    ]

    worksheet.append_rows(rows, value_input_option="RAW")


def safe_log_event(event):
    """
    如果网络或 Google Sheet 临时失败，先把事件留在 session_state.pending_events。
    下一次操作时会再次尝试同步。
    """
    st.session_state.pending_events.append(event)

    try:
        append_events(st.session_state.pending_events)
        st.session_state.pending_events = []
        st.session_state.sync_error = ""
    except Exception as e:
        st.session_state.sync_error = str(e)


def build_backup_votes_df():
    """
    用于同步失败时让受访者下载当前答案备份。
    """
    df = pd.DataFrame(st.session_state.temp_votes)

    if df.empty:
        return df

    df.insert(0, "participant_id", st.session_state.participant_id)
    df["gender"] = st.session_state.get("gender", "")
    df["age_group"] = st.session_state.get("age_group", "")
    df["user_type"] = st.session_state.get("user_type", "")
    df["lang"] = st.session_state.get("lang", "")
    df["vote_count"] = st.session_state.get("vote_count", 0)
    df["skip_count"] = st.session_state.get("skip_count", 0)
    df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    return df


def record_vote(winner, cl, il, cr, ir, cat_eng):
    response_index = st.session_state.vote_count + 1

    vote = {
        "response_index": response_index,
        "left_img": f"{cl}/{il}",
        "right_img": f"{cr}/{ir}",
        "winner": winner,
        "category": cat_eng,
        "case_l": cl,
        "case_r": cr
    }

    st.session_state.temp_votes.append(vote)
    st.session_state.vote_count += 1

    completed_now = st.session_state.vote_count >= TARGET_VOTES

    event = make_event(
        event_type="vote",
        category=cat_eng,
        left_img=f"{cl}/{il}",
        right_img=f"{cr}/{ir}",
        winner=winner,
        case_l=cl,
        case_r=cr,
        response_index=response_index,
        question_number=response_index,
        completed=completed_now
    )

    safe_log_event(event)

    if "pair" in st.session_state:
        del st.session_state.pair

    if completed_now:
        st.session_state.step = "end"


# --- 8. 状态管理 ---
if "lang" not in st.session_state:
    st.session_state.lang = "English"

if "step" not in st.session_state:
    st.session_state.step = "onboarding"

if "vote_count" not in st.session_state:
    st.session_state.vote_count = 0

if "skip_count" not in st.session_state:
    st.session_state.skip_count = 0

if "temp_votes" not in st.session_state:
    st.session_state.temp_votes = []

if "pending_events" not in st.session_state:
    st.session_state.pending_events = []

if "sync_error" not in st.session_state:
    st.session_state.sync_error = ""

if "participant_id" not in st.session_state:
    st.session_state.participant_id = str(uuid.uuid4())

if "event_seq" not in st.session_state:
    st.session_state.event_seq = 0

if "used_images" not in st.session_state:
    st.session_state.used_images = []

if "question_pool" not in st.session_state:
    cats = list(CAT_TRANS["English"].keys())
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool


# --- 9. 逻辑流 ---
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
    if st.button(T["privacy_btn"]):
        show_privacy_modal(T["privacy_content"])

    # 同意勾选
    agree = st.checkbox(T["privacy_agree"])

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

    st.subheader(T["role_title"])

    c1, c2 = st.columns(2)

    with c1:
        if st.button(T["role_res"], disabled=not basic_info_completed):
            st.session_state.gender = gender
            st.session_state.age_group = age_group
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"

            start_event = make_event(event_type="start")
            safe_log_event(start_event)

            st.rerun()

    with c2:
        if st.button(T["role_tour"], disabled=not basic_info_completed):
            st.session_state.gender = gender
            st.session_state.age_group = age_group
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"

            start_event = make_event(event_type="start")
            safe_log_event(start_event)

            st.rerun()


elif st.session_state.step == "voting":
    T = LANG_DICT[st.session_state.lang]

    all_img_data = load_all_image_data(IMG_DIR, CASES)

    if len(all_img_data) < 2:
        st.error("Not enough images found. Please check the images folder.")
        st.stop()

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

    if "pair" not in st.session_state:
        pair = get_new_pair(all_img_data)
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

        if st.button(T["btn_select"], key="L"):
            record_vote(
                winner="left",
                cl=cl,
                il=il,
                cr=cr,
                ir=ir,
                cat_eng=cat_eng
            )
            st.rerun()

    with col2:
        st.image(os.path.join(IMG_DIR, cr, ir), use_container_width=True)

        if st.button(T["btn_select"], key="R"):
            record_vote(
                winner="right",
                cl=cl,
                il=il,
                cr=cr,
                ir=ir,
                cat_eng=cat_eng
            )
            st.rerun()

    st.write("")

    b1, b2 = st.columns(2)

    with b1:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)

        if st.button(T["btn_back"], disabled=(st.session_state.vote_count == 0)):
            removed_vote = st.session_state.temp_votes.pop()

            st.session_state.pair = (
                removed_vote["case_l"],
                removed_vote["left_img"].split("/")[-1],
                removed_vote["case_r"],
                removed_vote["right_img"].split("/")[-1]
            )

            st.session_state.vote_count -= 1

            back_event = make_event(
                event_type="back",
                question_number=st.session_state.vote_count + 1,
                completed=False,
                removed_vote=removed_vote
            )
            safe_log_event(back_event)

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    with b2:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)

        if st.button(T["btn_skip"]):
            st.session_state.skip_count += 1

            skip_event = make_event(
                event_type="skip",
                category=cat_eng,
                left_img=f"{cl}/{il}",
                right_img=f"{cr}/{ir}",
                winner="",
                case_l=cl,
                case_r=cr,
                question_number=st.session_state.vote_count + 1,
                completed=False
            )
            safe_log_event(skip_event)

            if "pair" in st.session_state:
                del st.session_state.pair

            st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)


elif st.session_state.step == "end":
    T = LANG_DICT[st.session_state.lang]

    st.balloons()
    st.title(f"🎉 {T['end_title']}")
    st.subheader(T["thank_you"])
    st.divider()

    # 尝试把之前未同步的 pending events 再同步一次
    if st.session_state.pending_events:
        try:
            append_events(st.session_state.pending_events)
            st.session_state.pending_events = []
            st.session_state.sync_error = ""
        except Exception as e:
            st.session_state.sync_error = str(e)

    if not st.session_state.pending_events:
        st.success(T["success"])
    else:
        st.error("Sync Error")
        backup_df = build_backup_votes_df()
        st.download_button(
            "Download CSV",
            backup_df.to_csv(index=False),
            "backup.csv"
        )
        st.warning("Please download the CSV backup before closing this page.")

    # 如果还有未同步事件，则禁用 Restart，避免误清空数据
    if st.button(T["restart"], disabled=bool(st.session_state.pending_events)):
        st.session_state.clear()
        st.rerun()
