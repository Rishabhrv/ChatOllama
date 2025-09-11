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

        response = requests.post(
            OLLAMA_URL,
            json={"model": st.session_state["selected_model"], "messages": st.session_state["messages"]},
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


# --- Benchmark Section ---
st.write("---")
st.write("### ⚡ Benchmark All Models")

# Sample prompts for benchmarking
prompts = [
    "Explain why the sky is blue in simple terms.",
    "If you flip a coin 10 times, what is the probability of getting at least 6 heads?",
    "Write a short bedtime story about a robot and a cat.",
    "Write a Python function to check if a number is prime.",
]

def query_model(model_id, prompt):
    """Send prompt to a model and return output + elapsed time"""
    payload = {"model": model_id, "messages": [{"role": "user", "content": prompt}]}
    start_time = time.time()
    response = requests.post(OLLAMA_URL, json=payload, stream=True)
    output = ""
    for line in response.iter_lines():
        if line:
            data = json.loads(line.decode("utf-8"))
            if "message" in data and "content" in data["message"]:
                output += data["message"]["content"]
    elapsed_time = round(time.time() - start_time, 2)
    return output.strip(), elapsed_time

if st.button("Run Benchmark"):
    results = {}
    with st.spinner("Benchmarking models... this may take a few minutes ⏳"):
        for model_name, model_id in models.items():
            st.write(f"#### 🚀 Testing {model_name}")
            model_times = []
            for prompt in prompts:
                output, elapsed = query_model(model_id, prompt)
                st.markdown(f"**Prompt:** {prompt}")
                st.markdown(f"⏱️ Time: `{elapsed} sec`")
                st.markdown(f"**Answer:**\n{output}\n")
                model_times.append(elapsed)
            avg_time = round(sum(model_times) / len(model_times), 2)
            results[model_name] = avg_time

    st.write("### 📊 Benchmark Summary")
    for model_name, avg_time in results.items():
        st.write(f"- {model_name}: **{avg_time} sec** average per response")
