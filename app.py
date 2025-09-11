import streamlit as st
import requests
import json

st.set_page_config(page_title="Phi-3 Chat", layout="centered")

st.write("### 💬 Chat with Phi-3 (3.8B)")

if "messages" not in st.session_state:
    st.session_state["messages"] = []

for msg in st.session_state["messages"]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if prompt := st.chat_input("Type your message..."):
    st.session_state["messages"].append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    response = requests.post(
        "http://localhost:11434/api/chat",
        json={"model": "phi3:3.8b", "messages": st.session_state["messages"]},
        stream=True,   # enable streaming
    )

    reply_content = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                reply_content += data["message"]["content"]

    st.session_state["messages"].append({"role": "assistant", "content": reply_content})
    with st.chat_message("assistant"):
        st.markdown(reply_content)
