import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images"  # 确保 GitHub 仓库里有名为 images 的文件夹
TARGET_VOTES = 30 

# --- 2. PAGE SETTINGS ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# 自动置顶脚本：解决手机端点击后页面不回弹
def scroll_to_top():
    st.components.v1.html(
        """
        <script>
            var body = window.parent.document.querySelector(".main");
            if (body) { body.scrollTop = 0; }
        </script>
        """,
        height=0,
    )

# Professional CSS
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path):
        return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

def save_vote(left_img, right_img, winner, category, user_type):
    # 准备这一条新数据
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
        # 建立 Google Sheets 连接
        conn = st.connection("gsheets", type=GSheetsConnection)
        
        try:
            # 读取现有数据 (ttl=0 保证不使用缓存，实时读写)
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            if existing_data.empty:
                updated_df = new_df
            else:
                updated_df = pd.concat([existing_data, new_df], ignore_index=True)
        except:
            # 如果表格完全空白或读取出错，直接使用新数据（会自动创建表头）
            updated_df = new_df
            
        # 核心：执行更新
        conn.update(worksheet="Sheet1", data=updated_df)
        
    except Exception as e:
        # 如果云端失败，在网页显示错误并存入本地备份
        st.error(f"Cloud Save Error: {e}")
        file_name = f"backup_results_{user_type.lower()}.csv"
        header = not os.path.exists(file_name)
        new_df.to_csv(file_name, mode='a', header=header, index=False)

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
    st.subheader("Please identify yourself:")
    
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
    scroll_to_top() # 每一题加载时强制置顶
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: No images found in '{IMG_DIR}' folder.")
    else:
        # Progress Tracking
        progress = min(st.session_state.vote_count / TARGET_VOTES, 1.0)
        st.progress(progress)
        st.caption(f"Progress: {st.session_state.vote_count} / {TARGET_VOTES}")

        # Select Image Pair and Category
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
            if st.button("Select Image Above", key="btn_l"):
                save_vote(img_l, img_r, "left", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES:
                    st.session_state.step = "thankyou"
                st.rerun()

        with col_right:
            st.markdown("**Image B**")
            st.image(os.path.join(IMG_DIR, img_r), use_container_width=True)
            if st.button("Select Image Above", key="btn_r"):
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
    st.success("Your responses have been recorded in the database.")
    
    if st.button("Start New Session"):
        st.session_state.clear()
        st.rerun()

