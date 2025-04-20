import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from backend.database import Database
from backend.chat_engine import run_query
from backend.auth import Auth  # Add this import
from streamlit_chat import message  # Add this import

# Page config
st.set_page_config(
    page_title="Homeopathy ChatBot",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize database and auth
db = Database()
auth = Auth(db)

# Initialize session state for authentication
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False
    st.session_state.doctor_email = None

# Main title
st.title("💬 Homeo Assist AI")

# Sidebar with authentication and patient management
with st.sidebar:
    if not st.session_state.authenticated:
        st.header("👨‍⚕️ Doctor Access")
        tab1, tab2 = st.tabs(["Login", "Register"])
        
        with tab1:
            doctor_email = st.text_input("Email", key="login_email")
            if doctor_email:
                doctor = db.get_doctor(doctor_email)
                if not doctor:
                    st.error("Doctor not found. Please register first.")
                elif not doctor[4]:  # is_verified check
                    otp = st.text_input("Enter OTP")
                    if st.button("Verify OTP"):
                        if auth.verify_otp(doctor_email, otp):
                            st.session_state.authenticated = True
                            st.session_state.doctor_email = doctor_email
                            st.success("Account verified successfully!")
                            st.rerun()
                        else:
                            st.error("Invalid OTP")
                else:
                    st.session_state.authenticated = True
                    st.session_state.doctor_email = doctor_email
                    st.success("Logged in successfully!")
                    st.rerun()
        
        with tab2:
            with st.form("registration_form"):
                name = st.text_input("Full Name")
                email = st.text_input("Email")
                mobile = st.text_input("Mobile")
                reg_number = st.text_input("Registration Number")
                
                submit_registration = st.form_submit_button("Register")
                if submit_registration:
                    if not (name and email and mobile and reg_number):
                        st.error("All fields are required")
                    else:
                        try:
                            otp = auth.register_doctor(email, name, mobile, reg_number)
                            st.success("Registration successful! Check your email/console for OTP")
                            st.info(f"Your OTP: {otp}")  # For testing only
                        except Exception as e:
                            st.error(f"Registration failed: {str(e)}")
    
    else:
        # Show logged-in doctor's email and logout button
        st.header("👨‍⚕️ Doctor Dashboard")
        st.info(f"Logged in as: {st.session_state.doctor_email}")
        if st.button("Logout"):
            st.session_state.authenticated = False
            st.session_state.doctor_email = None
            st.rerun()
        
        # Patient Management
        st.header("👤 Patient Management")
        patients = db.get_patients(st.session_state.doctor_email)
        selected_patient = st.selectbox("Select Patient", patients if patients else ["No patients"])
        new_patient = st.text_input("Add New Patient")
        
        if st.button("Add Patient") and new_patient:
            db.add_patient(st.session_state.doctor_email, new_patient)
            st.success(f"Added patient: {new_patient}")
            st.rerun()

# Chat interface
# Add this near the top of the file, after the page config
# Remove the first title at the top
# Remove the default Streamlit title here
# st.title("💬 Homeo Assist AI")

# Improved CSS for sticky header and chat input
st.markdown("""
    <style>
        .main-header {
            background-color: #111;
            position: fixed;
            top: 0;
            margin-left: 0; /* use margin-left for flexibility */
            width: 100vw; /* full width to allow flexibility */
            padding: 2.5rem 1rem 1rem 1rem; /* added left padding for spacing */
            z-index: 1000;
            border-bottom: 1px solid #222;
            text-align: left; /* align text to the left */
            color: #fff;
            transition: margin-left 0.3s ease; /* smooth transition for sidebar toggle */
        }
        .chat-area {
            margin-top: 160px;
            height: calc(100vh - 260px);
            overflow-y: auto;
            padding: 1rem 0.5rem 0.5rem 0.5rem;
        }
        .chat-input {
            background-color: #111;
            position: fixed;
            bottom: 0;
            margin-left: 0; /* use margin-left for flexibility */
            width: 100vw; /* full width to allow flexibility */
            padding: 1rem 0.5rem;
            z-index: 1000;
            border-top: 1px solid #f0f0f0;
            transition: margin-left 0.3s ease; /* smooth transition for sidebar toggle */
        }
        .block-container {
            padding-top: 40px !important;
        }
    </style>
""", unsafe_allow_html=True)

# Remove or comment out the custom CSS and chat-area/chat-input divs
# (since streamlit-chat handles the UI)

# Main content area
if st.session_state.authenticated and (selected_patient != "No patients" or new_patient):
    st.markdown(
        f'''
        <div class="main-header">
            <h1 style="margin-bottom:0.2em; color:#fff;">💬 Homeo Assist AI</h1>
            <h3 style="margin-top:0; color:#fff;">👤 Patient {new_patient if new_patient else selected_patient}</h3>
        </div>
        ''',
        unsafe_allow_html=True
    )

    # Define patient_id before using it
    patient_id = new_patient if new_patient else selected_patient

    # Chat area (scrollable)
    st.markdown('<div class="chat-area">', unsafe_allow_html=True)
    # Initialize or clear chat history when patient changes
    if 'current_patient' not in st.session_state:
        st.session_state.current_patient = patient_id
        st.session_state.messages = []
    elif st.session_state.current_patient != patient_id:
        st.session_state.current_patient = patient_id
        st.session_state.messages = []

    # Load and display chat history
    if selected_patient != "No patients":
        chat_history = db.get_chat_history(st.session_state.doctor_email, selected_patient)
        if chat_history:
            st.session_state.messages = [
                {"role": "user" if is_user else "assistant", "content": message}
                for message, is_user in chat_history
            ]

    # Display chat history using streamlit-chat
    for i, msg in enumerate(st.session_state.messages):
        message(msg["content"], is_user=(msg["role"] == "user"), key=f"msg_{i}")
    st.markdown('</div>', unsafe_allow_html=True)

    # Initialize session state for first-time prompt
    if 'first_prompt' not in st.session_state:
        st.session_state.first_prompt = True
    
    # Chat input (sticky at bottom)
    st.markdown('<div class="chat-input">', unsafe_allow_html=True)
    if prompt := st.chat_input("Ask your question about homeopathy..."):
    # Append additional text only for the first prompt
        if st.session_state.first_prompt:
            prompt += ", suggest a next related question or homeopathy remedy on it please."
        st.session_state.first_prompt = False  # Set to False after first use
    
        st.session_state.messages.append({"role": "user", "content": prompt})
        message(prompt, is_user=True, key=f"user_{len(st.session_state.messages)}")
        db.save_chat(st.session_state.doctor_email, patient_id, prompt, 1)
    
        # Get bot response
        with st.spinner("Thinking..."):
            response = run_query(prompt, st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        message(response, is_user=False, key=f"bot_{len(st.session_state.messages)}")
        db.save_chat(st.session_state.doctor_email, patient_id, response, 0)
else:
    st.markdown(
        '''
        <div class="main-header">
            <h1 style="margin-bottom:0.2em; color:#fff;">💬 Homeo Assist AI</h1>
        </div>
        ''',
        unsafe_allow_html=True
    )
    st.markdown(
        '''
        <div style="
            background-color: #f0f0f0; 
            padding: 20px; 
            border-radius: 10px; 
            box-shadow: 0 4px 8px rgba(0, 0, 0, 0.1); 
            margin-top: 20px;
        ">
            <h2 style="color: #333;">Patient-Specific. Literature-Based.
<p style="color: #333;">AI-Enhanced Remedies.</p></h2>
            <p style="color: #555;">
                Exclusively for certified homeopathic doctors, Homeo Assist AI helps you analyze cases smarter, with full patient-wise history, and remedy suggestions grounded in classical homeopathic literature like repertories and materia medica.
            </p>
            <ul style="color: #555; list-style-type: none; padding-left: 0;">
                <li>📂 Personalized patient memory</li>
                <li>🔍 Symptom-driven diagnosis</li>
                <li>📚 Powered by trusted homeopathic texts</li>
                <li>🔐 Secure. Doctor-only access.</li>
            </ul>
            <p style="color: #555;">
                Your clinical wisdom — now with AI by your side.
            </p>
        </div>
        ''',
        unsafe_allow_html=True
    )
    # Removed the redundant st.info line
    st.info("Log in to begin your AI-powered homeopathy journey — one patient at a time.")