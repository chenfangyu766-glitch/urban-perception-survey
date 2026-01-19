import streamlit as st
import pandas as pd
import os
import random
from datetime import datetime

# --- 1. RESEARCH CONFIGURATION ---
# IMPORTANT: Update this path to your local image folder
IMG_DIR = "images"
TARGET_VOTES = 30  # Increased to 30 as per your PhD research requirement

# --- 2. PAGE SETTINGS ---
st.set_page_config(
    page_title="Urban Perception Study | PhD Research",
    page_icon="🏙️",
    layout="centered"
)

# Professional CSS Styling
st.markdown("""
    <style>
    .stButton>button { width: 100%; border-radius: 8px; height: 3.5em; font-weight: bold; }
    .stProgress > div > div > div > div { background-color: #ff4b4b; }
    /* Mobile optimization: ensures images don't look too cramped */
    @media (max-width: 640px) {
        .stImage { margin-bottom: -10px; }
    }
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

# STEP 1: Onboarding & Identity Selection
if st.session_state.step == "onboarding":
    st.title("🏙️ Urban Perception Study")
    st.markdown("""
    Welcome! This research investigates how historic city centers are perceived by different people.
    Your input will help calibrate AI models to better understand human-scale urban design.
    
    **Instructions:**
    * You will be shown **30 pairs** of street-view images.
    * Select the one that best fits the description provided.
    * It takes approximately **5-7 minutes** to complete.
    """)
    
    st.divider()
    st.subheader("First, please identify yourself:")
    
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📍 I am a LOCAL RESIDENT\n(Live or work here)"):
            st.session_state.user_type = "Resident"
            st.session_state.step = "voting"
            st.rerun()
    with c2:
        if st.button("📸 I am a TOURIST\n(Visiting/Traveling)"):
            st.session_state.user_type = "Tourist"
            st.session_state.step = "voting"
            st.rerun()

# STEP 2: The Voting Interface
elif st.session_state.step == "voting":
    images = get_image_list(IMG_DIR)
    
    if len(images) < 2:
        st.error(f"Error: Images not found in {IMG_DIR}. Please check the path.")
    else:
        # Progress Tracking
        progress = min(st.session_state.vote_count / TARGET_VOTES, 1.0)
        st.progress(progress)
        st.caption(f"Progress: {st.session_state.vote_count} / {TARGET_VOTES} | Role: {st.session_state.user_type}")

        # Select Image Pair and Category
        if 'current_pair' not in st.session_state:
            st.session_state.current_pair = random.sample(images, 2)
            st.session_state.current_cat = random.choice([
                "Safe", "Lively", "Wealthy", "Beautiful", "Boring", "Depressing"
            ])
        
        img_l, img_r = st.session_state.current_pair
        category = st.session_state.current_cat

        st.subheader(f"Which street looks more **{category.lower()}**?")
        st.write("---")
        
        # UI Layout: Modified to "Image Above" to support both Desktop and Mobile
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

        st.write("---")
        if st.button("Skip this pair ⏩"):
            del st.session_state.current_pair
            st.rerun()

# STEP 3: Thank You Screen
elif st.session_state.step == "thankyou":
    st.balloons()
    st.title("Grazie! Thank You!")
    st.success(f"Session complete for: **{st.session_state.user_type}**.")
    st.markdown(f"""
    Successfully collected **30 comparisons**. 
    Your data has been saved to `results_{st.session_state.user_type.lower()}.csv`. 
    
    This feedback is essential for training the localized Urban Perception AI model.
    """)
    
    if st.button("Finish and Restart"):
        st.session_state.clear()
        st.rerun()
