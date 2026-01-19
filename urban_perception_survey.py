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

# --- 核心改进：自动置顶脚本与移动端样式优化 ---
st.markdown("""
    <style>
    /* 1. 强制置顶的关键：减少顶部空白 */
    .main .block-container { padding-top: 1rem; }
    
    /* 2. 移动端强制压缩图片高度，确保按钮尽量在第一屏显示 */
    @media (max-width: 640px) {
        img {
            max-height: 38vh !important; /* 图片只占屏幕高度的38% */
            object-fit: cover;
            border-radius: 10px;
        }
        .stButton>button {
            height: 3.5em !important;
            margin-bottom: 20px !important;
        }
        h3 { font-size: 1.2rem !important; }
    }
    
    /* 3. 按钮样式 */
    .stButton>button { width: 100%; border-radius: 8px; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    </style>
    
    <div id="top_marker"></div>
    """, unsafe_allow_html=True)

# 定义置顶函数
def scroll_to_top():
    # 尝试多种 JS 方式确保在不同手机浏览器中都能回跳
    js = """
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) { body.scrollTo({top: 0, behavior: 'auto'}); }
        window.location.hash = 'top_marker';
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 3. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path):
        return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

def save_vote(left_img, right_img, winner, category, user_type):
    file_name = f"results_{user_type.lower()}.csv"
    new_record = pd.DataFrame([{
        "left_image": left_img,
        "right_image": right_img,
        "winner": winner,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }])
    header = not os.path.exists(file_name)
    new_record.to_csv(file_name, mode='a', header=header, index=False)

# --- 4. STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state:
    st.session_state.vote_count = 0
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# --- 5. SURVEY STEPS ---

# STEP 1: Onboarding
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("""
    Welcome! This research investigates how historic city centers are perceived.
    **Instructions:**
    * You will be shown **30 pairs** of street-view images.
    * Select the one that best fits the description.
    """)
    
    st.divider()
    st.subheader("First, please identify yourself:")
    
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

# STEP 2: The Voting Interface
elif st.session_state.step == "voting":
    # --- 关键改动：进入投票环节立刻执行置顶 ---
    scroll_to_top()
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: Images not found in {IMG_DIR}.")
    else:
        # Progress Tracking
        progress = min(st.session_state.vote_count / TARGET_VOTES, 1.0)
        st.progress(progress)
        st.caption(f"Progress: {st.session_state.vote_count} / {TARGET_VOTES} | Role: {st.session_state.user_type}")

        if 'current_pair' not in st.session_state:
            st.session_state.current_pair = random.sample(images, 2)
            st.session_state.current_cat = random.choice([
                "Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"
            ])
        
        img_l, img_r = st.session_state.current_pair
        category = st.session_state.current_cat

        st.subheader(f"Which street looks more **{category.lower()}**?")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Image A**")
            st.image(os.path.join(IMG_DIR, img_l), use_container_width=True)
            if st.button(f"Select Image Above", key="btn_left"):
                save_vote(img_l, img_r, "left", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES:
                    st.session_state.step = "thankyou"
                st.rerun()

        with col_right:
            st.markdown("**Image B**")
            st.image(os.path.join(IMG_DIR, img_r), use_container_width=True)
            if st.button(f"Select Image Above", key="btn_right"):
                save_vote(img_l, img_r, "right", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES:
                    st.session_state.step = "thankyou"
                st.rerun()

        st.divider()
        if st.button("Skip this pair ⏩"):
            del st.session_state.current_pair
            st.rerun()

# STEP 3: Thank You Screen
elif st.session_state.step == "thankyou":
    st.balloons()
    st.title("Grazie! Thank You!")
    st.success(f"Session complete.")
    
    if st.button("Finish and Restart"):
        st.session_state.clear()
        st.rerun()

