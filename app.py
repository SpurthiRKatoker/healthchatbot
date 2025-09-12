import streamlit as st
from chatbot import HealthChatbot

# Initialize chatbot
bot = HealthChatbot()

# Streamlit UI
st.title("🩺 Health Chatbot")
st.write("Ask health-related questions and get advice.")

# Input text box
user_input = st.text_input("You:", "")

if user_input:
    response = bot.get_response(user_input)
    st.text_area("Chatbot:", value=response, height=150, max_chars=None)
