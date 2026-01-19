import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# --- 1. 配置 ---
IMG_DIR = "images"
TARGET_VOTES = 30 

st.set_page_config(page_title="PhD Urban Study", layout="centered")

# --- 2. 物理压缩样式 (解决回弹痛点) ---
st.markdown("""
    <style>
    .main .block-container { padding-top: 0.5rem !important; }
    @media (max-width: 640px) {
        .stImage img {
            max-height: 32vh !important; 
            object-fit: cover;
            border-radius: 8px;
        }
        h3 { font-size: 1rem !important; margin-bottom: 0px !important; }
        .stButton>button { height: 3em !important; margin-top: -5px !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. 工具函数 ---
def save_data(l, r, w, c, u):
    file = f"results_{u.lower()}.csv"
    pd.DataFrame([{"l":l, "r":r, "w":w, "c":c, "t":datetime.now()}]).to_csv(
        file, mode='a', header=not os.path.exists(file), index=False)

# --- 4. 状态初始化 ---
if 'step' not in st.session_state: st.session_state.step = "start"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'history' not in st.session_state: st.session_state.history = [] # 存储历史记录

# --- 5. 逻辑 ---
if st.session_state.step == "start":
    st.title("🏙️ Urban Perception Study")
    if st.button("Resident"): st.session_state.u = "Res"; st.session_state.step = "v"; st.rerun()
    if st.button("Tourist"): st.session_state.u = "Tour"; st.session_state.step = "v"; st.rerun()

elif st.session_state.step == "v":
    # 强制置顶脚本
    st.components.v1.html("<script>window.parent.document.querySelector('.main').scrollTo(0,0);</script>", height=0)
    
    imgs = [f for f in os.listdir(IMG_DIR) if f.lower().endswith(('.jpg', '.png', '.jpeg'))]
    
    # 获取当前题目
    if 'pair' not in st.session_state:
        st.session_state.pair = random.sample(imgs, 2)
        st.session_state.cat = random.choice(["Safe", "Beautiful", "Lively", "Boring"])
    
    l, r = st.session_state.pair
    cat = st.session_state.cat
    
    st.progress(st.session_state.vote_count / TARGET_VOTES)
    st.subheader(f"Which looks more **{cat}**?")

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, l), use_container_width=True)
        if st.button("Select A", key="L"):
            # 存入历史记录以便返回
            st.session_state.history.append({"pair": [l, r], "cat": cat})
            save_data(l, r, "left", cat, st.session_state.u)
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    with col2:
        st.image(os.path.join(IMG_DIR, r), use_container_width=True)
        if st.button("Select B", key="R"):
            st.session_state.history.append({"pair": [l, r], "cat": cat})
            save_data(l, r, "right", cat, st.session_state.u)
            st.session_state.vote_count += 1
            del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    # --- 返回上一题按钮 ---
    st.write("---")
    c1, c2 = st.columns([1, 1])
    with c1:
        if st.button("⬅️ Back (Undo last)", disabled=(st.session_state.vote_count == 0)):
            # 逻辑：弹出最后一条历史，进度减1，重置当前题目
            last_item = st.session_state.history.pop()
            st.session_state.pair = last_item["pair"]
            st.session_state.cat = last_item["cat"]
            st.session_state.vote_count -= 1
            # 注意：实际研究中，由于CSV已经写入，返回上一题会导致CSV里有多余记录
            # 建议在最终数据清洗时删除重复或时间戳过近的数据
            st.rerun()
    with c2:
        if st.button("Skip ⏩"):
            del st.session_state.pair
            st.rerun()

elif st.session_state.step == "end":
    st.success("Session Complete! Thank you for your contribution.")
    if os.path.exists(f"results_{st.session_state.u.lower()}.csv"):
        with open(f"results_{st.session_state.u.lower()}.csv", "rb") as f:
            st.download_button("📥 Download My Data", f, file_name="data.csv")
