import streamlit as st
import requests
import json
import time

st.set_page_config(page_title="Offline Chatbot", layout="centered")

st.write("### 💬 Chat with Your Local Models")

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
                    reply_placeholder.markdown(reply_content + " ▌")

        end_time = time.time()
        elapsed_time = round(end_time - start_time, 2)

        # Final update without cursor
        reply_content = reply_content.strip() + f"\n\n⏱️ Response time: {elapsed_time} sec"
        reply_placeholder.markdown(reply_content)

        # Save assistant reply
        st.session_state["messages"].append({"role": "assistant", "content": reply_content})
