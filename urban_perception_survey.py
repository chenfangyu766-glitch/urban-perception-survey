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

# --- 3. 极致紧凑布局 CSS ---
st.markdown("""
    <style>
    /* 彻底隐藏顶部装饰条和页脚 */
    header {visibility: hidden !important; height: 0px !important;}
    footer {visibility: hidden !important;}
    
    /* 极致压缩容器边距，整体大幅向上提升 */
    .main .block-container { 
        padding-top: 0rem !important; 
        margin-top: -3.8rem !important; 
        max-width: 98% !important;
    }

    /* 带数字的自定义进度条 */
    .progress-container {
        width: 100%;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin: 5px 0px;
        position: relative;
        height: 18px;
    }
    .progress-bar {
        background-color: #4CAF50;
        height: 100%;
        border-radius: 10px;
        transition: width 0.3s;
    }
    .progress-text {
        position: absolute;
        width: 100%;
        text-align: center;
        top: 0;
        left: 0;
        font-size: 12px;
        line-height: 18px;
        color: #000;
        font-weight: bold;
    }

    /* 问题文字放大样式 */
    .question-text {
        font-size: 1.3rem !important;
        font-weight: 700;
        text-align: center;
        margin: 5px 0px !important;
        color: #31333F;
    }

    /* 手机端适配：压缩图片，调整按钮 */
    @media (max-width: 640px) {
        .stImage img {
            max-height: 28vh !important; 
            object-fit: cover;
            border-radius: 10px;
        }
        .top-btns button {
            height: 2rem !important;
            font-size: 0.8rem !important;
            background-color: #f8f9fa !important;
        }
        .select-btn button {
            height: 3.2em !important;
            font-weight: bold !important;
            border: 2px solid #000 !important;
        }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 4. CORE UTILITIES ---

@st.cache_data
def get_image_list(path):
    if not os.path.exists(path):
        return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

# --- 5. STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state:
    st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state:
    st.session_state.temp_votes = []
if 'user_type' not in st.session_state:
    st.session_state.user_type = None

# --- 6. SURVEY STEPS ---

# STEP 1: Onboarding
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("Select your identity to begin the comparison.")
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

# STEP 2: Voting Interface
elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    # --- A. 顶部功能区 (Back & Skip) ---
    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown('<div class="top-btns">', unsafe_allow_html=True)
        # 撤回逻辑：弹出内存最后一条记录
        if st.button("⬅️ Back", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = [last["left_image"], last["right_image"]]
            st.session_state.cat = last["category"]
            st.session_state.vote_count -= 1
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with t_col2:
        st.markdown('<div class="top-btns">', unsafe_allow_html=True)
        if st.button("Skip ⏩"):
            if 'pair' in st.session_state: del st.session_state.pair
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    # --- B. 带数字的自定义进度条 ---
    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    st.markdown(f'''
        <div class="progress-container">
            <div class="progress-bar" style="width: {percent}%;"></div>
            <div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div>
        </div>
    ''', unsafe_allow_html=True)

    # 题目逻辑
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(images, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    
    # --- C. 放大问题文字 ---
    st.markdown(f'<p class="question-text">Which street looks more <u>{cat.lower()}</u>?</p>', unsafe_allow_html=True)

    # --- D. 核心选择区 ---
    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, l), use_container_width=True)
        st.markdown('<div class="select-btn">', unsafe_allow_html=True)
        if st.button("Select Above", key="btn_l"):
            st.session_state.temp_votes.append({
                "left_image": l, "right_image": r, "winner": "left", 
                "category": cat, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

    with col2:
        st.image(os.path.join(IMG_DIR, r), use_container_width=True)
        st.markdown('<div class="select-btn">', unsafe_allow_html=True)
        if st.button("Select Above", key="btn_r"):
            st.session_state.temp_votes.append({
                "left_image": l, "right_image": r, "winner": "right", 
                "category": cat, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            })
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# STEP 3: Thank You & Once-off Sync
elif st.session_state.step == "end":
    st.balloons()
    st.title("✅ Session Complete")
    
    # 将暂存的 30 条数据整合
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.user_type
    
    # 一次性执行保存逻辑
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        except:
            updated_df = final_df
        
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("Data successfully synced to Google Sheets!")
    except Exception as e:
        st.error(f"Sync failed: {e}")
        st.download_button("Download Data Backup (CSV)", final_df.to_csv(index=False), "backup.csv")

    st.write("Thank you for your PhD research contribution.")
    if st.button("Start New Session"):
        # 彻底清理状态
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()
