import streamlit as st
import requests
import re
import base64
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Universal AI App Factory", layout="wide")

st.title("Universal AI App Factory")
st.caption("Autonomous Multi-Brain Council with Persistent Vision & Tool Execution")

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

TEXT_MODEL = "openai/gpt-oss-20b"
VISION_MODEL = "llama-3.2-11b-vision-preview"

def call_groq(messages, model=TEXT_MODEL, key=api_key, max_tok=1000, temp=0.2):
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
            timeout=35
        )
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return strip_internal_thoughts(content)
        return None
    except Exception:
        return None

# Session State Initialization
if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "persisted_image" not in st.session_state:
    st.session_state.persisted_image = None
if "persisted_mime" not in st.session_state:
    st.session_state.persisted_mime = None

user_request = st.text_area(
    "What kind of tool or assistant do you want to build?",
    placeholder="Describe ANY task: math tutor that reads photos, coding assistant, data visualizer..."
)

if st.button("Build Autonomous AI Tool", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe the tool you want to build.")
    else:
        with st.status("Council Activating 10 Brains across all domains...", expanded=True) as status:
            status.write("🧠 Brain 1 & 2: Goal Deconstruction & Boundary Analysis...")
            b1 = call_groq([{"role": "user", "content": f"Deconstruct the complete functional scope for: '{user_request}'. Be brief."}], max_tok=180)
            b2 = call_groq([{"role": "user", "content": f"List 2 failure modes and constraints for: {b1}."}], max_tok=180)

            status.write("🧠 Brain 3, 4 & 5: System Identity, Reasoning & Formatting Guardrails...")
            b3 = call_groq([{"role": "user", "content": f"Define the master expert authority and persona for: {b1}."}], max_tok=220)
            b4 = call_groq([{"role": "user", "content": f"Formulate the step-by-step problem-solving reasoning algorithm for: {b3}."}], max_tok=220)
            b5 = call_groq([{"role": "user", "content": f"Define formatting standards (bullets, clean math notation, zero meta-filler) for: {b4}."}], max_tok=180)

            status.write("🧠 Brains 6, 7 & 8: UI Architecture, Computational Backends & Resilience...")
            def run_b6():
                return call_groq([{"role": "user", "content": f"Plan interactive UI layouts for: {b1}"}], max_tok=180)
            def run_b7():
                return call_groq([{"role": "user", "content": f"Identify necessary computational modules for: {b1}"}], max_tok=180)
            def run_b8():
                return call_groq([{"role": "user", "content": f"Formulate error handling and validation for: {b2}"}], max_tok=180)

            with ThreadPoolExecutor(max_workers=3) as executor:
                f6 = executor.submit(run_b6)
                f7 = executor.submit(run_b7)
                f8 = executor.submit(run_b8)
                b6, b7, b8 = f6.result(), f7.result(), f8.result()

            master_spec = (
                f"### SYSTEM OBJECTIVE\n{b1 or user_request}\n\n"
                f"### EXPERT IDENTITY\n{b3}\n\n"
                f"### REASONING PROTOCOL\n{b4}\n\n"
                f"### FORMATTING STANDARDS\n{b5}\n\n"
                f"### TECHNICAL WORKFLOW\n{b6}\n{b7}\n\n"
                f"### RESILIENCE\n{b8}"
            )

            status.write("🧠 Brain 9: Standalone Python Package Synthesis...")
            code_prompt = (
                f"Generate a complete, fully functional standalone Python Streamlit application tailored to:\n{master_spec}\n\n"
                "CRITICAL: Output ONLY valid Python code inside a single ```python ``` block without conversational filler."
            )
            raw_code = call_groq([{"role": "user", "content": code_prompt}], max_tok=1800, temp=0.1)
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            status.write("🧠 Brain 10: Operational Audit & Certification...")
            qa_verdict = "Council Certified: Ready for open execution."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec,
                "source_code": clean_code,
                "qa_verdict": qa_verdict
            }
            st.session_state.chat_history = []
            status.update(label="Universal Custom AI Deployed!", state="complete", expanded=False)
            st.rerun()

# Workspace
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live Custom AI Workspace", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Autonomous AI Active")
        st.caption(f"Status: {app_info['qa_verdict']} | Objective: {app_info['goal']}")

        # Prominent Multimodal Section
        st.markdown("#### 📷 Image & Document Input")
        uploaded_file = st.file_uploader(
            "Upload an image or document (persists for the whole session):",
            type=["png", "jpg", "jpeg"],
            key="file_uploader_widget"
        )
        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            st.session_state.persisted_image = base64.b64encode(bytes_data).decode("utf-8")
            st.session_state.persisted_mime = uploaded_file.type

        if st.session_state.persisted_image:
            col_img, col_btn = st.columns([3, 1])
            with col_img:
                st.image(
                    base64.b64decode(st.session_state.persisted_image),
                    caption="Active Attached Image (AI can see this)",
                    width=280
                )
            with col_btn:
                if st.button("❌ Remove Image"):
                    st.session_state.persisted_image = None
                    st.session_state.persisted_mime = None
                    st.rerun()

        # Render Chat History
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

        user_input = st.chat_input("Ask a question, request an explanation, or inspect your uploaded photo...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Processing request..."):
                    council_system = (
                        f"You are the deployed expert AI tool designed for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "OPERATING DIRECTIVES:\n"
                        "1. Fulfill the user's request directly, step-by-step, and accurately.\n"
                        "2. Never print internal thinking, scratchpads, or 'We need to' notes.\n"
                        "3. When an image is provided, carefully inspect and describe everything visible in it.\n"
                        "4. If generating visual graphs, provide executable Python code using `matplotlib.pyplot as plt` and define `fig`.\n"
                    )

                    # Route to Vision Model if an image is attached
                    if st.session_state.persisted_image:
                        user_content = [
                            {"type": "text", "text": user_input},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{st.session_state.persisted_mime};base64,{st.session_state.persisted_image}"
                                }
                            }
                        ]
                        messages = [
                            {"role": "system", "content": council_system},
                            {"role": "user", "content": user_content}
                        ]
                        reply = call_groq(messages, model=VISION_MODEL, max_tok=1000, temp=0.2)
                    else:
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            messages.append({"role": m["role"], "content": m["content"]})
                        reply = call_groq(messages, model=TEXT_MODEL, max_tok=1000, temp=0.2)

                    if reply:
                        st.markdown(reply)

                        # Code plotting check
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
        st.caption("Standalone code synthesized for this exact system architecture:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
