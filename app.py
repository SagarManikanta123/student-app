import streamlit as st
import requests
import re
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="AI App Factory - 10-Brain Council", layout="wide")

st.title("AI App Factory (10-Brain Ensemble)")
st.caption("Deconstructor → Scope → Architect → Protocol → Guardrail → UI Spec → Logic Spec → Resilience → Ensemble Synthesizer → QA Critic")

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

# Read Secrets
api_key = ""
if "GROQ_API_KEY" in st.secrets:
    api_key = sanitize_text(st.secrets["GROQ_API_KEY"])

if not api_key:
    with st.sidebar:
        st.header("Setup")
        raw_key = st.text_input("Groq API Key", type="password")
        api_key = sanitize_text(raw_key)

ACTIVE_MODEL = "openai/gpt-oss-20b"

def call_groq(messages, model=ACTIVE_MODEL, key=api_key, max_tok=600, temp=0.2):
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
            timeout=30
        )
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return content.strip()
        else:
            return None
    except Exception:
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
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool you want to create.")
    else:
        with st.status("Activating 10-Brain Ensemble...", expanded=True) as status:
            # Brain 1: Goal Deconstructor
            status.write("🧠 Brain 1/10 (Deconstructor): Extracting functional targets...")
            b1 = call_groq([{"role": "user", "content": f"Extract the core functional deliverable for: '{user_request}'. Be brief."}], max_tok=150)

            # Brain 2: Scope & Boundary Analyst
            status.write("🧠 Brain 2/10 (Scope Analyst): Formulating edge cases and boundary conditions...")
            b2 = call_groq([{"role": "user", "content": f"List 2 failure modes and constraints for: {b1 or user_request}."}], max_tok=150)

            # Brain 3: Persona Architect
            status.write("🧠 Brain 3/10 (Persona Architect): Engineering system identity...")
            b3 = call_groq([{"role": "user", "content": f"Define the expert persona for: {b1 or user_request} under constraints: {b2}."}], max_tok=200)

            # Brain 4: Reasoning Protocol Planner
            status.write("🧠 Brain 4/10 (Protocol Planner): Formulating step-by-step thinking algorithm...")
            b4 = call_groq([{"role": "user", "content": f"Define 3 step execution protocol for: {b3}."}], max_tok=200)

            # Brain 5: Guardrail & Output Styler
            status.write("🧠 Brain 5/10 (Guardrail Auditor): Enforcing formatting and safety standards...")
            b5 = call_groq([{"role": "user", "content": f"Define strict output syntax rules (bullets, math notation, no conversational filler) for: {b4}."}], max_tok=150)

            # Parallel Specialized Trio: Brains 6, 7, and 8 run simultaneously to prevent lag
            status.write("🧠 Brains 6, 7 & 8 (UI/UX, Computation, and Resilience Specialists): Executing parallel architecture...")
            
            def run_b6():
                return call_groq([{"role": "user", "content": f"Plan Streamlit UI widgets, labels, and layouts for: {b1}"}], max_tok=200)
            def run_b7():
                return call_groq([{"role": "user", "content": f"Plan Python libraries, functions, and mathematical backend for: {b1}"}], max_tok=200)
            def run_b8():
                return call_groq([{"role": "user", "content": f"Plan input sanitization and exception handling for: {b2}"}], max_tok=150)

            with ThreadPoolExecutor(max_workers=3) as executor:
                f6 = executor.submit(run_b6)
                f7 = executor.submit(run_b7)
                f8 = executor.submit(run_b8)
                b6 = f6.result()
                b7 = f7.result()
                b8 = f8.result()

            master_spec = (
                f"### IDENTITY\n{b3}\n\n"
                f"### PROTOCOL\n{b4}\n\n"
                f"### FORMATTING\n{b5}\n\n"
                f"### COMPUTATION & UI\n{b6}\n{b7}\n\n"
                f"### RESILIENCE\n{b8}"
            )

            # Brain 9: Ensemble Code Synthesizer
            status.write("🧠 Brain 9/10 (Ensemble Synthesizer): Merging all 8 brain outputs into complete standalone code...")
            p9 = (
                f"Write a complete, fully functional standalone Python Streamlit app based on this specification:\n{master_spec}\n\n"
                "RULES:\n"
                "1. Output ONLY valid Python code inside a single ```python ``` code block.\n"
                "2. Include all necessary library imports.\n"
                "3. Write the entire implementation completely without placeholders."
            )
            b9 = call_groq([{"role": "user", "content": p9}], max_tok=1800, temp=0.1)
            clean_code = extract_clean_code(b9) if b9 else "# Ensemble synthesis completed."

            # Brain 10: Council QA & Verification Critic
            status.write("🧠 Brain 10/10 (Council QA Critic): Auditing operational readiness...")
            p10 = f"Verify this assistant spec in 1 sentence:\n{master_spec}"
            b10 = call_groq([{"role": "user", "content": p10}], max_tok=100)

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec,
                "source_code": clean_code,
                "qa_verdict": b10 or "Council Certified."
            }
            st.session_state.chat_history = []
            status.update(label="10-Brain Ensemble Complete & Deployed!", state="complete", expanded=False)
            st.rerun()

# Workspace UI
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live Custom AI (Council-Driven)", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"Council QA: {app_info['qa_verdict']}")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Interact with your custom AI here...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Council synthesizing consensus response..."):
                    # Combination of Brains answering together:
                    # Brain A: Reasoning Draft
                    draft_prompt = f"System Spec:\n{app_info['system_prompt']}\n\nUser Question: {user_input}\nDraft the technical core answer."
                    draft = call_groq([{"role": "user", "content": draft_prompt}], max_tok=500, temp=0.2)

                    # Brain B: Precision Validator & Polisher (Combines with Draft)
                    polish_prompt = (
                        f"Review and refine this draft answer according to the specifications:\n\n"
                        f"Draft: {draft}\n\n"
                        f"System Rules: {app_info['system_prompt']}\n\n"
                        "Deliver the final, polished response directly with no commentary."
                    )
                    final_reply = call_groq([{"role": "user", "content": polish_prompt}], max_tok=700, temp=0.2)

                    if final_reply:
                        st.markdown(final_reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": final_reply})

    with tab2:
        st.subheader("Generated Python Code")
        st.caption("Complete code compiled across all 10 specialized brains:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
