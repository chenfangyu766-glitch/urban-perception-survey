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

# --- 2. 极致排版 CSS (解决间距、字号和位移问题) ---
st.markdown("""
    <style>
    /* 1. 移除 Streamlit 头部和边距 */
    header {visibility: hidden !important; height: 0px !important;}
    .main .block-container { 
        padding-top: 0rem !important; 
        margin-top: -3.8rem !important; /* 整体大幅向上提 */
        padding-left: 0.5rem !important;
        padding-right: 0.5rem !important;
    }

    /* 2. 核心问题文字 (Which looks more...) 样式优化 */
    .question-text {
        font-size: 1.3rem !important; /* 放大字体 */
        font-weight: bold;
        color: #31333F;
        text-align: center;
        margin-bottom: -10px !important; /* 消除下方空白 */
        margin-top: 5px !important;
    }

    /* 3. 手机端极致压缩布局 */
    @media (max-width: 640px) {
        /* 图片高度继续收缩，腾出空间给下方按钮 */
        .stImage img {
            max-height: 26vh !important; 
            object-fit: cover;
            border-radius: 8px;
        }
        
        /* 进度条压缩 */
        .stProgress { margin-top: -5px !important; margin-bottom: -15px !important; }

        /* 统一所有按钮高度，减少间距 */
        .stButton>button {
            height: 2.4em !important;
            padding: 0px !important;
            margin-top: -10px !important;
            margin-bottom: 2px !important;
        }
        
        /* 专门针对 Back 和 Skip 的行间距优化 */
        [data-testid="stHorizontalBlock"] {
            gap: 0.2rem !important;
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

# --- 5. 问卷流程 ---

if st.session_state.step == "start":
    st.title("🏙️ Urban Perception")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 RESIDENT"):
            st.session_state.u = "Resident"; st.session_state.step = "voting"; st.rerun()
    with c2:
        if st.button("📸 TOURIST"):
            st.session_state.u = "Tourist"; st.session_state.step = "voting"; st.rerun()

elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    # 顶部极简进度条
    st.progress(st.session_state.vote_count / TARGET_VOTES)
    
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    
    # 使用自定义 HTML 放大问题文字
    st.markdown(f'<p class="question-text">Which looks more <u>{cat.lower()}</u>?</p>', unsafe_allow_html=True)

    # 1. 核心投票按钮区
    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, l), use_container_width=True)
        if st.button("Select A", key="L"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"left", "c":cat, "t":datetime.now().strftime("%H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
    with col2:
        st.image(os.path.join(IMG_DIR, r), use_container_width=True)
        if st.button("Select B", key="R"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"right", "c":cat, "t":datetime.now().strftime("%H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    # 2. 功能辅助区 (Back 和 Skip 紧跟在下方)
    # 我们不再使用 st.write("---") 因为分割线占空间
    aux1, aux2 = st.columns(2)
    with aux1:
        if st.button("⬅️ Back", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = [last["l"], last["r"]]; st.session_state.cat = last["c"]
            st.session_state.vote_count -= 1; st.rerun()
    with aux2:
        if st.button("Skip ⏩"):
            del st.session_state.pair; st.rerun()

elif st.session_state.step == "end":
    # 自动保存逻辑同步
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.u
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Data Saved!")
    except Exception as e:
        st.error(f"Sync failed: {e}")
        st.download_button("Download CSV", final_df.to_csv(index=False), "backup.csv")
    
    st.balloons()
    st.write("Thanks for your time!")
    if st.button("Restart"): st.session_state.clear(); st.rerun()
