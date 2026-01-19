import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# --- 1. 基础配置 ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

st.set_page_config(
    page_title="Urban Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# --- 2. 核心：手机端布局压缩与置顶 CSS ---
st.markdown("""
    <style>
    /* 1. 移除顶部巨大的空白 */
    .main .block-container { padding-top: 1rem; }
    
    /* 2. 手机端适配：压缩图片高度 */
    @media (max-width: 640px) {
        /* 强制图片只占用屏幕高度的 35%，确保两张图都能挤在一屏 */
        img {
            max-height: 35vh !important; 
            object-fit: cover;
            border-radius: 8px;
            margin-bottom: 5px;
        }
        /* 调整按钮高度，使其更容易点击且不占空间 */
        .stButton>button {
            height: 3.5em !important;
            margin-bottom: 15px !important;
        }
        /* 缩小标题字体 */
        h3 { font-size: 1.1rem !important; }
    }
    
    /* 3. 按钮样式增强 */
    .stButton>button { 
        width: 100%; 
        border-radius: 10px; 
        font-weight: bold; 
        border: 1px solid #ddd;
    }
    </style>
    
    <div id="top_marker"></div>
    """, unsafe_allow_html=True)

# 暴力清理脚本：尝试强迫父容器归零
def force_scroll_to_top():
    js = """
    <script>
        var scroll_target = window.parent.document.querySelector('.main');
        if (scroll_target) {
            scroll_target.scrollTo({top: 0, behavior: 'auto'});
        }
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. 工具函数 ---
@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

def save_data(l, r, w, c, u):
    # 保存到服务器本地 CSV
    new_row = pd.DataFrame([{
        "left_image": l, "right_image": r, "winner": w, 
        "category": c, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
        "user_type": u
    }])
    file_name = "survey_results.csv"
    header = not os.path.exists(file_name)
    new_row.to_csv(file_name, mode='a', header=header, index=False)

# --- 4. 问卷流程控制 ---
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0

# STEP 1: 开始页面
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.write("Help us analyze the city center of Bologna.")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 I am a RESIDENT"):
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"
            st.rerun()
    with c2:
        if st.button("📸 I am a TOURIST"):
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"
            st.rerun()

# STEP 2: 投票环节
elif st.session_state.step == "voting":
    # 每次刷新页面执行一次暴力置顶
    force_scroll_to_top()
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error("Error: Images not found.")
    else:
        # 进度条
        st.progress(min(st.session_state.vote_count / TARGET_VOTES, 1.0))
        
        # 随机选择图片对和类别
        if 'current_pair' not in st.session_state:
            st.session_state.current_pair = random.sample(images, 2)
            st.session_state.current_cat = random.choice(["Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"])
        
        l, r = st.session_state.current_pair
        cat = st.session_state.current_cat

        st.subheader(f"Which street looks more **{cat.lower()}**?")
        
        # 左右布局
        col1, col2 = st.columns(2)
        with col1:
            st.image(os.path.join(IMG_DIR, l), use_container_width=True)
            if st.button("Select Above (A)", key="btn_l"):
                save_data(l, r, "left", cat, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                st.rerun()

        with col2:
            st.image(os.path.join(IMG_DIR, r), use_container_width=True)
            if st.button("Select Above (B)", key="btn_r"):
                save_data(l, r, "right", cat, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                st.rerun()

# STEP 3: 结束与下载
elif st.session_state.step == "thankyou":
    st.balloons()
    st.title("Grazie!")
    st.success("Your responses have been recorded.")
    
    # 博士生专用备份按钮
    if os.path.exists("survey_results.csv"):
        with open("survey_results.csv", "rb") as f:
            st.download_button("📥 Download Data Backup", f, file_name="results.csv")
    
    if st.button("Restart"):
        st.session_state.clear()
        st.rerun()
