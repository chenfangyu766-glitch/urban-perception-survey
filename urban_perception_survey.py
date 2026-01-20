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

# --- 2. 物理压缩样式 (这是解决你问题的唯一钥匙) ---
st.markdown("""
    <style>
    /* 1. 消除页面所有不必要的边距 */
    .main .block-container { 
        padding-top: 0.5rem !important; 
        padding-bottom: 0rem !important;
        max-width: 95% !important;
    }
    
    /* 2. 手机端强制压缩图片高度 */
    @media (max-width: 640px) {
        .stImage img {
            max-height: 30vh !important; /* 核心：只占屏幕30%高度 */
            object-fit: cover;
            border-radius: 6px;
        }
        /* 标题字体变小，减少占用空间 */
        h3 { 
            font-size: 1rem !important; 
            margin-top: -10px !important;
            margin-bottom: 0px !important; 
        }
        /* 进度条变细 */
        .stProgress { height: 4px !important; }
        /* 按钮紧凑化 */
        .stButton>button {
            height: 2.8em !important;
            margin-top: -5px !important;
            font-size: 0.8rem !important;
        }
        /* 隐藏电脑端的提示字 */
        .desktop-hint { display: none; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 辅助函数 ---
@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

# --- 4. 状态初始化 ---
if 'step' not in st.session_state: st.session_state.step = "start"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []

# --- 5. 逻辑 ---

# STEP 1: 开始
if st.session_state.step == "start":
    st.title("🏙️ Urban Perception")
    st.write("30-pair comparison study.")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 RESIDENT"):
            st.session_state.u = "Resident"; st.session_state.step = "voting"; st.rerun()
    with c2:
        if st.button("📸 TOURIST"):
            st.session_state.u = "Tourist"; st.session_state.step = "voting"; st.rerun()

# STEP 2: 投票 (高度压缩版)
elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    # 顶部紧凑进度条
    st.progress(st.session_state.vote_count / TARGET_VOTES)
    
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    
    # 问题文字（精简）
    st.subheader(f"Which looks more **{cat.lower()}**?")

    # 左右并排布局
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

    # 底端功能按钮（缩小显示）
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

# STEP 3: 结束并保存到 Google Sheets
elif st.session_state.step == "end":
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.u
    
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        except:
            updated_df = final_df
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ Data Synced!")
    except Exception as e:
        st.error(f"Sync error: {e}")
        st.download_button("Download CSV Backup", final_df.to_csv(index=False), "backup.csv")

    st.balloons()
    st.write("Done! Thank you.")
    if st.button("Restart"): st.session_state.clear(); st.rerun()
