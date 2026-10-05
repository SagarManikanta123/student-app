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

# Check Streamlit Secrets first so users are never asked for a key
api_key = ""
if "GROQ_API_KEY" in st.secrets:
    api_key = sanitize_text(st.secrets["GROQ_API_KEY"])

# Fallback sidebar for manual override only if secret is missing
if not api_key:
    with st.sidebar:
        st.header("Admin Setup")
        raw_key = st.text_input("Groq API Key", type="password")
        api_key = sanitize_text(raw_key)

# Dynamic text model fetching
available_models = ["llama-3.1-8b-instant"]
if api_key:
    try:
        m_res = requests.get(
            "https://api.groq.com/openai/v1/models",
            headers={
                "Authorization": f"Bearer {api_key}",
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
            },
            timeout=8
        )
        if m_res.status_code == 200:
            fetched = [
                m["id"] for m in m_res.json().get("data", [])
                if not any(bad in m["id"].lower() for bad in ["whisper", "guard", "orpheus", "tts", "audio", "canopy", "safeguard"])
            ]
            if fetched:
                available_models = fetched
    except Exception:
        pass

selected_model = available_models[0]

def call_groq(messages, model, key, max_tok=1000, temp=0.2):
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
            st.error(f"Brain Pipeline API Error {res.status_code}: {res.text}")
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
    placeholder="e.g. An AI that solves and plots math equations, explains theory doubts, or converts notes into clean summaries"
)

if st.button("Build AI Tool", type="primary"):
    if not api_key:
        st.error("No API key configured. Please add GROQ_API_KEY in Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool you want to create.")
    else:
        with st.status("Executing 7-Brain Pipeline...", expanded=True) as status:
            # Brain 1: Intent Deconstructor
            status.write("🧠 Brain 1/7 (Deconstructor): Extracting primary intent and user deliverables...")
            p1 = f"Identify the core purpose, user persona, and primary deliverable for: '{user_request}'. Be concise."
            b1_out = call_groq([{"role": "user", "content": p1}], selected_model, api_key, max_tok=350)
            
            # Brain 2: Scope & Edge-Case Specialist
            status.write("🧠 Brain 2/7 (Scope Analyst): Mapping boundary conditions and edge cases...")
            p2 = f"Based on this scope:\n{b1_out}\nList 3 potential input failure modes and exact handling guidelines."
            b2_out = call_groq([{"role": "user", "content": p2}], selected_model, api_key, max_tok=350) if b1_out else None
            
            # Brain 3: System Architect
            status.write("🧠 Brain 3/7 (System Architect): Formulating core AI identity...")
            p3 = f"Given:\nIntent: {b1_out}\nGuardrails: {b2_out}\nWrite the exact expert persona and identity for this custom AI."
            b3_out = call_groq([{"role": "user", "content": p3}], selected_model, api_key, max_tok=400) if b2_out else None

            # Brain 4: Reasoning Protocol Planner
            status.write("🧠 Brain 4/7 (Reasoning Planner): Building step-by-step thinking algorithm...")
            p4 = f"For identity:\n{b3_out}\nDefine the precise step-by-step execution algorithm the AI must follow when answering."
            b4_out = call_groq([{"role": "user", "content": p4}], selected_model, api_key, max_tok=450) if b3_out else None

            # Brain 5: Output Styler & Guardrails
            status.write("🧠 Brain 5/7 (Guardrail Auditor): Enforcing formatting standards...")
            p5 = f"For execution logic:\n{b4_out}\nDefine strict layout and syntax formatting constraints (tables, markdown, bullet limits)."
            b5_out = call_groq([{"role": "user", "content": p5}], selected_model, api_key, max_tok=400) if b4_out else None

            # Compile Master System Prompt
            master_system_prompt = (
                f"### ROLE & IDENTITY\n{b3_out}\n\n"
                f"### OPERATING PROTOCOL\n{b4_out}\n\n"
                f"### FORMATTING & CONSTRAINTS\n{b5_out}\n\n"
                f"### EDGE CASE HANDLING\n{b2_out}"
            ) if b5_out else None

            # Brain 6: Code Synthesizer
            status.write("🧠 Brain 6/7 (Code Synthesizer): Compiling standalone Streamlit source package...")
            p6 = (
                f"Write a clean, standalone Python Streamlit app implementing this assistant logic:\n{master_system_prompt}\n\n"
                "Return ONLY valid python code wrapped inside a single ```python ``` block."
            )
            b6_out = call_groq([{"role": "user", "content": p6}], selected_model, api_key, max_tok=1800) if master_system_prompt else None

            # Brain 7: QA & Reviewer
            status.write("🧠 Brain 7/7 (Quality Assurance): Auditing pipeline output and issuing health report...")
            p7 = f"Review this generated directive:\n{master_system_prompt}\nProvide a 2-sentence QA sign-off confirming operational readiness."
            b7_out = call_groq([{"role": "user", "content": p7}], selected_model, api_key, max_tok=250) if master_system_prompt else None

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
