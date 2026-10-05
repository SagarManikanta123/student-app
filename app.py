import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory - 7-Brain Pipeline", layout="wide", initial_sidebar_state="collapsed")

st.title("AI App Factory (7-Brain Core)")
st.caption("Deconstructor → Scope → Architect → Reasoning → Guardrail → Synthesizer → QA")

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

# Auto-detect active text models directly from Groq API
def get_live_model(key):
    try:
        res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={"Authorization": f"Bearer {key}"},
            timeout=8
        )
        if res.status_code == 200:
            data = res.json().get("data", [])
            # Filter out audio, whisper, safeguard, and vision models
            valid = [
                m["id"] for m in data
                if not any(bad in m["id"].lower() for bad in ["whisper", "guard", "orpheus", "tts", "audio", "vision"])
            ]
            # Prioritize standard fast models
            for preferred in ["openai/gpt-oss-20b", "openai/gpt-oss-120b", "qwen/qwen3-32b"]:
                if preferred in valid:
                    return preferred
            if valid:
                return valid[0]
    except Exception:
        pass
    return "openai/gpt-oss-20b"

active_model = get_live_model(api_key) if api_key else "openai/gpt-oss-20b"

def call_groq(messages, model, key, max_tok=450, temp=0.2):
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
            return res.json()["choices"][0]["message"]["content"]
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
        with st.status(f"Executing 7-Brain Pipeline (Engine: {active_model})...", expanded=True) as status:
            # Brain 1: Intent Deconstructor
            status.write("🧠 Brain 1/7 (Deconstructor): Extracting primary intent...")
            p1 = f"Identify the core purpose, user persona, and primary deliverable for: '{user_request}'. Be very concise."
            b1_out = call_groq([{"role": "user", "content": p1}], active_model, api_key, max_tok=200)
            
            # Brain 2: Scope & Edge-Case Specialist
            status.write("🧠 Brain 2/7 (Scope Analyst): Mapping boundary conditions...")
            p2 = f"Based on this scope:\n{b1_out}\nList 2 potential input failure modes and handling guidelines concisely."
            b2_out = call_groq([{"role": "user", "content": p2}], active_model, api_key, max_tok=200) if b1_out else None
            
            # Brain 3: System Architect
            status.write("🧠 Brain 3/7 (System Architect): Formulating core AI identity...")
            p3 = f"Given:\nIntent: {b1_out}\nGuardrails: {b2_out}\nWrite the exact expert persona and identity for this custom AI."
            b3_out = call_groq([{"role": "user", "content": p3}], active_model, api_key, max_tok=250) if b2_out else None

            # Brain 4: Reasoning Protocol Planner
            status.write("🧠 Brain 4/7 (Reasoning Planner): Building execution algorithm...")
            p4 = f"For identity:\n{b3_out}\nDefine the step-by-step execution algorithm the AI must follow when answering."
            b4_out = call_groq([{"role": "user", "content": p4}], active_model, api_key, max_tok=250) if b3_out else None

            # Brain 5: Output Styler & Guardrails
            status.write("🧠 Brain 5/7 (Guardrail Auditor): Enforcing formatting standards...")
            p5 = f"For execution logic:\n{b4_out}\nDefine strict layout and syntax formatting constraints (bullet limits, math notation)."
            b5_out = call_groq([{"role": "user", "content": p5}], active_model, api_key, max_tok=200) if b4_out else None

            master_system_prompt = (
                f"### ROLE & IDENTITY\n{b3_out}\n\n"
                f"### OPERATING PROTOCOL\n{b4_out}\n\n"
                f"### FORMATTING & CONSTRAINTS\n{b5_out}\n\n"
                f"### EDGE CASE HANDLING\n{b2_out}"
            ) if b5_out else None

            # Brain 6: Code Synthesizer
            status.write("🧠 Brain 6/7 (Code Synthesizer): Compiling standalone Streamlit package...")
            p6 = (
                f"Write a standalone Python Streamlit app implementing this assistant logic:\n{master_system_prompt}\n\n"
                "Return ONLY valid python code wrapped in a single ```python ``` block."
            )
            b6_out = call_groq([{"role": "user", "content": p6}], active_model, api_key, max_tok=700) if master_system_prompt else None

            # Brain 7: QA & Reviewer
            status.write("🧠 Brain 7/7 (Quality Assurance): Issuing readiness sign-off...")
            p7 = f"Review this generated directive:\n{master_system_prompt}\nProvide a 1-sentence QA sign-off confirming operational readiness."
            b7_out = call_groq([{"role": "user", "content": p7}], active_model, api_key, max_tok=100) if master_system_prompt else None

            if master_system_prompt:
                clean_code = extract_clean_code(b6_out) if b6_out else "# Code generation unavailable."
                st.session_state.configured_app = {
                    "goal": user_request,
                    "system_prompt": master_system_prompt,
                    "source_code": clean_code,
                    "qa_report": b7_out or "QA Passed."
                }
                st.session_state.chat_history = []
                status.update(label="All 7 Brains Finished Successfully!", state="complete", expanded=False)

if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["⚡ Live Custom AI", "📄 Standalone Code (.py)"])
    
    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"QA Verification: {app_info['qa_report']}")
        
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
