import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

# --- 2. PAGE SETTINGS ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# --- 增强型手机端优化样式 ---
st.markdown("""
    <style>
    /* 1. 强制页面主体从顶端开始 */
    .main .block-container { padding-top: 1rem; }
    
    /* 2. 限制移动端图片高度，防止过长 */
    @media (max-width: 640px) {
        img {
            max-height: 45vh !important; 
            object-fit: cover;
            border-radius: 10px;
        }
        .stButton>button {
            height: 4em !important;
            margin-bottom: 20px;
        }
    }
    
    /* 3. 按钮美化 */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold; 
        background-color: #f8f9fa;
        border: 1px solid #ddd;
    }
    .stButton>button:active { border: 2px solid #ff4b4b; }
    </style>
    
    <div id="top_anchor"></div>
    """, unsafe_allow_html=True)

# 强制置顶 JS 脚本
def scroll_to_top():
    js = """
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) { body.scrollTo({top: 0, behavior: 'auto'}); }
        window.location.hash = 'top_anchor';
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

def save_vote_local(left_img, right_img, winner, category, user_type):
    # 既然暂时不连 Google，我们稳健地存入服务器本地 CSV
    new_row = pd.DataFrame([{
        "left_image": left_img,
        "right_image": right_img,
        "winner": winner,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_type": user_type
    }])
    file_name = "collected_data.csv"
    header = not os.path.exists(file_name)
    new_row.to_csv(file_name, mode='a', header=header, index=False)

# --- 4. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'user_type' not in st.session_state: st.session_state.user_type = None

# --- 5. SURVEY STEPS ---

# STEP 1: Onboarding
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("Help us understand the historic city center of Bologna.")
    st.divider()
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 I am a LOCAL RESIDENT"):
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"
            st.rerun()
    with c2:
        if st.button("📸 I am a TOURIST"):
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"
            st.rerun()

# STEP 2: Voting Interface
elif st.session_state.step == "voting":
    # 核心动作：刷新即回顶
    scroll_to_top()
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: No images found in '{IMG_DIR}' folder.")
    else:
        # 进度显示
        st.progress(min(st.session_state.vote_count / TARGET_VOTES, 1.0))
        
        if 'current_pair' not in st.session_state:
            st.session_state.current_pair = random.sample(images, 2)
            st.session_state.current_cat = random.choice(["Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"])
        
        img_l, img_r = st.session_state.current_pair
        category = st.session_state.current_cat

        st.subheader(f"Which street looks more **{category.lower()}**?")
        
        # 布局优化
        col_left, col_right = st.columns(2)
        with col_left:
            st.image(os.path.join(IMG_DIR, img_l), use_container_width=True)
            if st.button("Select Above (A)", key="L"):
                save_vote_local(img_l, img_r, "left", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                st.rerun()

        with col_right:
            st.image(os.path.join(IMG_DIR, img_r), use_container_width=True)
            if st.button("Select Above (B)", key="R"):
                save_vote_local(img_l, img_r, "right", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                st.rerun()

# STEP 3: Thank You & Data Download
elif st.session_state.step == "thankyou":
    st.balloons()
    st.title("Grazie! Thank you!")
    st.success("Research session complete.")
    
    st.divider()
    # 博士生专用下载通道（每天手动备份一次）
    st.subheader("Data Management (Admin Only)")
    if os.path.exists("collected_data.csv"):
        with open("collected_data.csv", "rb") as file:
            st.download_button(
                label="📥 Download All Collected Data",
                data=file,
                file_name=f"survey_backup_{datetime.now().strftime('%m%d')}.csv",
                mime="text/csv"
            )
    
    if st.button("Restart Survey"):
        st.session_state.clear()
        st.rerun()
