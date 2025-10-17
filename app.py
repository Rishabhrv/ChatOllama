import streamlit as st
import requests
import json
import time
import os

st.set_page_config(page_title="Offline Chatbot", layout="centered")

st.markdown("""
    <style>
            
        /* Remove Streamlit's default top padding */
        .main > div {
            padding-top: 0px !important;
        }
        /* Ensure the first element has minimal spacing */
        .block-container {
            padding-top: 28px !important;  /* Small padding for breathing room */
        }
            """, unsafe_allow_html=True)

# Function to check credentials
def check_credentials(username, password):
    if not os.path.exists("users.txt"):
        return False
    with open("users.txt", "r") as f:
        for line in f:
            stored_user, stored_pass = line.strip().split(":")
            if username == stored_user and password == stored_pass:
                return True
    return False

# Function to save new user
def save_user(username, password):
    with open("users.txt", "a") as f:
        f.write(f"{username}:{password}\n")

# Login page
def login_page():
    st.title("Login to Offline Chatbot")
    username = st.text_input("Username")
    password = st.text_input("Password", type="password")
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Login"):
            if check_credentials(username, password):
                st.session_state["logged_in"] = True
                st.session_state["username"] = username
                st.rerun()
            else:
                st.error("Invalid credentials. Try again or register.")
    with col2:
        if st.button("Register"):
            if username and password:
                if not check_credentials(username, password):
                    save_user(username, password)
                    st.success("Registered successfully! Please login.")
                else:
                    st.error("Username already exists.")
            else:
                st.error("Please enter both username and password.")

# Main chat app
def chat_app():
    st.write("### 💬 Chat Without Limits!")
    st.write(f"Welcome, {st.session_state['username']}!")

    # Available models
    models = {
        "LLaMA 3.1 8B (Meta) - High-Performance": "llama3.1:8b",
        "Gemma 3 270M (Google) - Small, Fast": "gemma3:270m",
        "Gemma 3 1B (Google) - Medium, Balanced": "gemma3:1b",
        "LLaMA 2 7B (Meta) - Uncensored": "llama2-uncensored:7b",
        "Dolphine 7B (Mistral) - Uncensored": "dolphin-mistral:7b",
        "Smollm2 1.7B (Hugging Face) - Open, Efficient": "smollm2:1.7b",
        "Qwen 2.5 7B (Alibaba) - Advance Coder": "qwen2.5-coder:7b",
        "Qwen 2.5 3B (Alibaba) - Coder": "qwen2.5-coder:3b",
    }

    OLLAMA_URL = "http://localhost:11434/api/chat"

    # Model selector
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = list(models.values())[0]

    selected_model_name = st.selectbox(
        "Select Model", list(models.keys()), 
        index=list(models.values()).index(st.session_state["selected_model"]),
        label_visibility="collapsed"
    )
    st.session_state["selected_model"] = models[selected_model_name]

    # Message history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Control buttons
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⏹ Stop Response"):
            st.session_state["stop_generation"] = True
    with col2:
        if st.button("🧹 Clear Chat"):
            st.session_state["messages"] = []
            st.rerun()

    # Stop flag
    if "stop_generation" not in st.session_state:
        st.session_state["stop_generation"] = False

    # Chat input
    if prompt := st.chat_input("Type your message..."):
        st.session_state["messages"].append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # Placeholder for streaming reply
        with st.chat_message("assistant"):
            reply_placeholder = st.empty()
            reply_content = ""

            # Measure response time
            start_time = time.time()

            # Prepare request payload
            payload = {"model": st.session_state["selected_model"], "messages": st.session_state["messages"]}

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                stream=True,
            )

            # Reset stop flag before streaming
            st.session_state["stop_generation"] = False

            # Stream response with cursor effect
            for line in response.iter_lines():
                if st.session_state["stop_generation"]:
                    break
                if line:
                    data = json.loads(line.decode("utf-8"))
                    if "message" in data and "content" in data["message"]:
                        token = data["message"]["content"]
                        reply_content += token
                        reply_placeholder.markdown(reply_content + " ➤")

            end_time = time.time()
            elapsed_time = round(end_time - start_time, 2)

            # Final update without cursor
            reply_content = reply_content.strip() + f"\n\n⏱️ Response time: {elapsed_time} sec"
            reply_placeholder.markdown(reply_content)

            # Save assistant reply (only if not interrupted)
            if not st.session_state["stop_generation"]:
                st.session_state["messages"].append({"role": "assistant", "content": reply_content})

# Main app logic
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    chat_app()
