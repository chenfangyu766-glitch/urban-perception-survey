import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

# --- 2. PAGE SETTINGS ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# 强制置顶脚本：增强了 JavaScript 的执行强度
def scroll_to_top():
    st.components.v1.html(
        """
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) { 
                body.scrollTo({top: 0, behavior: 'smooth'}); 
            }
        </script>
        """,
        height=0,
    )

# 样式美化
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

def save_vote(left_img, right_img, winner, category, user_type):
    new_row = {
        "left_image": left_img,
        "right_image": right_img,
        "winner": winner,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_type": user_type
    }
    new_df = pd.DataFrame([new_row])

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 读取时禁用缓存，确保获取最新状态
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        except:
            updated_df = new_df
        
        conn.update(worksheet="Sheet1", data=updated_df)
        return True
    except Exception as e:
        # 这里的错误不再是一闪而过，而是会停留在页面上
        st.error(f"❌ Cloud Save Error: {e}")
        # 本地备份
        file_name = f"backup_results_{user_type.lower()}.csv"
        new_df.to_csv(file_name, mode='a', header=not os.path.exists(file_name), index=False)
        return False

# --- 4. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'user_type' not in st.session_state: st.session_state.user_type = None

# --- 5. SURVEY STEPS ---

# STEP 1: Onboarding
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("Select your identity to start. Each session contains **30 pairs**.")
    
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
    # --- 核心改进：在渲染任何内容前强制置顶 ---
    scroll_to_top()
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: No images found in '{IMG_DIR}' folder.")
    else:
        st.progress(min(st.session_state.vote_count / TARGET_VOTES, 1.0))
        st.caption(f"Progress: {st.session_state.vote_count} / {TARGET_VOTES}")

        if 'current_pair' not in st.session_state:
            st.session_state.current_pair = random.sample(images, 2)
            st.session_state.current_cat = random.choice(["Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"])
        
        img_l, img_r = st.session_state.current_pair
        category = st.session_state.current_cat

        st.subheader(f"Which street looks more **{category.lower()}**?")
        
        col_left, col_right = st.columns(2)
        
        with col_left:
            st.markdown("**Image A**")
            st.image(os.path.join(IMG_DIR, img_l), use_container_width=True)
            if st.button("Select Image Above", key="btn_l"):
                # 尝试保存
                success = save_vote(img_l, img_r, "left", category, st.session_state.user_type)
                if success:
                    st.session_state.vote_count += 1
                    del st.session_state.current_pair
                    if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                    st.rerun()

        with col_right:
            st.markdown("**Image B**")
            st.image(os.path.join(IMG_DIR, img_r), use_container_width=True)
            if st.button("Select Image Above", key="btn_r"):
                success = save_vote(img_l, img_r, "right", category, st.session_state.user_type)
                if success:
                    st.session_state.vote_count += 1
                    del st.session_state.current_pair
                    if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "thankyou"
                    st.rerun()

# STEP 3: Thank You
elif st.session_state.step == "thankyou":
    st.balloons()
    st.title("Grazie!")
    st.success("All data synchronized.")
    if st.button("Start Again"):
        st.session_state.clear()
        st.rerun()
