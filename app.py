import streamlit as st
import requests
import json
import time
import os

st.set_page_config(page_title="Offline Chatbot", layout="centered")

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
    st.write("### 💬 Chat with Your Local Models")
    st.write(f"Welcome, {st.session_state['username']}!")
    
    # Logout button
    if st.button("Logout"):
        st.session_state["logged_in"] = False
        st.session_state["messages"] = []
        st.session_state.pop("username", None)
        st.rerun()

    # Available models
    models = {
        "Phi-3 (3.8B)": "phi3:3.8b",
        "Mistral 7B": "mistral:7b",
        "LLaMA 3.1 (8B)": "llama3.1:8b",
        "Gemma 3 (4B)": "gemma3:4b",
    }

    OLLAMA_URL = "http://localhost:11434/api/chat"

    # Model selector
    if "selected_model" not in st.session_state:
        st.session_state["selected_model"] = list(models.values())[0]

    selected_model_name = st.selectbox(
        "Select Model", list(models.keys()), 
        index=list(models.values()).index(st.session_state["selected_model"])
    )
    st.session_state["selected_model"] = models[selected_model_name]

    # Message history
    if "messages" not in st.session_state:
        st.session_state["messages"] = []

    for msg in st.session_state["messages"]:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # If Gemma selected → allow image upload
    uploaded_image = None
    if st.session_state["selected_model"] == "gemma3:4b":
        uploaded_image = st.file_uploader("Upload an image for Gemma", type=["png", "jpg", "jpeg"])

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

            # If Gemma and image uploaded → include image
            files = None
            if st.session_state["selected_model"] == "gemma3:4b" and uploaded_image is not None:
                files = {"image": uploaded_image.getvalue()}  # raw bytes

            response = requests.post(
                OLLAMA_URL,
                json=payload,
                files=files,
                stream=True,
            )

            # Stream response with cursor effect
            for line in response.iter_lines():
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

            # Save assistant reply
            st.session_state["messages"].append({"role": "assistant", "content": reply_content})

# Main app logic
if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False

if not st.session_state["logged_in"]:
    login_page()
else:
    chat_app()