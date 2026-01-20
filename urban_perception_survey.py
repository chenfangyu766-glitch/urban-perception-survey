import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 配置 ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

st.set_page_config(page_title="Urban Study", layout="centered")

# --- 2. 极致排版 CSS (顶部紧凑化) ---
st.markdown("""
    <style>
    /* 隐藏所有默认多余元素 */
    header {visibility: hidden !important; height: 0px !important;}
    footer {visibility: hidden !important;}
    .main .block-container { 
        padding-top: 0rem !important; 
        margin-top: -3.5rem !important; 
        max-width: 98% !important;
    }

    /* 自定义进度条容器 */
    .progress-container {
        width: 100%;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 5px 0px;
        position: relative;
        height: 18px;
    }
    .progress-bar {
        background-color: #4CAF50;
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s;
    }
    .progress-text {
        position: absolute;
        width: 100%;
        text-align: center;
        top: 0;
        left: 0;
        font-size: 12px;
        line-height: 18px;
        color: #000;
        font-weight: bold;
    }

    /* 问题文字样式 */
    .question-text {
        font-size: 1.3rem !important;
        font-weight: 700;
        text-align: center;
        margin: 5px 0px !important;
    }

    /* 手机端按钮微调 */
    @media (max-width: 640px) {
        .stImage img {
            max-height: 28vh !important; 
            object-fit: cover;
            border-radius: 10px;
        }
        /* 顶部功能按钮 (Back/Skip) 样式 */
        .top-btns button {
            height: 2rem !important;
            font-size: 0.8rem !important;
            background-color: #f8f9fa !important;
            border: 1px solid #ddd !important;
        }
        /* 选择按钮样式 */
        .select-btn button {
            height: 3.2em !important;
            font-weight: bold !important;
            border: 2px solid #000 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 辅助函数 ---
@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    return [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]

# --- 4. 状态初始化 ---
if 'step' not in st.session_state: st.session_state.step = "start"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []

# --- 5. 逻辑控制 ---

if st.session_state.step == "start":
    st.title("🏙️ Urban Perception Study")
    st.write("欢迎参加城市感知研究")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 居民 (Resident)"):
            st.session_state.u = "Resident"; st.session_state.step = "voting"; st.rerun()
    with c2:
        if st.button("📸 游客 (Tourist)"):
            st.session_state.u = "Tourist"; st.session_state.step = "voting"; st.rerun()

elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    # --- A. 顶部功能区 (Back & Skip) ---
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown('<div class="top-btns">', unsafe_allow_html=True)
        if st.button("⬅️ Back", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = [last["l"], last["r"]]; st.session_state.cat = last["c"]
            st.session_state.vote_count -= 1; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with t_col2:
        st.markdown('<div class="top-btns">', unsafe_allow_html=True)
        if st.button("Skip ⏩"):
            del st.session_state.pair; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- B. 带数字的进度条 ---
    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    progress_html = f'''
        <div class="progress-container">
            <div class="progress-bar" style="width: {percent}%;"></div>
            <div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div>
        </div>
    '''
    st.markdown(progress_html, unsafe_allow_html=True)

    # --- C. 核心选题区 ---
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    st.markdown(f'<p class="question-text">Which street looks more <u>{cat.lower()}</u>?</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, l), use_container_width=True)
        st.markdown('<div class="select-btn">', unsafe_allow_html=True)
        if st.button("Select A", key="L"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"left", "c":cat, "t":datetime.now().strftime("%H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with col2:
        st.image(os.path.join(IMG_DIR, r), use_container_width=True)
        st.markdown('<div class="select-btn">', unsafe_allow_html=True)
        if st.button("Select B", key="R"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"right", "c":cat, "t":datetime.now().strftime("%H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == "end":
    # 数据同步到 Google Sheets
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.u
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ 数据已保存至云端表格！")
    except Exception as e:
        st.error(f"同步失败: {e}")
        st.download_button("下载备份 CSV", final_df.to_csv(index=False), "backup.csv")
    
    st.balloons()
    st.subheader("感谢您的参与！")
    if st.button("开始新的一次 (Restart)"): st.session_state.clear(); st.rerun()
