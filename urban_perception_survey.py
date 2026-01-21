import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- 1. RESEARCH CONFIGURATION ---
IMG_DIR = "images" 
TARGET_VOTES = 30 
CASES = ["CaseA", "CaseB", "CaseC", "CaseD"] 

st.set_page_config(
    page_title="Subjective Perception of Historic Centre Street Images", 
    page_icon="🏙️", 
    layout="centered"
)

# --- 2. COMPACT CSS FOR MOBILE OPTIMIZATION ---
st.markdown("""
    <style>
    header {visibility: hidden !important; height: 0px !important;}
    footer {visibility: hidden !important;}
    .main .block-container { 
        padding-top: 0.5rem !important; 
        margin-top: -3.5rem !important; 
        max-width: 98% !important; 
    }
    .progress-container { 
        width: 100%; background-color: #f0f2f6; border-radius: 10px; 
        margin: 5px 0px; position: relative; height: 18px; 
    }
    .progress-bar { background-color: #4CAF50; height: 100%; border-radius: 10px; transition: width 0.3s; }
    .progress-text { position: absolute; width: 100%; text-align: center; top: 0; font-size: 12px; line-height: 18px; font-weight: bold; }
    .question-text { font-size: 1.4rem !important; font-weight: 400; text-align: left !important; margin: 10px 0px !important; color: #1E1E1E; line-height: 1.2; }
    .keyword { font-weight: 700; color: #000; } 
    @media (max-width: 640px) {
        .stImage img { max-height: 28vh !important; object-fit: cover; border-radius: 10px; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) { display: flex !important; flex-direction: row !important; justify-content: flex-start !important; gap: 10px !important; }
        div[data-testid="stHorizontalBlock"]:has(div.bottom-btns) > div { width: auto !important; min-width: 85px !important; flex: none !important; }
        .bottom-btns button { height: 2.2rem !important; font-size: 0.85rem !important; background-color: #f8f9fa !important; color: #666 !important; border: 1px solid #ddd !important; padding: 0 10px !important; }
        .select-btn button { height: 3.2em !important; font-weight: bold !important; border: 2px solid #000 !important; }
    }
    </style>
    """, unsafe_allow_html=True)

# --- 3. HELPER FUNCTIONS ---
@st.cache_data
def load_all_image_data(img_dir, cases):
    all_data = []
    for c in cases:
        path = os.path.join(img_dir, c)
        if os.path.exists(path):
            imgs = [f for f in os.listdir(path) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
            for img in imgs: all_data.append((c, img))
    return all_data

# --- 4. STATE MANAGEMENT ---
if 'step' not in st.session_state: st.session_state.step = "onboarding"
if 'vote_count' not in st.session_state: st.session_state.vote_count = 0
if 'temp_votes' not in st.session_state: st.session_state.temp_votes = []
if 'question_pool' not in st.session_state:
    cats = ["Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"]
    pool = cats * 5
    random.shuffle(pool)
    st.session_state.question_pool = pool

# --- 5. LOGIC FLOW ---

# STEP 1: Introduction & Role Selection
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("""
    Welcome! This research investigates how historic centres are perceived by different people. 
    Your input will help us better understand human-scale urban design.
    
    **Instructions:**
    * You will be shown **30 pairs** of street-view images.
    * Select the one that best fits the description provided.
    * It takes approximately **5 minutes** to complete.
    """)
    st.divider()
    st.subheader("Please identify your role:")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("I am a Resident (Live or work here)"):
            st.session_state.user_type, st.session_state.step = "Resident", "voting"; st.rerun()
    with c2:
        if st.button("I am a Tourist (Visit or travel here)"):
            st.session_state.user_type, st.session_state.step = "Tourist", "voting"; st.rerun()

# STEP 2: Voting Interface
elif st.session_state.step == "voting":
    all_img_data = load_all_image_data(IMG_DIR, CASES)
    
    # Progress Bar
    percent = int((st.session_state.vote_count / TARGET_VOTES) * 100)
    st.markdown(f'''<div class="progress-container"><div class="progress-bar" style="width: {percent}%;"></div><div class="progress-text">{st.session_state.vote_count} / {TARGET_VOTES}</div></div>''', unsafe_allow_html=True)

    # Random Pair Selection (No replacement within the pair)
    if 'pair' not in st.session_state:
        pair = random.sample(all_img_data, 2)
        st.session_state.pair = (pair[0][0], pair[0][1], pair[1][0], pair[1][1])
    
    cl, il, cr, ir = st.session_state.pair
    category = st.session_state.question_pool[st.session_state.vote_count]
    
    st.markdown(f'<p class="question-text">Which street looks more <span class="keyword">{category.lower()}</span>?</p>', unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.image(os.path.join(IMG_DIR, cl, il), use_container_width=True)
        if st.button("Select Above", key="L"):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "left", "category": category, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()
    with col2:
        st.image(os.path.join(IMG_DIR, cr, ir), use_container_width=True)
        if st.button("Select Above", key="R"):
            st.session_state.temp_votes.append({"left_img": f"{cl}/{il}", "right_img": f"{cr}/{ir}", "winner": "right", "category": category, "case_l": cl, "case_r": cr})
            st.session_state.vote_count += 1; del st.session_state.pair
            if st.session_state.vote_count >= TARGET_VOTES: st.session_state.step = "end"
            st.rerun()

    # Functional Buttons
    st.write("")
    b1, b2 = st.columns(2)
    with b1:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)
        if st.button("⬅️ Back", disabled=(st.session_state.vote_count == 0)):
            last = st.session_state.temp_votes.pop()
            st.session_state.pair = (last["case_l"], last["left_img"].split('/')[-1], last["case_r"], last["right_img"].split('/')[-1])
            st.session_state.vote_count -= 1; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)
    with b2:
        st.markdown('<div class="bottom-btns">', unsafe_allow_html=True)
        if st.button("Skip ⏩"): del st.session_state.pair; st.rerun()
        st.markdown('</div>', unsafe_allow_html=True)

# STEP 3: Completion & Data Sync
elif st.session_state.step == "end":
    st.balloons()
    st.title("🎉 Completed")
    st.subheader("Thank you for your time!")
    st.divider()

    final_df = pd.DataFrame(st.session_state.temp_votes)
    final_df["user_type"] = st.session_state.user_type
    final_df["timestamp"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    try:
        conn = st.connection("gsheets", type=GSheetsConnection)
        existing_data = conn.read(worksheet="Sheet1", ttl=0)
        conn.update(worksheet="Sheet1", data=pd.concat([existing_data, final_df], ignore_index=True))
        st.success("✅ Data synced successfully!")
    except:
        st.error("Connection Error. Please download backup.")
        st.download_button("Download CSV Backup", final_df.to_csv(index=False), "survey_data.csv")
    
    if st.button("Restart"): st.session_state.clear(); st.rerun()


