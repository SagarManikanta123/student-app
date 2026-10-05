import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import base64
import urllib.parse
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Universal AI Factory (Mega Rayquaza Core)", layout="wide")

st.markdown("""
<style>
    .rayquaza-header {
        background: linear-gradient(90deg, #064e3b, #047857, #d97706);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.2rem;
        font-weight: 800;
        margin-bottom: 0px;
    }
    .apex-badge {
        background-color: #065f46;
        color: #fde047;
        padding: 4px 10px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #d97706;
        display: inline-block;
        margin-bottom: 12px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="rayquaza-header">Universal AI Factory: 21-Brain Council</p>', unsafe_allow_html=True)
st.markdown('<span class="apex-badge">🐉 Inner Core: Mega Rayquaza (Apex Governor & Delta Stream Engine)</span>', unsafe_allow_html=True)
st.caption("Build custom AIs using Voice Dictation or Text. Features real image generation, Matplotlib plotting, and visual inspection.")

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

# In-browser microphone component reusable across sections
def render_voice_button(element_id="factoryMic", label="Speak Your AI Design"):
    mic_html = f"""
    <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 6px;">
        <button id="{element_id}_btn" style="
            background: linear-gradient(90deg, #059669, #d97706);
            color: white;
            border: none;
            padding: 8px 16px;
            border-radius: 6px;
            cursor: pointer;
            font-weight: bold;
            display: inline-flex;
            align-items: center;
            gap: 6px;">
            🎤 {label}
        </button>
        <div id="{element_id}_box" style="
            font-size: 13px;
            color: #d1d5db;
            background: #1f2937;
            padding: 8px;
            border-radius: 6px;
            min-height: 38px;
            border: 1px solid #059669;">Click microphone and talk (automatically copies speech to clipboard)...</div>
    </div>

    <script>
    const btn = document.getElementById('{element_id}_btn');
    const box = document.getElementById('{element_id}_box');
    let recognizing = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SpeechRecognition = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recognition = new SpeechRecognition();
        recognition.continuous = false;
        recognition.interimResults = true;

        recognition.onstart = function() {{
            recognizing = true;
            btn.innerText = "🛑 Stop & Copy";
            btn.style.background = "#10b981";
            box.innerText = "Listening...";
        }};

        recognition.onresult = function(event) {{
            let text = '';
            for (let i = event.resultIndex; i < event.results.length; ++i) {{
                text += event.results[i][0].transcript;
            }}
            box.innerText = text;
            navigator.clipboard.writeText(text);
        }};

        recognition.onerror = function(event) {{
            box.innerText = "Mic error: " + event.error;
            recognizing = false;
            btn.innerText = "🎤 {label}";
            btn.style.background = "linear-gradient(90deg, #059669, #d97706)";
        }};

        recognition.onend = function() {{
            recognizing = false;
            btn.innerText = "🎤 {label} (Copied to Clipboard!)";
            btn.style.background = "linear-gradient(90deg, #059669, #d97706)";
        }};

        btn.onclick = function() {{
            if (recognizing) {{
                recognition.stop();
            }} else {{
                recognition.start();
            }}
        }};
    }} else {{
        box.innerText = "Web Speech API not supported in this browser. Please use Chrome/Edge.";
        btn.disabled = true;
    }}
    </script>
    """
    components.html(mic_html, height=95)

# State Initialization
if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "persisted_image_b64" not in st.session_state:
    st.session_state.persisted_image_b64 = None
if "persisted_image_mime" not in st.session_state:
    st.session_state.persisted_image_mime = None

# AI FACTORY CREATOR SECTION WITH VOICE COMMAND
st.subheader("1. AI Factory Creator (Voice or Text)")
col_creator_text, col_creator_mic = st.columns([2, 1])

with col_creator_mic:
    st.write("🎙️ **Voice Command to Build AI**")
    render_voice_button(element_id="factory_creator_mic", label="Speak What AI to Build")

with col_creator_text:
    user_request = st.text_area(
        "Describe or paste the AI tool you want the factory to create:",
        placeholder="e.g. Build an AI tutor that can explain circuits, solve math, draw graphs, and generate diagrams.",
        height=100
    )

if st.button("Deploy AI with Mega Rayquaza Inner Core", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe what tool you want to create (speak via microphone or type above).")
    else:
        with st.status("Awakening Mega Rayquaza & The 21-Brain Council...", expanded=True) as status:
            status.write("🐉 Channeling the Delta Stream: Harmonizing 21 specialized brains...")
            
            council_synthesis_prompt = (
                f"You are the Mega Rayquaza Core — the legendary apex intelligence presiding over the 21-Brain Council. "
                f"A creator commands the deployment of an assistant designed for: '{user_request}'.\n\n"
                "Command the full 21 departments into perfect alignment:\n"
                "1. Inner Apex Core: Mega Rayquaza (Supreme Speed, Global Coherence, Unstoppable Problem Solving)\n"
                "2. Hardware & Electronics Specialist (Circuits, Arduino, Microcontrollers, Pinouts)\n"
                "3. Vision & Diagram Inspector (OCR, High-Resolution Circuit & Photo Analysis)\n"
                "4. Pure & Applied Mathematics Brain (Algebra, Calculus, Precise Step-by-Step Proofs)\n"
                "5. Theoretical & Classical Physics Engine (Kinematics, Electromagnetism, Forces)\n"
                "6. Chemistry Specialist (Reactions, Balancing, Molecules)\n"
                "7. Computer Science & Algorithm Engine\n"
                "8. Software Engineering Brain\n"
                "9. Microcontroller Firmware Specialist\n"
                "10. Life Sciences & Bioengineering Brain\n"
                "11. Statistical Modeling Brain\n"
                "12. Dynamic Visualizer & Graph Plotter\n"
                "13. Image Generation Prompt Specialist\n"
                "14. Voice & Audio Interaction Specialist\n"
                "15. Creative Analogy Architect\n"
                "16. Pedagogical Manners Brain\n"
                "17. History & Civics Brain\n"
                "18. Linguistics Specialist\n"
                "19. Edge Case & Failure Analyst\n"
                "20. Code Verification Brain\n"
                "21. Universal Multi-Disciplinary Synthesizer\n\n"
                "OPERATIONAL OUTPUT RULES:\n"
                "- Speak with decisive clarity, supreme competence, and encouraging polite tone.\n"
                "- If the user asks to GENERATE AN IMAGE, DRAW A PICTURE, or CREATE ART: Describe what is created, then on the very last line output: `IMAGE_PROMPT: <vivid visual description in English>`\n"
                "- If the user asks to DRAW A MATHEMATICAL GRAPH: Explain the math, then provide executable plotting code with matplotlib.pyplot as plt and numpy as np defining fig inside a python code block.\n"
                "- Never dump raw code unless the user explicitly requested code."
            )
            
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1100,
                temp=0.4
            )

            status.write("Compiling standalone production code under Apex supervision...")
            code_prompt = (
                f"Write a standalone Streamlit Python app implementing this directive:\n{master_system_prompt}\n\n"
                "Output ONLY executable Python code inside a single markdown code block with python tag."
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
            status.update(label="AI Tool Created & Deployed Successfully!", state="complete", expanded=False)
            st.rerun()

# CREATED AI WORKSPACE SECTION
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live Custom AI Workspace", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("2. Your Active Custom AI")
        st.caption(f"Council Objective: {app_info['goal']} | Inner Core: Mega Rayquaza Activated")

        # Media & Voice Controls inside the Created Tool
        st.markdown("#### 🎙️ Media & Voice Interaction")
        col_up, col_chat_mic = st.columns([2, 1])

        with col_up:
            uploaded_file = st.file_uploader(
                "Upload photo, diagram, circuit, or document:",
                type=["png", "jpg", "jpeg"],
                key="workspace_file_input"
            )
            if uploaded_file is not None:
                bytes_data = uploaded_file.getvalue()
                if len(bytes_data) > 0:
                    st.session_state.persisted_image_b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.session_state.persisted_image_mime = uploaded_file.type

        with col_chat_mic:
            st.write("🎙️ **Voice Command to Chat with AI**")
            render_voice_button(element_id="chat_interaction_mic", label="Speak Question to AI")

        if st.session_state.get("persisted_image_b64"):
            st.success("🐉 Mega Rayquaza Vision Core locked onto image.")
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

        # Render conversation history with images, graphs & text
        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                if msg.get("text_content"):
                    st.markdown(msg["text_content"])
                
                if msg.get("image_url"):
                    st.image(msg["image_url"], caption="Generated via Mega Rayquaza Visual Core", use_container_width=True)
                
                if msg.get("plot_code"):
                    try:
                        exec_env = {"np": np, "plt": plt}
                        exec(msg["plot_code"], exec_env)
                        fig = exec_env.get("fig") or plt.gcf()
                        st.pyplot(fig)
                        plt.clf()
                    except Exception:
                        pass

        # Chat Input Bar
        user_input = st.chat_input("Speak via mic above (it auto-copies), paste, or type your question here...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Mega Rayquaza Inner Core harmonizing council response..."):
                    council_system = (
                        f"You are the deployed expert AI system created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "OPERATIONAL DIRECTIVES:\n"
                        "1. Answer with supreme confidence, crystal clarity, and polite pedagogical authority.\n"
                        "2. IF THE USER ASKS TO GENERATE AN IMAGE, PICTURE, OR ART: Describe the concept, then on the last line output: `IMAGE_PROMPT: <vivid visual description in English>`\n"
                        "3. IF DRAWING A GRAPH OR PLOTTING AN EQUATION: Explain the math, then provide executable plotting code with matplotlib.pyplot as plt and numpy as np defining fig inside a python code block.\n"
                        "4. Never output internal thoughts or planning notes."
                    )

                    img_b64 = st.session_state.get("persisted_image_b64")
                    img_mime = st.session_state.get("persisted_image_mime", "image/png")

                    if img_b64:
                        user_content = [
                            {"type": "text", "text": user_input},
                            {
                                "type": "image_url",
                                "image_url": {
                                    "url": f"data:{img_mime};base64,{img_b64}"
                                }
                            }
                        ]
                        messages = [
                            {"role": "system", "content": council_system},
                            {"role": "user", "content": user_content}
                        ]
                        reply = call_groq(messages, model=PRIMARY_VISION_MODEL, max_tok=1200, temp=0.4)
                    else:
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            if m.get("text_content"):
                                messages.append({"role": m["role"], "content": m["text_content"]})
                        reply = call_groq(messages, model=PRIMARY_TEXT_MODEL, max_tok=1400, temp=0.4)

                    if reply:
                        image_url = None
                        img_prompt_match = re.search(r"IMAGE_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                        if img_prompt_match:
                            raw_prompt = img_prompt_match.group(1).strip()
                            clean_prompt = re.sub(r"[^\w\s,.-]", "", raw_prompt)
                            encoded_prompt = urllib.parse.quote(clean_prompt[:250])
                            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&nologo=true"

                        plot_match = re.search(r"```(?:python)?\s*(.*?fig\s*=.*?)\s*```", reply, re.DOTALL)
                        plot_code = plot_match.group(1) if plot_match else None

                        cleaned_text = re.sub(r"IMAGE_PROMPT:\s*.+", "", reply, flags=re.IGNORECASE)
                        cleaned_text = re.sub(r"```(?:python)?\s*.*?fig\s*=.*?\s*```", "", cleaned_text, flags=re.DOTALL).strip()

                        if cleaned_text:
                            st.markdown(cleaned_text)

                        if image_url:
                            st.image(image_url, caption="Generated via Mega Rayquaza Visual Core", use_container_width=True)

                        if plot_code:
                            try:
                                exec_env = {"np": np, "plt": plt}
                                exec(plot_code, exec_env)
                                fig = exec_env.get("fig") or plt.gcf()
                                st.pyplot(fig)
                                plt.clf()
                            except Exception as err:
                                st.caption(f"(Graph rendering error: {err})")

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "text_content": cleaned_text,
                            "image_url": image_url,
                            "plot_code": plot_code
                        })

    with tab2:
        st.subheader("Generated Python Code")
        st.caption("Complete code compiled across all 21 specialist brains:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
