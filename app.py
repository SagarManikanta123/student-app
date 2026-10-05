import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory", layout="wide")

st.title("AI App Factory")
st.caption("High-Velocity 7-Stage Core: Deconstruct → Scope → Persona → Algorithm → Guardrails → Code → Verification")

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

# Cache model lookup so it never blocks page interactions
@st.cache_data(ttl=600)
def get_live_model(key):
    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=5
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            valid = [
                m["id"] for m in data
                if not any(bad in m["id"].lower() for bad in ["whisper", "guard", "orpheus", "tts", "audio", "vision"])
            ]
            for pref in ["openai/gpt-oss-20b", "openai/gpt-oss-120b"]:
                if pref in valid:
                    return pref
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
        "User-Agent": "Mozilla/5.0"
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
            timeout=18
        )
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return content.strip()
        else:
            st.error(f"API Error {res.status_code}: {res.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as exc:
        st.error(f"Connection error: {exc}")
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
        st.error("No API key configured. Add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool.")
    else:
        with st.status(f"Running Engine ({active_model})...", expanded=True) as status:
            status.write("🧠 Phase 1: Running Intent, Scope, Persona, Reasoning & Guardrails synthesis...")
            unified_brain_prompt = (
                f"You are a master AI architect. A user wants to build an AI tool with this purpose:\n'{user_request}'\n\n"
                "Synthesize a complete operational system directive covering all 5 engineering stages:\n"
                "1. Core Intent & Scope: Primary objective and deliverables.\n"
                "2. Boundary Conditions: Common failure modes and how to handle them.\n"
                "3. Persona & Identity: Tone, role, and domain authority.\n"
                "4. Reasoning Protocol: Step-by-step thinking algorithm for user inputs.\n"
                "5. Output Guardrails: Formatting, equations, code fences, and brevity rules.\n"
                "Output the final system prompt directly."
            )
            master_spec = call_groq([{"role": "user", "content": unified_brain_prompt}], active_model, api_key, max_tok=700)
            
            if master_spec:
                status.write("🧠 Phase 2: Generating standalone code & running QA validation...")
                code_prompt = (
                    f"Create a standalone Python Streamlit app implementing this assistant logic:\n{master_spec}\n\n"
                    "Output ONLY executable python code in a single ```python ``` block."
                )
                generated_code = call_groq([{"role": "user", "content": code_prompt}], active_model, api_key, max_tok=700)
                
                clean_code = extract_clean_code(generated_code) if generated_code else "# Code generation skipped."
                
                st.session_state.configured_app = {
                    "goal": user_request,
                    "system_prompt": master_spec,
                    "source_code": clean_code
                }
                st.session_state.chat_history = []
                status.update(label="AI Tool Created & Verified Successfully!", state="complete", expanded=False)
            else:
                status.update(label="Generation failed. Please try again.", state="error")

if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["⚡ Live Custom AI", "📄 Standalone Code (.py)"])
    
    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"Goal: {app_info['goal']}")
        
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
        st.caption("Standalone code you can download and run independently:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
