import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. 研究配置 ---
IMG_DIR = "images" 
TARGET_VOTES = 30 

# --- 2. 页面全局设置 ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# --- 3. 手机端物理回弹与布局优化 (CSS) ---
st.markdown("""
    <style>
    /* 移除顶部多余空白 */
    .main .block-container { padding-top: 1rem !important; }
    
    /* 核心：限制手机端图片高度，确保两张图+按钮能挤进一屏，解决回弹问题 */
    @media (max-width: 640px) {
        .stImage img {
            max-height: 32vh !important; 
            object-fit: cover;
            border-radius: 8px;
        }
        /* 紧凑型标题和进度条 */
        h3 { font-size: 1rem !important; margin-bottom: 0px !important; }
        .stProgress { margin-bottom: 0px !important; }
        /* 调整按钮高度和间距 */
        .stButton>button {
            height: 3.2em !important;
            margin-top: -5px !important;
            margin-bottom: 10px !important;
        }
    }
    
    /* 通用按钮样式 */
    .stButton>button { 
        width: 100%; 
        border-radius: 8px; 
        font-weight: bold;
    }
    </style>
    """, unsafe_allow_html=True)

# 强制置顶脚本 (JS) 作为物理 CSS 的补充
def scroll_to_top():
    js = """
    <script>
        var body = window.parent.document.querySelector(".main");
        if (body) { body.scrollTo({top: 0, behavior: 'auto'}); }
    </script>
    """
    st.components.v1.html(js, height=0)

# --- 4. 核心工具函数 ---
@st.cache_data
def get_image_list(path):
    if not os.path.exists(path): return []
    valid_formats = ('.jpg', '.jpeg', '.png', '.bmp')
    return [f for f in os.listdir(path) if f.lower().endswith(valid_formats)]

# --- 5. 初始化状态管理 ---
if 'step' not in st.session_state: st.session_state.step = "start"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'user_type' not in st.session_state: st.session_state.user_type = None

# --- 6. 问卷流程 ---

# 第一步：身份识别
if st.session_state.step == "start":
    st.title("🏙️ Urban Perception Study")
    st.markdown("""
    Welcome! This research investigates how historic city centers are perceived.
    Please select your identity to begin the **30-pair** comparison.
    """)
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

# 第二步：核心投票环节
elif st.session_state.step == "voting":
    scroll_to_top() # 刷新即尝试置顶
    
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: No images found in '{IMG_DIR}'. Please check your GitHub repository.")
    else:
        # 显示进度
        st.progress(st.session_state.vote_count / TARGET_VOTES)
        
        # 选题逻辑
        if 'pair' not in st.session_state:
            st.session_state.pair = random.sample(images, 2)
            st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring", "Wealthy", "Depressing"])
        
        l, r = st.session_state.pair
        cat = st.session_state.cat
        st.subheader(f"Which street looks more **{cat.lower()}**?")

        col1, col2 = st.columns(2)
        with col1:
            st.image(os.path.join(IMG_DIR, l), use_container_width=True)
            if st.button("Select Above (A)", key="L"):
                # 记录到内存列表
                st.session_state.temp_votes.append({
                    "left_image": l, "right_image": r, "winner": "left", 
                    "category": cat, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.vote_count += 1
                del st.session_state.pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
                st.rerun()

        with col2:
            st.image(os.path.join(IMG_DIR, r), use_container_width=True)
            if st.button("Select Above (B)", key="R"):
                st.session_state.temp_votes.append({
                    "left_image": l, "right_image": r, "winner": "right", 
                    "category": cat, "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
                st.session_state.vote_count += 1
                del st.session_state.pair
                if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
                st.rerun()

        # 功能区：撤回与跳过
        st.divider()
        bc1, bc2 = st.columns(2)
        with bc1:
            if st.button("⬅️ Back (Undo last)", disabled=(st.session_state.vote_count == 0)):
                last_vote = st.session_state.temp_votes.pop()
                st.session_state.pair = [last_vote["left_image"], last_vote["right_image"]]
                st.session_state.cat = last_vote["category"]
                st.session_state.vote_count -= 1
                st.rerun()
        with bc2:
            if st.button("Skip this pair ⏩"):
                del st.session_state.pair
                st.rerun()

# 第三步：结束与自动保存
elif st.session_state.step == "end":
    st.balloons()
    st.title("Grazie! Session Complete")
    
    # 准备最终数据
    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.user_type
    
    # 尝试同步到 Google Sheets (方案A)
    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        # 读取现有数据追加
        try:
            existing_data = conn.read(worksheet="Sheet1", ttl=0)
            updated_df = pd.concat([existing_data, final_df], ignore_index=True)
        except:
            updated_df = final_df
        
        conn.update(worksheet="Sheet1", data=updated_df)
        st.success("✅ All responses have been successfully synced to Google Sheets.")
    except Exception as e:
        st.error(f"❌ Cloud sync error: {e}")
        # 保底：允许手动下载 CSV
        st.download_button("Download Data Backup (CSV)", final_df.to_csv(index=False), "survey_backup.csv")

    st.write("Thank you for contributing to our PhD research!")
    if st.button("Start New Session"):
        st.session_state.clear()
        st.rerun()
