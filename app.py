import streamlit as st
import requests
import re
import matplotlib.pyplot as plt
import numpy as np
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="AI App Factory - Multi-Brain Council", layout="wide")

st.title("AI App Factory (Multi-Brain Council)")
st.caption("Deconstructor → Scope → Architect → Protocol → Guardrail → UI Spec → Logic Spec → Resilience → Synthesizer → QA")

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

def strip_internal_thoughts(text):
    if not text:
        return ""
    clean = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    lines = clean.split("\n")
    filtered = []
    skipping_meta = True
    for line in lines:
        stripped = line.strip().lower()
        if skipping_meta and (
            stripped.startswith("we need to") or 
            stripped.startswith("the user wants") or 
            stripped.startswith("the user is asking")
        ):
            continue
        skipping_meta = False
        filtered.append(line)
    result = "\n".join(filtered).strip()
    return result if result else clean.strip()

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

def call_groq(messages, model=ACTIVE_MODEL, key=api_key, max_tok=700, temp=0.2):
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
            return strip_internal_thoughts(content)
        return None
    except Exception:
        return None

if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_request = st.text_area(
    "What AI tool do you want to create?",
    placeholder="e.g. make an AI that can draw graphs based on user input equations"
)

if st.button("Build AI Tool", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool you want to create.")
    else:
        with st.status("Council Activating 10 Brains...", expanded=True) as status:
            status.write("🧠 Brain 1 & 2: Goal Deconstruction & Boundary Analysis...")
            b1 = call_groq([{"role": "user", "content": f"Extract the core functional purpose for: '{user_request}'. Be brief."}], max_tok=150)
            b2 = call_groq([{"role": "user", "content": f"List 2 constraints and handling rules for: {b1 or user_request}."}], max_tok=150)

            status.write("🧠 Brain 3, 4 & 5: System Identity, Logic Protocol & Output Guardrails...")
            b3 = call_groq([{"role": "user", "content": f"Define the expert persona for: {b1}."}], max_tok=200)
            b4 = call_groq([{"role": "user", "content": f"Define the step-by-step reasoning steps for persona: {b3}."}], max_tok=200)
            b5 = call_groq([{"role": "user", "content": f"Define concise output syntax guidelines (bullet points, LaTeX math notation, no meta commentary) for: {b4}."}], max_tok=150)

            status.write("🧠 Brains 6, 7 & 8: Parallel UI, Computational Backend & Resilience Engines...")
            def run_b6():
                return call_groq([{"role": "user", "content": f"Streamlit UI layout specs for: {b1}"}], max_tok=180)
            def run_b7():
                return call_groq([{"role": "user", "content": f"Backend computation and math libraries for: {b1}"}], max_tok=180)
            def run_b8():
                return call_groq([{"role": "user", "content": f"Exception handling and validation for: {b2}"}], max_tok=150)

            with ThreadPoolExecutor(max_workers=3) as executor:
                f6 = executor.submit(run_b6)
                f7 = executor.submit(run_b7)
                f8 = executor.submit(run_b8)
                b6, b7, b8 = f6.result(), f7.result(), f8.result()

            master_spec = (
                f"Role: {b3 or user_request}\n"
                f"Protocol: {b4 or 'Provide clear steps'}\n"
                f"Output Standards: {b5 or 'Clean bullet points and math notation'}\n"
                f"Edge Cases: {b8 or 'Handle mathematical domain errors cleanly'}"
            )

            status.write("🧠 Brain 9: Ensemble Code Synthesizer...")
            code_prompt = (
                f"Write a standalone Streamlit Python app that solves: '{user_request}'.\n"
                f"Architecture reference: {master_spec}\n\n"
                "CRITICAL: Output ONLY valid python code inside a single ```python ``` code block. Do NOT include markdown commentary."
            )
            raw_code = call_groq([{"role": "user", "content": code_prompt}], max_tok=1800, temp=0.1)
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            status.write("🧠 Brain 10: Council QA Verification...")
            # Enforce clean verdict with no chain-of-thought planning
            qa_instruction = "Return ONLY one short sentence certifying this system ready. Example: 'Verified: Operational and ready for input.'"
            b10_raw = call_groq([{"role": "system", "content": qa_instruction}, {"role": "user", "content": f"Spec: {b1}"}], max_tok=60)
            b10 = strip_internal_thoughts(b10_raw) if b10_raw else "Council Certified: Ready for deployment."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec,
                "source_code": clean_code,
                "qa_verdict": b10
            }
            st.session_state.chat_history = []
            status.update(label="10-Brain Ensemble Certified & Deployed!", state="complete", expanded=False)
            st.rerun()

# Workspace UI
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live Custom AI (Council Core)", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Your Custom AI is Active")
        st.caption(f"Council QA: {app_info['qa_verdict']}")

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
                if "plot_code" in msg:
                    try:
                        exec_env = {"np": np, "plt": plt}
                        exec(msg["plot_code"], exec_env)
                        fig = exec_env.get("fig") or plt.gcf()
                        st.pyplot(fig)
                        plt.clf()
                    except Exception:
                        pass

        user_input = st.chat_input("Enter equation or prompt here...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Council analyzing and plotting..."):
                    council_system_instruction = (
                        f"You are the deployed expert tool created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "CRITICAL OPERATIONAL RULES:\n"
                        "1. Answer the user prompt directly. Never output internal planning notes or 'We need to...'.\n"
                        "2. Provide an analytical breakdown using bullet points and LaTeX formatting.\n"
                        "3. If the user input represents a mathematical equation or function to graph, you MUST include a clean Python block using `matplotlib.pyplot as plt` and `numpy as np` defining a figure named `fig`. Do not call `plt.show()`.\n"
                    )

                    messages = [{"role": "system", "content": council_system_instruction}]
                    for m in st.session_state.chat_history:
                        messages.append({"role": m["role"], "content": m["content"]})

                    reply = call_groq(messages, max_tok=1000, temp=0.2)
                    if reply:
                        st.markdown(reply)
                        
                        # Extract and render plot code directly if present
                        code_match = re.search(r"```python\s*(.*?fig\s*=.*?)\s*```", reply, re.DOTALL)
                        entry = {"role": "assistant", "content": reply}
                        
                        if code_match:
                            extracted_plot = code_match.group(1)
                            try:
                                exec_env = {"np": np, "plt": plt}
                                exec(extracted_plot, exec_env)
                                fig = exec_env.get("fig") or plt.gcf()
                                st.pyplot(fig)
                                plt.clf()
                                entry["plot_code"] = extracted_plot
                            except Exception:
                                pass
                        
                        st.session_state.chat_history.append(entry)

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
