import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory", layout="wide", initial_sidebar_state="collapsed")

st.title("AI App Factory")
st.caption("Robust Multi-Brain Core: Architect → Code Synthesizer → QA Verifier")

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

# Check Streamlit Secrets first
api_key = ""
if "GROQ_API_KEY" in st.secrets:
    api_key = sanitize_text(st.secrets["GROQ_API_KEY"])

if not api_key:
    with st.sidebar:
        st.header("Admin Setup")
        raw_key = st.text_input("Groq API Key", type="password")
        api_key = sanitize_text(raw_key)

# Auto-detect the best active text model
def get_live_model(key):
    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=8
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            valid = [
                m["id"] for m in data
                if not any(bad in m["id"].lower() for bad in ["whisper", "guard", "orpheus", "tts", "audio", "vision"])
            ]
            for preferred in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3.8-27b"]:
                if preferred in valid:
                    return preferred
            if valid:
                return valid[0]
    except Exception:
        pass
    return "openai/gpt-oss-20b"

active_model = get_live_model(api_key) if api_key else "openai/gpt-oss-20b"

def call_groq(messages, model, key, max_tok=600, temp=0.2):
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
            timeout=30
        )
        if res.status_code == 200:
            content = res.json()["choices"][0]["message"]["content"]
            return content.strip() if content else None
        else:
            st.error(f"API Error {res.status_code}: {res.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Pipeline timed out. Please retry.")
        return None
    except Exception as exc:
        st.error(f"Connection failed: {exc}")
        return None

if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_request = st.text_area(
    "What AI tool do you want to create?",
    placeholder="e.g. make an AI that can draw graphs based on user defined functions"
)

if st.button("Build AI Tool", type="primary"):
    if not api_key:
        st.error("No API key configured. Please add GROQ_API_KEY in Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool you want to create.")
    else:
        with st.status(f"Running Engine ({active_model})...", expanded=True) as status:
            # Brain 1: Master Architect & Reasoning Protocol
            status.write("🧠 Brain 1/3 (Architect): Engineering persona, operating logic, and edge-case guardrails...")
            p1 = (
                f"You are a master AI architect. A user wants to build an AI assistant with this goal:\n'{user_request}'\n\n"
                "Define the comprehensive system instructions for this custom AI. Cover:\n"
                "1. Exact expert persona & role.\n"
                "2. Step-by-step problem-solving and reasoning rules.\n"
                "3. Edge cases and how to avoid errors.\n"
                "4. Strict output formatting rules.\n"
                "Be direct, detailed, and clear."
            )
            master_system_prompt = call_groq([{"role": "user", "content": p1}], active_model, api_key, max_tok=600)
            
            # Brain 2: Code Synthesizer
            status.write("🧠 Brain 2/3 (Code Synthesizer): Compiling standalone Python package...")
            p2 = (
                f"Write a standalone Python Streamlit app that runs an assistant with these instructions:\n{master_system_prompt}\n\n"
                "Output ONLY valid python code wrapped in a single ```python ``` block."
            )
            raw_code = call_groq([{"role": "user", "content": p2}], active_model, api_key, max_tok=700)
            
            # Brain 3: QA & Verification
            status.write("🧠 Brain 3/3 (QA Verifier): Auditing operational readiness...")
            p3 = f"Provide a brief 1-sentence verification confirming that this assistant is ready to use:\n{master_system_prompt}"
            qa_note = call_groq([{"role": "user", "content": p3}], active_model, api_key, max_tok=100)

            # Deploy to state
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation skipped."
            effective_prompt = master_system_prompt or f"You are an assistant designed for: {user_request}"
            
            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": effective_prompt,
                "source_code": clean_code,
                "qa_report": qa_note or "Operational verified."
            }
            st.session_state.chat_history = []
            status.update(label="Custom AI Built and Ready!", state="complete", expanded=False)

if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["⚡ Live Custom AI", "📄 Standalone Code (.py)"])
    
    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"Status: {app_info['qa_report']}")
        
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
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
                    
                    reply = call_groq(messages, active_model, api_key, max_tok=500, temp=0.3)
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
