import streamlit as st
from streamlit_drawable_canvas import st_canvas
import cv2
import numpy as np
import time
import random

# --- 1. CONFIGURATION & STYLING ---
st.set_page_config(page_title="Bio-Auth Prototype", page_icon="🔐", layout="centered")

st.markdown("""
    <style>
    .stApp { background-color: #f8f9fa; }
    .stButton>button { width: 100%; border-radius: 8px; height: 3em; font-weight: 600; }
    .stProgress > div > div > div > div { background-color: #4CAF50; }
    .instruction-box {
        background-color: #e9ecef;
        padding: 15px;
        border-radius: 10px;
        border-left: 5px solid #0d6efd;
    }
    </style>
""", unsafe_allow_html=True)

# --- 2. SESSION STATE MANAGEMENT ---
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'start_time' not in st.session_state:
    st.session_state.start_time = time.time()
if 'target_direction' not in st.session_state:
    st.session_state.target_direction = random.choice(['Left', 'Right', 'Up', 'Down'])

# --- 3. DIRECTION VERIFICATION LOGIC (FIXED) ---
def verify_direction(canvas_data, target):
    """
    Fixed Logic: Uses Thresholding to ignore the white background
    and detect Black Ink correctly.
    """
    if canvas_data is None:
        return False, "No drawing detected."

    # 1. Convert canvas data to numpy array
    img = np.array(canvas_data).astype('uint8')

    # 2. Convert to Grayscale
    # If image has Alpha channel (RGBA), convert to Gray
    if img.shape[2] == 4:
        gray = cv2.cvtColor(img, cv2.COLOR_RGBA2GRAY)
    else:
        gray = cv2.cvtColor(img, cv2.COLOR_RGB2GRAY)

    # 3. THRESHOLDING (Crucial Fix)
    # The canvas background is White (255) and ink is Black (0).
    # We invert this: Background -> 0 (Black), Ink -> 255 (White).
    # This ensures 'findNonZero' only sees what you DREW, not the background.
    _, thresh = cv2.threshold(gray, 100, 255, cv2.THRESH_BINARY_INV)

    # 4. Find valid pixels (The Ink)
    points = cv2.findNonZero(thresh)
    
    if points is None:
        return False, "Canvas is empty. Draw clearly!"

    # 5. Get Bounding Box of the ink
    x, y, w, h = cv2.boundingRect(points)
    
    # Check if drawing is too tiny (dot)
    if w < 30 or h < 30:
        return False, "Drawing too small. Please draw a bigger arrow."

    # 6. Analyze 'Center of Mass' to find direction
    # We crop to just the drawn arrow area
    roi = thresh[y:y+h, x:x+w]
    
    # Calculate Moments
    M = cv2.moments(roi)
    if M["m00"] == 0: return False, "Could not analyze shape."
    
    # Centroid (Center of gravity of the ink)
    cX = int(M["m10"] / M["m00"])
    cY = int(M["m01"] / M["m00"])
    
    detected_direction = "Unknown"

    # LOGIC: 
    # If Width > Height, it's horizontal (Left/Right).
    # If center of mass is on the Right half, it's pointing Right.
    if w > h:
        if cX > w / 2:
            detected_direction = "Right"
        else:
            detected_direction = "Left"
    # If Height > Width, it's vertical (Up/Down).
    else:
        if cY > h / 2:
            detected_direction = "Down"
        else:
            detected_direction = "Up"

    # --- FINAL VERDICT ---
    if detected_direction == target:
        return True, f"Verified! You drew {detected_direction}."
    else:
        return False, f"Error: You drew {detected_direction}, but we expected {target}."

# --- 4. UI FLOW ---

st.title("🔐 SecureFlow Prototype")
st.progress((st.session_state.step - 1) * 50)

# ---------------- STEP 1: BEHAVIORAL ANALYSIS ----------------
if st.session_state.step == 1:
    st.header("Step 1: Identity & Behavior")
    st.caption("We analyze your typing pattern to verify you are human.")
    
    with st.container():
        col1, col2 = st.columns(2)
        with col1:
            name = st.text_input("Full Name")
            email = st.text_input("Email Address")
        with col2:
            phone = st.text_input("Phone Number")
            if name and email and phone:
                st.info("⚡ Analyzing keystroke dynamics...")

    if st.button("Verify Identity"):
        if name and email and phone:
            # Check typing speed (must take > 2 seconds)
            time_taken = time.time() - st.session_state.start_time
            if time_taken < 2.0:
                st.error("⚠️ Suspicious activity (Too fast). Try again.")
                st.session_state.start_time = time.time()
            else:
                with st.spinner("Verifying..."):
                    time.sleep(1)
                st.success("✅ Behavioral Match Verified.")
                time.sleep(0.5)
                st.session_state.step = 2
                st.rerun()
        else:
            st.warning("Please fill in all details.")

# ---------------- STEP 2: COGNITIVE CHALLENGE ----------------
elif st.session_state.step == 2:
    st.header("Step 2: Directional Security")
    
    target = st.session_state.target_direction
    
    # Define Icons
    icons = {"Right": "➡️", "Left": "⬅️", "Up": "⬆️", "Down": "⬇️"}
    icon = icons.get(target, "")
    
    st.markdown(f"### Draw an Arrow pointing **{target}** {icon}")

    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Canvas Component
        # Use a dynamic key so it refreshes if we change target
        canvas_key = f"canvas_{target}"
        canvas_result = st_canvas(
            fill_color="rgba(255, 165, 0, 0.3)",
            stroke_width=15, # Thick strokes are easier to read
            stroke_color="#000000",
            background_color="#ffffff",
            height=300,
            width=300,
            drawing_mode="freedraw",
            point_display_radius=0,
            key=canvas_key,
        )

    with col2:
        st.markdown(f"""
        <div class="instruction-box">
            <b>Instructions:</b><br>
            Draw a clear arrow pointing <b>{target}</b>.<br>
            Make the head of the arrow heavy/thick.
        </div>
        """, unsafe_allow_html=True)
        
        st.write("") 
        verify_btn = st.button("Unlock Access")

    # --- RESULT HANDLING ---
    if verify_btn:
        if canvas_result.image_data is not None:
            is_match, msg = verify_direction(canvas_result.image_data, target)
            
            if is_match:
                st.balloons()
                st.success(f"🎉 {msg}")
                st.info("SYSTEM UNLOCKED. You may proceed.")
            else:
                st.error(f"❌ {msg}")
                st.warning("Tip: Draw the arrow head clearly so we know which way it points.")

    st.markdown("---")
    if st.button("⬅ Reset Prototype"):
        st.session_state.step = 1
        st.session_state.start_time = time.time()
        st.session_state.target_direction = random.choice(['Left', 'Right', 'Up', 'Down'])
        st.rerun()