import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

# --- 2. 极致压缩布局设置 ---
st.set_page_config(
    page_title="Urban Study",
    page_icon="🏙️",
    layout="centered"
)

st.markdown("""
    <style>
    /* 1. 彻底隐藏顶部装饰条、Fork按钮和底部署名 */
    header {visibility: hidden !important; height: 0px !important;}
    footer {visibility: hidden !important;}
    #MainMenu {visibility: hidden !important;}
    
    /* 2. 移除容器内边距，并强制内容向上移动 */
    .main .block-container { 
        padding-top: 0rem !important; 
        padding-bottom: 0rem !important;
        margin-top: -3.5rem !important; /* 核心：强行把内容往最顶端推 */
        max-width: 98% !important;
    }

    /* 3. 手机端极致压缩布局 */
    @media (max-width: 640px) {
        /* 限制图片高度为屏幕的 28%，确保两张图都能出现在一屏 */
        .stImage img {
            max-height: 28vh !important; 
            object-fit: cover;
            border-radius: 8px;
        }
        
        /* 进一步缩小标题、进度条的间距 */
        h3 { 
            font-size: 1rem !important; 
            margin-top: -15px !important;
            margin-bottom: 5px !important; 
        }
        
        .stProgress { margin-top: -10px !important; }
        
        /* 紧凑按钮：减少高度和间距 */
        .stButton>button {
            height: 2.6em !important;
            font-size: 0.85rem !important;
            margin-top: -5px !important;
            margin-bottom: 10px !important;
        }

        /* 移除列之间的多余间隙 */
        [data-testid="column"] {
            padding: 0px 5px !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

# --- 4. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = "start"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'user_type' not in st.session_state: st.session_state.user_type = None

# --- 5. SURVEY STEPS ---

# STEP 1: 开始页面
if st.session_state.step == "start":
    st.title("🏙️ Urban Perception Study")
    st.markdown("Please select your identity to begin.")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 RESIDENT"):
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"
            st.rerun()
    with c2:
        if st.button("📸 TOURIST"):
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"
            st.rerun()

# STEP 2: 核心投票界面 (极致紧凑版)
elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    # 顶部紧凑进度条
    st.progress(st.session_state.vote_count / TARGET_VOTES)
    
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    
    st.subheader(f"Which looks more **{cat.lower()}**?")

    # 左右排列布局
    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, l), use_container_width=True)
        if st.button("Select A", key="L"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"left", "c":cat, "t":datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    with col2:
        st.image(os.path.join(IMG_DIR, r), use_container_width=True)
        if st.button("Select B", key="R"):
            st.session_state.temp_votes.append({"l":l, "r":r, "w":"right", "c":cat, "t":datetime.now().strftime("%Y-%m-%d %H:%M")})
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    # 底端功能按钮（极小化）
    st.write("---")
    bc1, bc2 = st.columns(2)
    with bc1:
        if st.button("⬅️ Undo", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = [last["l"], last["r"]]; st.session_state.cat = last["c"]
            st.session_state.vote_count -= 1; st.rerun()
    with bc2:
        if st.button("Skip ⏩"):
            del st.session_state.pair; st.rerun()

# STEP 3: 结束并正式同步到 Google Sheets
elif st.session_state.step == "end":
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.user_type
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        except:
            updated_df = final_df
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ Data Synced to Google Sheets!")
    except Exception as e:
        st.error(f"Sync error: {e}")
        st.download_button("Download Backup CSV", final_df.to_csv(index=False), "backup.csv")

    st.balloons()
    st.write("PhD Research Session Complete. Thank you!")
    if st.button("Restart"): st.session_state.clear(); st.rerun()
