import streamlit as st
import time

# IMPORT YOUR BACKEND FUNCTION
from chatbot import get_response

# ---------------- PAGE CONFIG ----------------
st.set_page_config(
    page_title="MediCare AI",
    page_icon="🩺"
)

# ---------------- HEADER ----------------
st.title("🩺 MediCare AI")
st.caption("💬 Smart Medical Assistant with AI Logic")

# ---------------- SESSION ----------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# ---------------- CHAT DISPLAY ----------------
for msg in st.session_state.messages:

    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# ---------------- TYPING EFFECT ----------------
def typing_effect(text):

    placeholder = st.empty()

    full_text = ""

    for char in text:

        full_text += char

        placeholder.markdown(full_text)

        time.sleep(0.01)

# ---------------- USER INPUT ----------------
user_input = st.chat_input("Describe your symptoms...")

# ---------------- PROCESS ----------------
if user_input:

    # Show user message
    st.chat_message("user").write(user_input)

    # Store user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    # Assistant response
    with st.chat_message("assistant"):

        with st.spinner("🧠 Analyzing symptoms..."):

            try:

                # DIRECTLY CALL BACKEND
                final_reply = get_response(
                    st.session_state.messages
                )

            except Exception as e:

                final_reply = (
                    "⚠️ Error while generating response."
                )

                print("Backend Error:", e)

        # Typing animation
        typing_effect(final_reply)

    # Store assistant response
    st.session_state.messages.append({
        "role": "assistant",
        "content": final_reply
    })

# ---------------- FOOTER ----------------
st.markdown("---")

st.caption("🏥 MediCare AI | Smart Chatbot Demo")