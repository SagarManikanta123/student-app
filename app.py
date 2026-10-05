import streamlit as st
import requests
import re
import base64
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="20-Brain Mega-Council Factory", layout="wide")

st.title("Universal AI Factory (20-Specialist Council)")
st.caption("Now with Active Graph Rendering & Vector Diagram Generation")

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

PRIMARY_TEXT_MODEL = "openai/gpt-oss-120b"
BACKUP_TEXT_MODEL = "openai/gpt-oss-20b"
PRIMARY_VISION_MODEL = "qwen/qwen3.8-27b"
BACKUP_VISION_MODEL = "llama-3.2-11b-vision-preview"

def call_groq(messages, model=PRIMARY_TEXT_MODEL, key=api_key, max_tok=1400, temp=0.4):
    clean_k = sanitize_text(key)
    headers = {
        "Authorization": f"Bearer {clean_k}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0"
    }

    models_to_try = [model]
    if model == PRIMARY_TEXT_MODEL:
        models_to_try.append(BACKUP_TEXT_MODEL)
    elif model == PRIMARY_VISION_MODEL:
        models_to_try.append(BACKUP_VISION_MODEL)

    last_error = ""
    for candidate in models_to_try:
        payload = {
            "model": candidate,
            "messages": messages,
            "temperature": temp,
            "max_tokens": max_tok
        }
        try:
            res = requests.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=40
            )
            if res.status_code == 200:
                msg = res.json()["choices"][0]["message"]
                content = msg.get("content") or msg.get("reasoning") or ""
                return strip_internal_thoughts(content)
            else:
                last_error = f"API Error ({res.status_code}): {res.text}"
        except Exception as exc:
            last_error = f"Request failed: {exc}"
            
    return last_error

# State Initialization
if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "persisted_image_b64" not in st.session_state:
    st.session_state.persisted_image_b64 = None
if "persisted_image_mime" not in st.session_state:
    st.session_state.persisted_image_mime = None

user_request = st.text_area(
    "What kind of AI tool do you want to create?",
    placeholder="e.g. Build an AI that can draw mathematical graphs, render diagrams, inspect hardware photos, and explain concepts simply."
)

if st.button("Deploy 20-Brain Mega-Council", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe what tool you want to create.")
    else:
        with st.status("Concurring 20-Brain Mega-Council...", expanded=True) as status:
            status.write("🧠 Synthesizing 20-department operational directive...")
            
            council_synthesis_prompt = (
                f"You are the Supreme Council Moderator. Build the operational prompt for: '{user_request}'.\n\n"
                "Incorporate all 20 domains:\n"
                "1. Hardware & Electronics Specialist\n"
                "2. Vision & Diagram Inspector\n"
                "3. Pure & Applied Mathematics Brain\n"
                "4. Theoretical & Classical Physics Engine\n"
                "5. Chemistry Specialist\n"
                "6. Computer Science & Algorithm Engine\n"
                "7. Software Engineering Brain\n"
                "8. Microcontroller Firmware Specialist\n"
                "9. Life Sciences Brain\n"
                "10. Statistical Modeling Brain\n"
                "11. Dynamic Visualizer & Graph Plotter\n"
                "12. Creative Analogy Architect\n"
                "13. Pedagogical Manners Brain\n"
                "14. History & Civics Brain\n"
                "15. Linguistics Specialist\n"
                "16. Edge Case & Failure Analyst\n"
                "17. Code Verification Brain\n"
                "18. Visual Renderer Engine (SVG & Matplotlib)\n"
                "19. Universal Cross-Disciplinary Tutor\n"
                "20. Council Moderator\n\n"
                "CRITICAL OUTPUT RULES:\n"
                "- If the user asks to DRAW, PLOT, or GRAPH an equation, explain the equation first, then supply a Python block with `plt.figure()` and `plt.plot()` defining `fig` at the very end.\n"
                "- If the user asks to GENERATE AN IMAGE, DIAGRAM, or ILLUSTRATION, supply a valid, clean SVG vector illustration enclosed inside an ```xml ``` block.\n"
                "- Never show raw code explanations unless the word 'code' was explicitly requested."
            )
            
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1100,
                temp=0.4
            )

            status.write("🧠 Compiling standalone production code...")
            code_prompt = (
                f"Write a standalone Streamlit Python app implementing this directive:\n{master_system_prompt}\n\n"
                "Output ONLY executable Python code inside a single ```python ``` code block."
            )
            raw_code = call_groq(
                [{"role": "user", "content": code_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1600,
                temp=0.1
            )
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_system_prompt,
                "source_code": clean_code
            }
            st.session_state.chat_history = []
            status.update(label="20-Brain Mega-Council Deployed!", state="complete", expanded=False)
            st.rerun()

# Workspace UI
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live 20-Brain Council Workspace", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Autonomous Mega-Council Active")
        st.caption(f"Council Objective: {app_info['goal']}")

        st.markdown("#### 📷 Image & Media Input")
        uploaded_file = st.file_uploader(
            "Upload an image, diagram, circuit photo, or document:",
            type=["png", "jpg", "jpeg"],
            key="mega_20_file_input"
        )

        if uploaded_file is not None:
            bytes_data = uploaded_file.getvalue()
            if len(bytes_data) > 0:
                st.session_state.persisted_image_b64 = base64.b64encode(bytes_data).decode("utf-8")
                st.session_state.persisted_image_mime = uploaded_file.type

        if st.session_state.get("persisted_image_b64"):
            st.success("✅ Image loaded into Vision Brain memory.")
            col_img, col_btn = st.columns([3, 1])
            with col_img:
                st.image(
                    base64.b64decode(st.session_state.persisted_image_b64),
                    caption="Active Attached Image",
                    width=280
                )
            with col_btn:
                if st.button("❌ Remove Image"):
                    st.session_state.persisted_image_b64 = None
                    st.session_state.persisted_image_mime = None
                    st.rerun()

        # Render conversation history with graphs & SVG diagrams
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if msg.get("text_content"):
                    st.markdown(msg["text_content"])
                
                # Render SVG image if generated
                if msg.get("svg_content"):
                    st.markdown(msg["svg_content"], unsafe_allow_html=True)
                
                # Render Python Matplotlib Plot if generated
                if msg.get("plot_code"):
                    try:
                        exec_env = {"np": np, "plt": plt}
                        exec(msg["plot_code"], exec_env)
                        fig = exec_env.get("fig") or plt.gcf()
                        st.pyplot(fig)
                        plt.clf()
                    except Exception:
                        pass

        user_input = st.chat_input("Ask a question, request a graph (e.g. plot y^2=4ax), or ask for a diagram...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Council analyzing and generating visual output..."):
                    council_system = (
                        f"You are the deployed expert AI system created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "OPERATIONAL DIRECTIVES:\n"
                        "1. Answer in clear, polite English with intuitive explanations.\n"
                        "2. IF DRAWING A GRAPH OR EQUATION: Provide the mathematical explanation first. At the very end, provide ONLY executable plotting code using `matplotlib.pyplot as plt` and `numpy as np` defining a figure variable named `fig` inside a ```python ``` code block.\n"
                        "3. IF GENERATING A DIAGRAM OR IMAGE: Output an inline SVG XML representation inside an ```xml
