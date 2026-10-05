import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import base64
import urllib.parse
import io
import json
import numpy as np
import matplotlib.pyplot as plt
import qrcode
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pypdf import PdfReader

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

st.markdown('<p class="rayquaza-header">Universal AI Factory: 26-Brain Council</p>', unsafe_allow_html=True)
st.markdown('<span class="apex-badge">🐉 Inner Core: Mega Rayquaza (Apex Governor with QR, Doc Intake, Video, PPTX & PDF)</span>', unsafe_allow_html=True)
st.caption("Voice Dictation, Document Intake (.pdf, .txt, .csv), QR Code Generator, Real-Time Video/Image, Matplotlib Graphing & Slide Decks.")

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

def build_pdf_bytes(title, content):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, text=title[:80], new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)
    
    clean_content = "".join(c for c in content if ord(c) < 256)
    for paragraph in clean_content.split("\n"):
        if paragraph.strip():
            pdf.multi_cell(0, 7, text=paragraph.strip())
            pdf.ln(2)
    return bytes(pdf.output())

def build_pptx_bytes(presentation_data):
    prs = Presentation()
    for slide_info in presentation_data.get("slides", []):
        slide = prs.slides.add_slide(prs.slide_layouts[1])
        title = slide.shapes.title
        body = slide.placeholders[1]
        
        title.text = slide_info.get("title", "Untitled Slide")
        tf = body.text_frame
        tf.word_wrap = True
        
        bullets = slide_info.get("bullets", [])
        if bullets:
            tf.text = bullets[0]
            for bullet in bullets[1:]:
                p = tf.add_paragraph()
                p.text = bullet
                p.level = 0
    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()

def build_qr_bytes(payload_data):
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_M,
        box_size=10,
        border=3
    )
    qr.add_data(payload_data)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def extract_document_text(uploaded_file):
    try:
        filename = uploaded_file.name.lower()
        if filename.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            extracted = []
            for i, page in enumerate(reader.pages[:25]): # Read up to 25 pages safely
                text = page.extract_text()
                if text:
                    extracted.append(f"--- Page {i+1} ---\n" + text)
            return "\n\n".join(extracted)
        elif filename.endswith((".txt", ".csv", ".md")):
            return uploaded_file.getvalue().decode("utf-8", errors="replace")
    except Exception as exc:
        return f"[Error parsing document: {exc}]"
    return "[Unsupported file format]"

def fetch_media_bytes(url, timeout=35):
    try:
        resp = requests.get(url, timeout=timeout)
        content_type = resp.headers.get("content-type", "")
        if resp.status_code == 200 and len(resp.content) > 10000 and "html" not in content_type:
            return resp.content, content_type
    except Exception:
        pass
    return None, None

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
if "persisted_document_text" not in st.session_state:
    st.session_state.persisted_document_text = None
if "persisted_document_name" not in st.session_state:
    st.session_state.persisted_document_name = None

if "ai_creativity" not in st.session_state:
    st.session_state.ai_creativity = 0.5
if "ai_max_tokens" not in st.session_state:
    st.session_state.ai_max_tokens = 1400
if "ai_custom_trait" not in st.session_state:
    st.session_state.ai_custom_trait = (
        "Articulate, polite, visually rich. "
        "Supports document reading, QR code generation, video prompts, slide decks, and graph plotting."
    )

# SECTION 1: AI FACTORY CREATOR
st.subheader("1. AI Factory Creator (Voice or Text)")
col_creator_text, col_creator_mic = st.columns([2, 1])

with col_creator_mic:
    st.write("🎙️ **Voice Command to Build AI**")
    render_voice_button(element_id="factory_creator_mic", label="Speak What AI to Build")

with col_creator_text:
    user_request = st.text_area(
        "Describe or paste the AI tool you want the factory to create:",
        placeholder="e.g. Build an AI assistant with document intake (.pdf/.txt), QR code generation, video creation, slides, and math graphs.",
        height=100
    )

