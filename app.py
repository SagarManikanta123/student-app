import streamlit as st
import requests
import re

st.set_page_config(page_title="AI App Factory", layout="wide")

st.title("AI App Factory")
st.caption("Multi-Stage AI Generator: Intent → Persona → Logic → Guardrails → Code Engine")

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

# Automatically fetch API Key from Secrets
api_key = ""
if "GROQ_API_KEY" in st.secrets:
    api_key = sanitize_text(st.secrets["GROQ_API_KEY"])

if not api_key:
    with st.sidebar:
        st.header("Setup")
        raw_key = st.text_input("Groq API Key", type="password")
        api_key = sanitize_text(raw_key)

ACTIVE_MODEL = "openai/gpt-oss-20b"

def call_groq(messages, model, key, max_tok=1800):
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
            timeout=35
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
        with st.status("Factory Engine: Engineering architecture and building tool...", expanded=True) as status:
            status.write("🧠 Phase 1: Synthesizing Persona, Intent, Algorithm & Output Guardrails...")
            architect_prompt = (
                f"You are a master AI systems architect. A user wants to build an AI assistant with this specification:\n'{user_request}'\n\n"
                "Synthesize a complete operational system directive covering all essential engineering stages:\n"
                "1. Exact Role & Technical Persona\n"
                "2. Step-by-Step Problem Solving & Reasoning Protocol\n"
                "3. Edge Cases & Input Validation Handling\n"
                "4. Strict Output Formatting Rules (clean explanations, math syntax, step-by-step guidance)\n\n"
                "Write the complete, detailed system instructions directly."
            )
            master_spec = call_groq(
                [{"role": "user", "content": architect_prompt}],
                ACTIVE_MODEL,
                api_key,
                max_tok=900
            )

            status.write("🧠 Phase 2: Generating full standalone Python package...")
            clean_code = "# Standalone code generation skipped."
            if master_spec:
                code_prompt = (
                    f"Write a complete, bug-free standalone Python Streamlit application that implements this specification:\n{master_spec}\n\n"
                    "Requirements:\n"
                    "- Include all necessary library imports (e.g., streamlit, numpy, matplotlib, sympy if needed).\n"
                    "- Write the full, working implementation without placeholders or cutting off early.\n"
                    "- Return ONLY valid Python code enclosed in a single ```python ``` block."
                )
                raw_code = call_groq(
                    [{"role": "user", "content": code_prompt}],
                    ACTIVE_MODEL,
                    api_key,
                    max_tok=1800
                )
                if raw_code:
                    clean_code = extract_clean_code(raw_code)

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec or f"You are an assistant specialized in: {user_request}",
                "source_code": clean_code
            }
            st.session_state.chat_history = []
            status.update(label="Custom AI Built Successfully!", state="complete", expanded=False)

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

                    reply = call_groq(messages, ACTIVE_MODEL, api_key, max_tok=1000)
                    if reply:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})

    with tab2:
        st.subheader("Generated Python Code")
        st.caption("Complete, standalone code package ready to download and run:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
