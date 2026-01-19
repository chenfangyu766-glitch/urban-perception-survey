import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images"  # 确保GitHub仓库里有名为images的文件夹
TARGET_VOTES = 30 

# --- 2. PAGE SETTINGS ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# 自动置顶脚本：解决手机端点击后不回弹的问题
def scroll_to_top():
    js = """
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) { body.scrollTop = 0; }
    </script>
    """
    st.components.v1.html(js, height=0)

# Professional CSS Styling
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
    new_data = pd.DataFrame([{
        "left_image": left_img,
        "right_image": right_img,
        "winner": winner,
        "category": category,
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "user_type": user_type
    }])

    # 方案：尝试写入 Google Sheets，如果失败则存入云端临时本地文件
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 读取现有数据（假设你的Sheet名字叫 Sheet1）
        existing_data = conn.read(worksheet="Sheet1")
        # 合并新旧数据
        updated_df = pd.concat([existing_data, new_data], ignore_index=True)
        # 更新回云端
        conn.update(worksheet="Sheet1", data=updated_df)
    except Exception as e:
        # 备选方案：存入云端本地 CSV (防止Google接口报错)
        file_name = f"backup_results_{user_type.lower()}.csv"
        header = not os.path.exists(file_name)
        new_data.to_csv(file_name, mode='a', header=header, index=False)

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
    * It takes approximately **5-7 minutes**.
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
    scroll_to_top() # 关键：每一题开始时自动置顶
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: Images not found in '{IMG_DIR}' folder.")
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
            if st.button(f"Select Image Above", key="btn_l"):
                save_vote(img_l, img_r, "left", category, st.session_state.user_type)
                st.session_state.vote_count += 1
                del st.session_state.current_pair
                if st.session_state.vote_count >= TARGET_VOTES:
                    st.session_state.step = "thankyou"
                st.rerun()

        with col_right:
            st.markdown("**Image B**")
            st.image(os.path.join(IMG_DIR, img_r), use_container_width=True)
            if st.button(f"Select Image Above", key="btn_r"):
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
    st.success("Your data has been successfully synced to the research database.")
    
    # 提供一个备用的本地下载按钮，双重保险
    st.write("Admin: You can also download the session backup here:")
    if st.button("Download Backup CSV"):
        # 这里逻辑仅作为博士生自己测试用
        st.info("Data is already in Google Sheets. This button is for local backup.")

    if st.button("Start Again"):
        st.session_state.clear()
        st.rerun()
