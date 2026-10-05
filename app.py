import streamlit as st
import requests
import re

st.set_page_config(page_title="AI App Factory", layout="wide")

st.title("AI App Factory")
st.caption("Custom AI Creator Engine")

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

# Read API Key from Secrets or Sidebar
api_key = ""
if "GROQ_API_KEY" in st.secrets:
    api_key = sanitize_text(st.secrets["GROQ_API_KEY"])

if not api_key:
    with st.sidebar:
        st.header("Setup")
        raw_key = st.text_input("Groq API Key", type="password")
        api_key = sanitize_text(raw_key)

# Fast, stable default model
ACTIVE_MODEL = "openai/gpt-oss-20b"

def call_groq(messages, model, key, max_tok=600):
    clean_k = sanitize_text(key)
    headers = {
        "Authorization": f"Bearer {clean_k}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }
    payload = {
        "model": model,
        "messages": messages,
        "temperature": 0.2,
        "max_tokens": max_tok
    }
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=15
        )
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return content.strip()
        else:
            st.error(f"Groq API Error {res.status_code}: {res.text}")
            return None
    except requests.exceptions.Timeout:
        st.error("Request timed out. Please try again.")
        return None
    except Exception as exc:
        st.error(f"Connection failed: {exc}")
        return None

# State Initialization
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
        st.error("Please add GROQ_API_KEY to Streamlit Secrets or enter it in the sidebar.")
    elif not user_request.strip():
        st.warning("Please describe what AI tool you want to create.")
    else:
        with st.spinner("Factory Engine: Synthesizing architecture and code..."):
            # Brain 1: Master Specification & Prompt Architecture
            architect_prompt = (
                f"You are a master AI architect. A user wants to build an AI tool with this purpose:\n'{user_request}'\n\n"
                "Synthesize a complete operational system directive covering all key engineering stages:\n"
                "1. Core Persona & Tone\n"
                "2. Step-by-Step Reasoning Logic\n"
                "3. Edge Cases & Boundary Handling\n"
                "4. Exact Formatting Rules\n\n"
                "Output the final system prompt directly."
            )
            master_spec = call_groq(
                [{"role": "user", "content": architect_prompt}],
                ACTIVE_MODEL,
                api_key,
                max_tok=600
            )

            # Brain 2: Standalone Code Generator
            clean_code = "# Standalone code generation skipped."
            if master_spec:
                code_prompt = (
                    f"Create a clean standalone Streamlit Python app implementing this logic:\n{master_spec}\n\n"
                    "Output ONLY the python code wrapped inside a single ```python ``` code block."
                )
                raw_code = call_groq(
                    [{"role": "user", "content": code_prompt}],
                    ACTIVE_MODEL,
                    api_key,
                    max_tok=700
                )
                if raw_code:
                    clean_code = extract_clean_code(raw_code)

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec or f"You are an assistant specialized in: {user_request}",
                "source_code": clean_code
            }
            st.session_state.chat_history = []
            st.success("Custom AI Built Successfully!")

# Display Active Workspace
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

                    reply = call_groq(messages, ACTIVE_MODEL, api_key, max_tok=500)
                    if reply:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    with tab2:
        st.subheader("Generated Python Code")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
