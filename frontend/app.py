import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import streamlit as st
from backend.database import Database
from backend.chat_engine import run_query
from backend.auth import Auth  # Add this import

# Page config
st.set_page_config(
    page_title="Homeopathy ChatBot",
    layout="centered",
    initial_sidebar_state="expanded"
)

# Initialize database and auth
db = Database()
auth = Auth(db)

# Main title
st.title("💬 Homeopathy ChatBot")

# Sidebar authentication and registration
with st.sidebar:
    st.header("👨‍⚕️ Doctor Access")
    tab1, tab2 = st.tabs(["Login", "Register"])
    
    with tab1:
        doctor_email = st.text_input("Email", key="login_email")
        if doctor_email:
            doctor = db.get_doctor(doctor_email)
            if not doctor:
                st.error("Doctor not found. Please register first.")
                st.stop()
            elif not doctor[4]:  # is_verified check
                otp = st.text_input("Enter OTP")
                if st.button("Verify OTP"):
                    if auth.verify_otp(doctor_email, otp):
                        st.success("Account verified successfully!")
                        st.experimental_rerun()
                    else:
                        st.error("Invalid OTP")
                st.stop()
            else:
                st.success("Logged in successfully!")
    
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

    # Move Patient Management outside the form
    if doctor_email and doctor[4]:  # Only show if doctor is logged in and verified
        st.header("👤 Patient Management")
        patients = db.get_patients(doctor_email)
        selected_patient = st.selectbox("Select Patient", patients if patients else ["No patients"])
        new_patient = st.text_input("Add New Patient")
        
        if st.button("Add Patient") and new_patient:
            db.add_patient(doctor_email, new_patient)
            st.success(f"Added patient: {new_patient}")
            st.experimental_rerun()

# Chat interface
if doctor_email and (selected_patient != "No patients" or new_patient):
    patient_id = new_patient if new_patient else selected_patient
    st.markdown(f"### Chatting with: {patient_id}")
    
    # Initialize chat history
    if 'messages' not in st.session_state:
        st.session_state.messages = []
        
    # Display chat history
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

    # Chat input
    if prompt := st.chat_input("Ask your question about homeopathy..."):
        # Add user message
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Get bot response
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                response = run_query(prompt, st.session_state.messages)
                st.markdown(response)
                st.session_state.messages.append({"role": "assistant", "content": response})

else:
    st.info("Please log in and select a patient to start chatting.")