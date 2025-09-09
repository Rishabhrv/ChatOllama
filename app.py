import streamlit as st
import requests

st.set_page_config(page_title="Phi-3 Chat", layout="centered")

st.write("## 💬 Chat with Phi-3 (3.8B)")

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
    )

    reply = response.json()["message"]["content"]

    st.session_state["messages"].append({"role": "assistant", "content": reply})
    with st.chat_message("assistant"):
        st.markdown(reply)
