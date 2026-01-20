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

# --- 2. 精致平衡 CSS (兼顾空间与美感) ---
st.markdown("""
    <style>
    /* 1. 顶部处理：保留极小边距，避免死贴边 */
    header {visibility: hidden !important; height: 0px !important;}
    .main .block-container { 
        padding-top: 0.5rem !important; 
        margin-top: -3rem !important; 
        max-width: 95% !important;
    }

    /* 2. 问题文字：大而清晰，且有呼吸感 */
    .question-text {
        font-size: 1.4rem !important;
        font-weight: 700;
        color: #1E1E1E;
        text-align: center;
        margin: 10px 0px 5px 0px !important;
    }

    /* 3. 手机端细节优化 */
    @media (max-width: 640px) {
        /* 图片比例恢复到更自然的程度 */
        .stImage img {
            max-height: 28vh !important; 
            object-fit: cover;
            border-radius: 12px;
            border: 1px solid #EEEEEE; /* 增加精致感边框 */
        }
        
        /* 进度条 */
        .stProgress { margin-top: -10px !important; }

        /* 主选择按钮：增加圆角和间距 */
        [data-testid="column"] .stButton>button {
            height: 3em !important;
            border-radius: 10px !important;
            margin-top: 5px !important;
            background-color: #FFFFFF;
            border: 1.5px solid #000000;
        }

        /* 底部功能键：小巧、灰色、不挤占空间 */
        .footer-buttons button {
            height: 2.2em !important;
            font-size: 0.8rem !important;
            color: #666666 !important;
            border: 1px solid #DDDDDD !important;
            background-color: #F9F9F9 !important;
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
    st.write("Professional Research Interface")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 RESIDENT"):
            st.session_state.u = "Resident"; st.session_state.step = "voting"; st.rerun()
    with c2:
        if st.button("📸 TOURIST"):
            st.session_state.u = "Tourist"; st.session_state.step = "voting"; st.rerun()

elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    st.progress(st.session_state.vote_count / TARGET_VOTES)
    
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    st.markdown(f'<p class="question-text">Which street looks more <u>{cat.lower()}</u>?</p>', unsafe_allow_html=True)

    # 投票区
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

    # 功能区：通过特殊的容器类名来区分样式
    st.write("") # 增加一点点呼吸间距
    f_col1, f_col2 = st.columns(2)
    with f_col1:
        st.markdown('<div class="footer-buttons">', unsafe_allow_html=True)
        if st.button("⬅️ Back", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = [last["l"], last["r"]]; st.session_state.cat = last["c"]
            st.session_state.vote_count -= 1; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with f_col2:
        st.markdown('<div class="footer-buttons">', unsafe_allow_html=True)
        if st.button("Skip ⏩"):
            del st.session_state.pair; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

elif st.session_state.step == "end":
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.u
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Success! Data saved to Google Sheets.")
    except Exception as e:
        st.error("Save error, please download backup.")
        st.download_button("Download CSV", final_df.to_csv(index=False), "backup.csv")
    
    st.balloons()
    if st.button("Restart"): st.session_state.clear(); st.rerun()
