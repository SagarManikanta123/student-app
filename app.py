import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory", layout="wide", initial_sidebar_state="expanded")

st.title("AI App Factory")
st.caption("Describe any tool or assistant. The factory will build, configure, and launch it live.")

def sanitize_text(text):
    if not text:
        return ""
    return "".join(c for c in text.strip() if 32 <= ord(c) <= 126)

def extract_clean_code(text):
    if not text:
        return ""
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    return text.strip()

# Standard, fast Groq models
VALID_MODELS = [
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant"
]

with st.sidebar:
    st.header("Factory Settings")
    raw_key = st.text_input("Groq API Key", type="password")
    api_key = sanitize_text(raw_key)
    st.markdown("[Get a free Groq API key here](https://console.groq.com/keys)")
    st.markdown("---")
    
    st.markdown("**Engine Settings:**")
    selected_model = st.selectbox("AI Model", VALID_MODELS, index=0)

def call_groq(messages, model, key, max_tok=1800, temp=0.2):
    clean_k = sanitize_text(key)
    headers = {
        "Authorization": f"Bearer {clean_k}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": temp,
        "max_tokens": max_tok
    }
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=25
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"API Error {res.status_code}: {res.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out after 25 seconds. Please try again.")
        return None
    except Exception as exc:
        st.error(f"Connection failed: {exc}")
        return None

# Session state initialization
if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_request = st.text_area(
    "What AI tool do you want to create?",
    placeholder="e.g. create an AI which can decode C codes and explain them point to point in bullet points"
)

if st.button("Build AI Tool", type="primary"):
    if not api_key:
        st.warning("Please enter your Groq API Key in the sidebar.")
    elif not user_request.strip():
        st.warning("Please type a description of what you want to create.")
    else:
        with st.status("Factory running: Constructing Custom AI...", expanded=True) as status:
            status.write("Architect Brain: Engineering AI persona, instructions, and tool rules...")
            architect_prompt = (
                f"You are a meta-architect. A user wants to build an AI tool with this purpose:\n'{user_request}'\n\n"
                "Define the complete system instructions for this custom AI. Include:\n"
                "1. Role and expertise.\n"
                "2. Specific step-by-step problem-solving method.\n"
                "3. Strict output formatting rules.\n"
                "Be thorough and direct."
            )
            spec = call_groq(
                [{"role": "user", "content": architect_prompt}],
                selected_model,
                api_key,
                max_tok=800,
                temp=0.2
            )
            
            if spec:
                status.write("Builder Brain: Generating standalone source code package...")
                code_prompt = (
                    f"Create a full, standalone Python Streamlit app implementing this specification:\n{spec}\n\n"
                    "Output ONLY the Python code in a single ```python ``` code block. Include necessary imports."
                )
                source_code = call_groq(
                    [{"role": "user", "content": code_prompt}],
                    selected_model,
                    api_key,
                    max_tok=1800,
                    temp=0.2
                )
                
                clean_source = extract_clean_code(source_code) if source_code else "# Code generation skipped"
                
                st.session_state.configured_app = {
                    "goal": user_request,
                    "system_prompt": spec,
                    "source_code": clean_source
                }
                st.session_state.chat_history = []
                status.update(label="Custom AI Built and Ready!", state="complete", expanded=False)

# Render the active AI if built
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["⚡ Live Custom AI", "📄 Standalone Code (.py)"])
    
    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"Goal: {app_info['goal']}")
        
        # Display chat history
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        # Input prompt for the custom AI
        user_input = st.chat_input("Interact with your custom AI here...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)
            
            with st.chat_message("assistant"):
                with st.spinner("Processing..."):
                    messages = [{"role": "system", "content": app_info["system_prompt"]}]
                    for m in st.session_state.chat_history:
                        messages.append({"role": m["role"], "content": m["content"]})
                    
                    reply = call_groq(messages, selected_model, api_key, max_tok=1800, temp=0.3)
                    if reply:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    with tab2:
        st.subheader("Generated Python Code")
        st.caption("You can copy or download this standalone Streamlit app to run locally or host elsewhere.")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