if st.button("Deploy AI with Mega Rayquaza Inner Core", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe what tool you want to create (speak via microphone or type above).")
    else:
        with st.status("Awakening Mega Rayquaza & The 26-Brain Council...", expanded=True) as status:
            status.write("🐉 Channeling the Delta Stream: Harmonizing 26 specialized brains...")
            
            council_synthesis_prompt = (
                f"You are the Mega Rayquaza Core — the apex intelligence presiding over the 26-Brain Council. "
                f"A creator commands the deployment of an assistant designed for: '{user_request}'.\n\n"
                "Command all 26 departments into alignment:\n"
                "1. Inner Apex Core: Mega Rayquaza\n"
                "2. Hardware & Electronics Specialist (Circuits, Microcontrollers, Pinouts)\n"
                "3. Vision & Diagram Inspector (OCR, Image Parsing)\n"
                "4. Pure & Applied Mathematics Brain (Proofs, Calculus, Algebra)\n"
                "5. Theoretical & Classical Physics Engine (Kinematics, Electromagnetism)\n"
                "6. Chemistry Specialist (Reactions, Balancing)\n"
                "7. Computer Science & Algorithm Engine\n"
                "8. Software Engineering Brain\n"
                "9. Microcontroller Firmware Specialist\n"
                "10. Life Sciences & Biology Brain\n"
                "11. Statistical Modeling Brain\n"
                "12. Dynamic Visualizer & Graph Plotter\n"
                "13. Motion & Video Generation Specialist\n"
                "14. Still Image Generation Prompt Specialist\n"
                "15. Voice & Audio Interaction Specialist\n"
                "16. Document & PDF Report Compiler (Exporting PDFs)\n"
                "17. Executive Slide Deck & PPTX Architect\n"
                "18. Multi-Format Document Intake Specialist (Brain 25: Reading uploaded PDFs/TXT/CSV)\n"
                "19. Barcode & QR Code Serialization Engine (Brain 26: Generating functional QR Codes)\n"
                "20. Creative Analogy Architect\n"
                "21. Pedagogical Manners Brain\n"
                "22. History & Civics Brain\n"
                "23. Linguistics Specialist\n"
                "24. Edge Case & Failure Analyst\n"
                "25. Code Verification Brain\n"
                "26. Universal Multi-Disciplinary Synthesizer\n\n"
                "OPERATIONAL OUTPUT RULES:\n"
                "- If the user asks to GENERATE A QR CODE: Confirm the content, then on the last line output: `GENERATE_QR: <raw URL, contact info, or text to encode>`\n"
                "- If an uploaded document is present: Cite specific details, summarize, answer questions accurately, and analyze the document content directly.\n"
                "- If the user requests a VIDEO or animation: Describe the scene, then on the last line output: `VIDEO_PROMPT: <detailed motion description>`\n"
                "- If the user requests an IMAGE: Describe it, then on the last line output: `IMAGE_PROMPT: <visual prompt>`\n"
                "- If the user requests a PPT/SLIDES: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                "- If the user requests a PDF/REPORT: Write the document, then finish with: `GENERATE_PDF: <Title>`.\n"
                "- If DRAWING A GRAPH: Supply executable code using `matplotlib.pyplot as plt` and `numpy as np` defining `fig` inside a python code block.\n"
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

# SECTION 2: CREATED AI WORKSPACE
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["⚡ Live Custom AI Workspace", "🛠️ Edit AI Characteristics", "📄 Standalone Code (.py)"])

    # TAB 2: LIVE CHARACTERISTICS & BEHAVIOR EDITOR
    with tab2:
        st.subheader("Customize & Tune AI Characteristics")
        st.caption("Change how your created AI behaves without rebuilding from scratch.")

        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.session_state.ai_creativity = st.slider(
                "Creativity Level (Temperature)",
                min_value=0.0,
                max_value=1.0,
                value=float(st.session_state.ai_creativity),
                step=0.05
            )
        with col_c2:
            st.session_state.ai_max_tokens = st.slider(
                "Maximum Response Length (Tokens)",
                min_value=400,
                max_value=2500,
                value=int(st.session_state.ai_max_tokens),
                step=100
            )

        st.session_state.ai_custom_trait = st.text_area(
            "Persona, Tone & Specific Characteristic Instructions:",
            value=st.session_state.ai_custom_trait
        )

        app_info["system_prompt"] = st.text_area(
            "Council Operational Directives (Direct Prompt Edit):",
            value=app_info["system_prompt"],
            height=180
        )
        st.success("✅ Characteristics auto-saved! Next prompts will utilize these updated behaviors.")

    # TAB 1: WORKSPACE
    with tab1:
        st.subheader("2. Your Active Custom AI")
        st.caption(f"Council Objective: {app_info['goal']} | Inner Core: Mega Rayquaza Activated")

        # Media, Document Intake & Voice Controls
        st.markdown("#### 📁 File Uploads, Document Intake & Voice Input")
        col_up_img, col_up_doc, col_chat_mic = st.columns([1.5, 1.5, 1.2])

        with col_up_img:
            uploaded_image = st.file_uploader(
                "📷 Upload Photo / Circuit / Diagram:",
                type=["png", "jpg", "jpeg"],
                key="workspace_image_input"
            )
            if uploaded_image is not None:
                bytes_data = uploaded_image.getvalue()
                if len(bytes_data) > 0:
                    st.session_state.persisted_image_b64 = base64.b64encode(bytes_data).decode("utf-8")
                    st.session_state.persisted_image_mime = uploaded_image.type

        with col_up_doc:
            uploaded_doc = st.file_uploader(
                "📄 Upload Document Intake (.pdf, .txt, .csv):",
                type=["pdf", "txt", "csv", "md"],
                key="workspace_doc_input"
            )
            if uploaded_doc is not None:
                doc_text = extract_document_text(uploaded_doc)
                st.session_state.persisted_document_text = doc_text
                st.session_state.persisted_document_name = uploaded_doc.name

        with col_chat_mic:
            st.write("🎙️️ **Voice Command to Chat**")
            render_voice_button(element_id="chat_interaction_mic", label="Speak Question to AI")

        # Active File Indicators
        col_stat1, col_stat2 = st.columns(2)
        with col_stat1:
            if st.session_state.get("persisted_image_b64"):
                st.success("📷 Vision Brain: Image loaded.")
                col_i, col_b = st.columns([3, 1])
                with col_i:
                    st.image(base64.b64decode(st.session_state.persisted_image_b64), width=180)
                with col_b:
                    if st.button("❌ Remove Image"):
                        st.session_state.persisted_image_b64 = None
                        st.session_state.persisted_image_mime = None
                        st.rerun()

        with col_stat2:
            if st.session_state.get("persisted_document_text"):
                doc_preview = st.session_state.persisted_document_text[:120].replace("\n", " ")
                st.info(f"📄 **Intake Active:** {st.session_state.persisted_document_name} ({len(st.session_state.persisted_document_text)} chars)")
                if st.button("❌ Clear Document Intake"):
                    st.session_state.persisted_document_text = None
                    st.session_state.persisted_document_name = None
                    st.rerun()

        # Render conversation history with unique keys
        for idx, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                if msg.get("text_content"):
                    st.markdown(msg["text_content"])
                
                # Render Generated QR Code
                if msg.get("qr_bytes"):
                    st.image(msg["qr_bytes"], caption="Scannable QR Code", width=220)
                    st.download_button(
                        "📥 Download QR Code (.png)",
                        data=msg["qr_bytes"],
                        file_name="qrcode.png",
                        mime="image/png",
                        key=f"dl_qr_btn_{idx}"
                    )

                # Render verified video/animation
                if msg.get("video_bytes"):
                    st.video(msg["video_bytes"])
                elif msg.get("visual_url"):
                    st.image(msg["visual_url"], caption="Generated Visual Sequence", use_container_width=True)

                if msg.get("video_link"):
                    st.markdown(f"🔗 [Direct Video Link / Browser Player]({msg['video_link']})")

                # Render Generated Image
                if msg.get("image_url"):
                    st.image(msg["image_url"], caption="Generated via Mega Rayquaza Visual Core", use_container_width=True)
                
                # Render Matplotlib Graph
                if msg.get("plot_code"):
                    try:
                        exec_env = {"np": np, "plt": plt}
                        exec(msg["plot_code"], exec_env)
                        fig = exec_env.get("fig") or plt.gcf()
                        st.pyplot(fig)
                        plt.clf()
                    except Exception:
                        pass

                if msg.get("pdf_data"):
                    st.download_button(
                        f"📄 Download Document: {msg['pdf_title']}.pdf",
                        data=msg["pdf_data"],
                        file_name=f"{msg['pdf_title'].replace(' ', '_')}.pdf",
                        mime="application/pdf",
                        key=f"dl_pdf_btn_{idx}"
                    )

                if msg.get("pptx_data"):
                    st.download_button(
                        "📊 Download Slide Deck (.pptx)",
                        data=msg["pptx_data"],
                        file_name="presentation.pptx",
                        mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                        key=f"dl_pptx_btn_{idx}"
                    )

        # Chat Input Bar
        user_input = st.chat_input("Ask a question, generate QR code (e.g. 'generate QR code for https://...'), analyze doc, make video, or plot graph...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Mega Rayquaza Council analyzing and executing commands..."):
                    council_system = (
                        f"You are the deployed expert AI system created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        f"USER-CONFIGURED PERSONALITY & TRAITS:\n{st.session_state.ai_custom_trait}\n\n"
                        "OPERATIONAL DIRECTIVES:\n"
                        "1. Answer with clarity, authority, and pedagogical instruction.\n"
                        "2. IF THE USER ASKS FOR A QR CODE: State what is encoded, then on the last line output: `GENERATE_QR: <exact string/URL to encode>`\n"
                        "3. IF AN UPLOADED DOCUMENT IS PRESENT: Read and answer based on the document text provided below.\n"
                        "4. IF THE USER ASKS FOR A VIDEO/ANIMATION: Explain the concept concisely, then on the last line output: `VIDEO_PROMPT: <vivid visual motion prompt in English>`\n"
                        "5. IF THE USER ASKS FOR AN IMAGE/PICTURE: Describe it, then on the last line output: `IMAGE_PROMPT: <vivid visual description in English>`\n"
                        "6. IF THE USER ASKS FOR A PRESENTATION/SLIDES/PPT: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                        "7. IF THE USER ASKS FOR A PDF/REPORT/NOTES: Write the document, and finish on the last line with: `GENERATE_PDF: <Title>`.\n"
                        "8. IF DRAWING A GRAPH: Supply executable plotting code using matplotlib.pyplot as plt and numpy as np defining fig inside a python code block.\n"
                        "9. Never output internal thoughts or planning notes."
                    )

                    # Inject active document text if loaded
                    if st.session_state.get("persisted_document_text"):
                        doc_chunk = st.session_state.persisted_document_text[:12000]
                        council_system += f"\n\n--- ATTACHED DOCUMENT INTAKE ({st.session_state.persisted_document_name}) ---\n{doc_chunk}\n--- END DOCUMENT INTAKE ---"

                    img_b64 = st.session_state.get("persisted_image_b64")
                    img_mime = st.session_state.get("persisted_image_mime", "image/png")

                    current_temp = float(st.session_state.ai_creativity)
                    current_tokens = int(st.session_state.ai_max_tokens)

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
                        reply = call_groq(messages, model=PRIMARY_VISION_MODEL, max_tok=current_tokens, temp=current_temp)
                    else:
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            if m.get("text_content"):
                                messages.append({"role": m["role"], "content": m["text_content"]})
                        reply = call_groq(messages, model=PRIMARY_TEXT_MODEL, max_tok=current_tokens, temp=current_temp)

                    if reply:
                        # Extract QR Code Generation
                        qr_bytes = None
                        qr_match = re.search(r"GENERATE_QR:\s*(.+)", reply, re.IGNORECASE)
                        if qr_match:
                            raw_qr_data = qr_match.group(1).strip()
                            try:
                                qr_bytes = build_qr_bytes(raw_qr_data)
                            except Exception:
                                pass

                        # Extract Video Generation
                        video_bytes = None
                        visual_url = None
                        video_link = None
                        vid_prompt_match = re.search(r"VIDEO_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                        if vid_prompt_match:
                            raw_vid_prompt = vid_prompt_match.group(1).strip()
                            clean_vid_prompt = re.sub(r"[^\w\s,.-]", "", raw_vid_prompt)
                            encoded_vid = urllib.parse.quote(clean_vid_prompt[:220])
                            video_link = f"https://image.pollinations.ai/prompt/{encoded_vid}?model=video&width=512&height=512"
                            visual_url = f"https://image.pollinations.ai/prompt/{encoded_vid}?width=768&height=432&nologo=true"
                            
                            with st.spinner("Retrieving video frames from Delta Stream..."):
                                v_bytes, c_type = fetch_media_bytes(video_link, timeout=25)
                                if v_bytes and "video" in (c_type or ""):
                                    video_bytes = v_bytes

                        # Extract Still Image Generation
                        image_url = None
                        img_prompt_match = re.search(r"IMAGE_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                        if img_prompt_match and not vid_prompt_match:
                            raw_prompt = img_prompt_match.group(1).strip()
                            clean_prompt = re.sub(r"[^\w\s,.-]", "", raw_prompt)
                            encoded_prompt = urllib.parse.quote(clean_prompt[:250])
                            image_url = f"https://image.pollinations.ai/prompt/{encoded_prompt}?width=768&height=512&nologo=true"

                        # Extract PDF Export
                        pdf_data = None
                        pdf_title = "Document"
                        pdf_match = re.search(r"GENERATE_PDF:\s*(.+)", reply, re.IGNORECASE)
                        if pdf_match:
                            pdf_title = pdf_match.group(1).strip()
                            body_for_pdf = re.sub(r"GENERATE_PDF:\s*.+", "", reply, flags=re.IGNORECASE).strip()
                            pdf_data = build_pdf_bytes(pdf_title, body_for_pdf)

                        # Extract PPTX Export
                        pptx_data = None
                        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
                        if json_match:
                            try:
                                parsed_json = json.loads(json_match.group(1))
                                if "slides" in parsed_json:
                                    pptx_data = build_pptx_bytes(parsed_json)
                            except Exception:
                                pass

                        # Extract Plot Code
                        plot_match = re.search(r"```(?:python)?\s*(.*?fig\s*=.*?)\s*```", reply, re.DOTALL)
                        plot_code = plot_match.group(1) if plot_match else None

                        # Clean conversational text
                        cleaned_text = re.sub(r"GENERATE_QR:\s*.+", "", reply, flags=re.IGNORECASE)
                        cleaned_text = re.sub(r"VIDEO_PROMPT:\s*.+", "", cleaned_text, flags=re.IGNORECASE)
                        cleaned_text = re.sub(r"IMAGE_PROMPT:\s*.+", "", cleaned_text, flags=re.IGNORECASE)
                        cleaned_text = re.sub(r"GENERATE_PDF:\s*.+", "", cleaned_text, flags=re.IGNORECASE)
                        cleaned_text = re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", cleaned_text, flags=re.DOTALL)
                        cleaned_text = re.sub(r"```(?:python)?\s*.*?fig\s*=.*?\s*```", "", cleaned_text, flags=re.DOTALL).strip()

                        if cleaned_text:
                            st.markdown(cleaned_text)

                        # Render QR Code immediately
                        if qr_bytes:
                            st.image(qr_bytes, caption="Scannable QR Code", width=220)

                        if video_bytes:
                            st.video(video_bytes)
                        elif visual_url:
                            st.image(visual_url, caption="Generated Visual Sequence", use_container_width=True)

                        if video_link:
                            st.markdown(f"🔗 [Direct Video Link / Browser Player]({video_link})")

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

                        new_idx = len(st.session_state.chat_history)
                        if qr_bytes:
                            st.download_button(
                                "📥 Download QR Code (.png)",
                                data=qr_bytes,
                                file_name="qrcode.png",
                                mime="image/png",
                                key=f"dl_qr_live_{new_idx}"
                            )

                        if pdf_data:
                            st.download_button(
                                f"📄 Download Document: {pdf_title}.pdf",
                                data=pdf_data,
                                file_name=f"{pdf_title.replace(' ', '_')}.pdf",
                                mime="application/pdf",
                                key=f"dl_pdf_live_{new_idx}"
                            )

                        if pptx_data:
                            st.download_button(
                                "📊 Download Slide Deck (.pptx)",
                                data=pptx_data,
                                file_name="presentation.pptx",
                                mime="application/vnd.openxmlformats-officedocument.presentationml.presentation",
                                key=f"dl_pptx_live_{new_idx}"
                            )

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "text_content": cleaned_text,
                            "qr_bytes": qr_bytes,
                            "video_bytes": video_bytes,
                            "visual_url": visual_url,
                            "video_link": video_link,
                            "image_url": image_url,
                            "plot_code": plot_code,
                            "pdf_data": pdf_data,
                            "pdf_title": pdf_title,
                            "pptx_data": pptx_data
                        })

    # TAB 3: STANDALONE EXPORT CODE
    with tab3:
        st.subheader("Generated Python Code")
        st.caption("Complete code compiled across all 26 specialist brains:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
