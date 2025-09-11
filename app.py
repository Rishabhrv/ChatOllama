import streamlit as st
import requests
import json

st.set_page_config(page_title="Offline Chatbot", layout="centered")

st.write("### 💬 Chat with Your Local Models")

# Available models
models = {
    "Phi-3 (3.8B)": "phi3:3.8b",
    "Mistral 7B": "mistral:7b",
    "LLaMA 3.1 (8B)": "llama3.1:8b",
}

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

# Chat input
if prompt := st.chat_input("Type your message..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    # Placeholder for streaming reply
    with st.chat_message("assistant"):
        reply_placeholder = st.empty()
        reply_content = ""

        response = requests.post(
            "http://localhost:11434/api/chat",
            json={"model": st.session_state["selected_model"], "messages": st.session_state["messages"]},
            stream=True,
        )

        # Stream response as it arrives
        for line in response.iter_lines():
            if line:
                data = json.loads(line.decode("utf-8"))
                if "message" in data and "content" in data["message"]:
                    token = data["message"]["content"]
                    reply_content += token
                    reply_placeholder.markdown(reply_content)  # update live

        # Save assistant reply
        st.session_state["messages"].append({"role": "assistant", "content": reply_content})
