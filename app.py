import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import base64
import urllib.parse
import io
import json
import zipfile
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sympy as sp
import qrcode
from fpdf import FPDF
from pptx import Presentation
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

st.markdown('<p class="rayquaza-header">Universal AI Factory: Enterprise Apex Platform</p>', unsafe_allow_html=True)
st.markdown('<span class="apex-badge">🐉 Mega Rayquaza Core: All 6 Upgrades Active (RAG, REPL, TTS, QR Hosting, Routing, ZIP Exporter)</span>', unsafe_allow_html=True)
st.caption("Multimodal Voice-In/Out, Ephemeral File Hosting, Sandboxed Computation, Vector Search, and One-Click Deployment.")

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

# --- UPGRADE 1: EPHEMERAL FILE HOSTING FOR QR CODES ---
def upload_to_temp_host(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes)}
        res = requests.post("https://tmpfiles.org/api/v1/upload", files=files, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                raw_url = data["data"]["url"]
                # Convert view url to direct download url
                direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return direct_url
    except Exception:
        pass
    return None

# --- UPGRADE 3: AGENTIC PYTHON REPL SANDBOX ---
def run_sandboxed_python(code_snippet):
    stdout_capture = io.StringIO()
    safe_globals = {
        "np": np,
        "pd": pd,
        "sp": sp,
        "plt": plt,
        "print": lambda *args: stdout_capture.write(" ".join(str(a) for a in args) + "\n")
    }
    try:
        exec(code_snippet, safe_globals)
        output = stdout_capture.getvalue()
        fig = safe_globals.get("fig") or plt.gcf()
        has_fig = len(plt.get_fignums()) > 0
        return True, output, fig if has_fig else None
    except Exception as exc:
        return False, str(exc), None

# --- UPGRADE 4: SEMANTIC RAG CHUNKER ---
def extract_and_chunk_document(uploaded_file):
    text_chunks = []
    filename = uploaded_file.name.lower()
    try:
        if filename.endswith(".pdf"):
            reader = PdfReader(uploaded_file)
            for i, page in enumerate(reader.pages[:60]):
                p_text = page.extract_text()
                if p_text:
                    paragraphs = [p.strip() for p in p_text.split("\n\n") if len(p.strip()) > 40]
                    for p in paragraphs:
                        text_chunks.append({"page": i + 1, "text": p})
        elif filename.endswith((".txt", ".csv", ".md")):
            raw = uploaded_file.getvalue().decode("utf-8", errors="replace")
            lines = raw.split("\n")
            bucket = []
            for line in lines:
                bucket.append(line)
                if len("\n".join(bucket)) > 600:
                    text_chunks.append({"page": 1, "text": "\n".join(bucket)})
                    bucket = []
            if bucket:
                text_chunks.append({"page": 1, "text": "\n".join(bucket)})
    except Exception:
        pass
    return text_chunks

def retrieve_relevant_context(chunks, query, top_k=5):
    if not chunks:
        return ""
    q_words = set(re.findall(r"\w+", query.lower()))
    scored = []
    for c in chunks:
        c_words = set(re.findall(r"\w+", c["text"].lower()))
        overlap = len(q_words.intersection(c_words))
        scored.append((overlap, c))
    scored.sort(key=lambda x: x[0], reverse=True)
    selected = [item[1]["text"] for item in scored[:top_k] if item[0] > 0]
    if not selected:
        selected = [c["text"] for c in chunks[:3]]
    return "\n---\n".join(selected)

# --- UPGRADE 6: BUNDLE ZIP EXPORTER ---
def build_deployment_zip(app_code, goal_text):
    zip_buffer = io.BytesIO()
    reqs_txt = (
        "streamlit\nrequests\nnumpy\nmatplotlib\n"
        "fpdf2\npython-pptx\npypdf\nqrcode[pil]\npandas\nsympy\n"
    )
    readme_txt = f"# Deployed AI Application\nGenerated by Universal AI Factory.\n\n### Objective:\n{goal_text}\n"
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("app.py", app_code)
        zip_file.writestr("requirements.txt", reqs_txt)
        zip_file.writestr("README.md", readme_txt)
    return zip_buffer.getvalue()

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
    qr = qrcode.QRCode(version=None, error_correction=qrcode.constants.ERROR_CORRECT_M, box_size=10, border=3)
    qr.add_data(str(payload_data)[:1200])
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    buf = io.BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()

def fetch_media_bytes(url, timeout=30):
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
FAST_ROUTER_MODEL = "llama-3.1-8b-instant"

def call_groq(messages, model=PRIMARY_TEXT_MODEL, key=api_key, max_tok=1400, temp=0.4):
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
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=40)
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return strip_internal_thoughts(content)
        else:
            return f"API Error ({res.status_code}): {res.text}"
    except Exception as exc:
        return f"Request failed: {exc}"

# --- UPGRADE 2: SPEECH-TO-TEXT & TEXT-TO-SPEECH (TTS) WIDGET ---
def render_voice_interface(element_id="mainVoice", label="Voice Interaction"):
    voice_html = f"""
    <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 6px;">
        <div style="display: flex; gap: 8px;">
            <button id="{element_id}_in" style="
                background: linear-gradient(90deg, #059669, #d97706);
                color: white; border: none; padding: 7px 14px; border-radius: 6px;
                cursor: pointer; font-weight: bold;">
                🎤 Speak Input
            </button>
            <button id="{element_id}_out" style="
                background: #374151; color: #fde047; border: 1px solid #d97706;
                padding: 7px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                🔊 Read Response
            </button>
        </div>
        <div id="{element_id}_status" style="
            font-size: 12px; color: #d1d5db; background: #1f2937; padding: 6px 10px;
            border-radius: 6px; min-height: 32px; border: 1px solid #059669;">
            Ready. Click Speak to dictate, or Read to speak aloud.
        </div>
    </div>
    <script>
    const bIn = document.getElementById('{element_id}_in');
    const bOut = document.getElementById('{element_id}_out');
    const stat = document.getElementById('{element_id}_status');
    let recognizing = false;

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recog = new SR();
        recog.continuous = false;
        recog.interimResults = true;

        recog.onstart = () => {{ recognizing = true; bIn.innerText = "🛑 Stop"; stat.innerText = "Listening..."; }};
        recog.onresult = (e) => {{
            let str = '';
            for (let i = e.resultIndex; i < e.results.length; ++i) str += e.results[i][0].transcript;
            stat.innerText = str;
            navigator.clipboard.writeText(str);
        }};
        recog.onerror = (e) => {{ stat.innerText = "Error: " + e.error; recognizing = false; bIn.innerText = "🎤 Speak Input"; }};
        recog.onend = () => {{ recognizing = false; bIn.innerText = "🎤 Speak Input (Copied!)"; }};

        bIn.onclick = () => {{ recognizing ? recog.stop() : recog.start(); }};
    }}

    bOut.onclick = () => {{
        const msgs = window.parent.document.querySelectorAll('.stChatMessage');
        if (msgs.length > 0) {{
            const last = msgs[msgs.length - 1].innerText;
            window.speechSynthesis.cancel();
            const utter = new SpeechSynthesisUtterance(last);
            utter.rate = 1.0;
            window.speechSynthesis.speak(utter);
            stat.innerText = "🔊 Reading latest response aloud...";
        }} else {{
            stat.innerText = "No response available to read yet.";
        }}
    }};
    </script>
    """
    components.html(voice_html, height=85)

# Session State Initialization
if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []
if "persisted_image_b64" not in st.session_state:
    st.session_state.persisted_image_b64 = None
if "persisted_image_mime" not in st.session_state:
    st.session_state.persisted_image_mime = None
if "persisted_doc_chunks" not in st.session_state:
    st.session_state.persisted_doc_chunks = []
if "persisted_doc_name" not in st.session_state:
    st.session_state.persisted_doc_name = None
if "persisted_doc_url" not in st.session_state:
    st.session_state.persisted_doc_url = None
if "ai_creativity" not in st.session_state:
    st.session_state.ai_creativity = 0.5
if "ai_max_tokens" not in st.session_state:
    st.session_state.ai_max_tokens = 1400
if "ai_custom_trait" not in st.session_state:
    st.session_state.ai_custom_trait = "Articulate, polite, visually rich, and mathematically rigorous."

# SECTION 1: AI FACTORY CREATOR
st.subheader("1. AI Factory Creator")
col_c_text, col_c_mic = st.columns([2, 1])

with col_c_mic:
    st.write("🎙️ **Voice Command to Build AI**")
    render_voice_interface(element_id="factory_creator_voice")

with col_c_text:
    user_request = st.text_area(
        "Describe the AI tool you want the factory to build:",
        placeholder="e.g. Build an AI assistant with document analysis, instant file QR codes, video/image generation, and math execution.",
        height=95
    )

if st.button("Deploy AI with Mega Rayquaza Inner Core", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please provide a prompt or speak your AI design.")
    else:
        with st.status("Harmonizing Council & Activating 6 Architectural Upgrades...", expanded=True) as status:
            status.write("🐉 Routing inner core directives with Mega Rayquaza...")
            council_synthesis_prompt = (
                f"You are the Mega Rayquaza Core presiding over the Enterprise Council. Objective: '{user_request}'.\n"
                "Incorporate all 26 brain domains:\n"
                "1. Hardware & Electronics Specialist (Circuits, Microcontrollers, Pinouts)\n"
                "2. Vision Inspector (Visual Hardware & Photo Analysis)\n"
                "3. Pure & Applied Mathematics Brain\n"
                "4. Physics Engine\n"
                "5. Chemistry Specialist\n"
                "6. Computer Science & Algorithm Engine\n"
                "7. Software Engineering Brain\n"
                "8. Microcontroller Firmware Specialist\n"
                "9. Life Sciences Brain\n"
                "10. Statistical Modeling Brain\n"
                "11. Dynamic Visualizer & Graph Plotter\n"
                "12. Motion & Video Specialist\n"
                "13. Still Image Prompt Specialist\n"
                "14. Voice & Audio Specialist\n"
                "15. Document Compiler (PDF Reports)\n"
                "16. Slide Deck Architect (PPTX)\n"
                "17. Document Intake & RAG Specialist (Retrieval over uploaded chunks)\n"
                "18. QR Code Engine (Instant file downloads and URLs)\n"
                "19. Sandboxed Python REPL Specialist (Evaluating mathematical expressions)\n"
                "20-26. Multi-Disciplinary Synthesis, Validation, & Safety\n\n"
                "RULES:\n"
                "- If the user needs computations or exact math: Output an executable python block tagged ```python ``` that defines variables and prints results or defines fig.\n"
                "- If the user asks for a QR CODE: Output `GENERATE_QR: <url or string>`.\n"
                "- If the user requests a VIDEO: Output `VIDEO_PROMPT: <prompt>`.\n"
                "- If the user requests an IMAGE: Output `IMAGE_PROMPT: <prompt>`.\n"
                "- If the user requests a PPT: Output a JSON block inside ```json ``` with slides/bullets structure.\n"
                "- If the user requests a PDF: Output `GENERATE_PDF: <Title>` on the last line.\n"
            )
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1100,
                temp=0.4
            )

            status.write("Compiling production source code & deployment bundle...")
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
            status.update(label="Enterprise AI Deployed with All 6 Upgrades!", state="complete", expanded=False)
            st.rerun()

# SECTION 2: CREATED AI WORKSPACE
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["⚡ Live Custom AI Workspace", "🛠️ Edit AI Characteristics", "📦 Standalone Code & One-Click ZIP Exporter"])

    # TAB 2: EDIT AI CHARACTERISTICS
    with tab2:
        st.subheader("Fine-Tune AI Behavior & Live Parameters")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            st.session_state.ai_creativity = st.slider(
                "Creativity (Temperature)", min_value=0.0, max_value=1.0, value=float(st.session_state.ai_creativity), step=0.05
            )
        with col_c2:
            st.session_state.ai_max_tokens = st.slider(
                "Response Length (Tokens)", min_value=400, max_value=2500, value=int(st.session_state.ai_max_tokens), step=100
            )

        st.session_state.ai_custom_trait = st.text_area(
            "Persona & Response Guidelines:", value=st.session_state.ai_custom_trait
        )
        app_info["system_prompt"] = st.text_area(
            "Operational Council Directive:", value=app_info["system_prompt"], height=160
        )
        st.success("✅ Parameters updated and active for subsequent chat turns.")

    # TAB 1: WORKSPACE
    with tab1:
        st.subheader("2. Your Active Custom AI")
        st.caption(f"Objective: {app_info['goal']} | Inner Core: Mega Rayquaza Active")

        st.markdown("#### 📁 File Intake, Voice & Ephemeral Cloud Storage")
        col_img, col_doc, col_mic = st.columns([1.3, 1.7, 1.2])

        with col_img:
            uploaded_image = st.file_uploader("📷 Upload Photo / Circuit:", type=["png", "jpg", "jpeg"], key="workspace_img")
            if uploaded_image:
                b_data = uploaded_image.getvalue()
                if len(b_data) > 0:
                    st.session_state.persisted_image_b64 = base64.b64encode(b_data).decode("utf-8")
                    st.session_state.persisted_image_mime = uploaded_image.type

        with col_doc:
            uploaded_doc = st.file_uploader("📄 Upload Document (.pdf, .txt, .csv):", type=["pdf", "txt", "csv", "md"], key="workspace_doc")
            if uploaded_doc:
                raw_bytes = uploaded_doc.getvalue()
                chunks = extract_and_chunk_document(uploaded_doc)
                st.session_state.persisted_doc_chunks = chunks
                st.session_state.persisted_doc_name = uploaded_doc.name
                # Ephemeral hosting for instant scannable QR code downloads
                if not st.session_state.persisted_doc_url:
                    with st.spinner("Publishing document to cloud storage for instant QR download..."):
                        hosted_url = upload_to_temp_host(raw_bytes, uploaded_doc.name)
                        st.session_state.persisted_doc_url = hosted_url

        with col_mic:
            st.write("🎙️ **Voice Controls**")
            render_voice_interface(element_id="chat_voice_ctrl")

        # Active File Status Displays
        col_s1, col_s2 = st.columns(2)
        with col_s1:
            if st.session_state.get("persisted_image_b64"):
                st.success("📷 Vision Brain: Attached image ready.")
                st.image(base64.b64decode(st.session_state.persisted_image_b64), width=160)
                if st.button("❌ Remove Image"):
                    st.session_state.persisted_image_b64 = None
                    st.session_state.persisted_image_mime = None
                    st.rerun()

        with col_s2:
            if st.session_state.get("persisted_doc_chunks"):
                st.info(f"📄 **Semantic Chunks:** {len(st.session_state.persisted_doc_chunks)} chunks parsed from {st.session_state.persisted_doc_name}")
                if st.session_state.get("persisted_doc_url"):
                    st.markdown(f"🔗 **Ephemeral Live Link:** [Direct Cloud URL]({st.session_state.persisted_doc_url})")
                if st.button("❌ Clear Document Memory"):
                    st.session_state.persisted_doc_chunks = []
                    st.session_state.persisted_doc_name = None
                    st.session_state.persisted_doc_url = None
                    st.rerun()

        # Render conversation history with unique keys
        for idx, msg in enumerate(st.session_state.chat_history):
            with st.chat_message(msg["role"]):
                if msg.get("text_content"):
                    st.markdown(msg["text_content"])

                if msg.get("qr_bytes"):
                    st.image(msg["qr_bytes"], caption="Scannable QR Code", width=220)
                    st.download_button("📥 Download QR Code (.png)", data=msg["qr_bytes"], file_name="qrcode.png", mime="image/png", key=f"dl_qr_btn_{idx}")

                if msg.get("repl_output"):
                    st.markdown("```text\n" + msg["repl_output"] + "\n```")

                if msg.get("video_bytes"):
                    st.video(msg["video_bytes"])
                elif msg.get("visual_url"):
                    st.image(msg["visual_url"], caption="Generated Motion Visualization", use_container_width=True)

                if msg.get("video_link"):
                    st.markdown(f"🔗 [Direct Video Link / Browser Player]({msg['video_link']})")

                if msg.get("image_url"):
                    st.image(msg["image_url"], caption="Visual Synthesizer Output", use_container_width=True)

                if msg.get("plot_fig"):
                    st.pyplot(msg["plot_fig"])

                if msg.get("pdf_data"):
                    st.download_button(f"📄 Download Document: {msg['pdf_title']}.pdf", data=msg["pdf_data"], file_name=f"{msg['pdf_title'].replace(' ', '_')}.pdf", mime="application/pdf", key=f"dl_pdf_btn_{idx}")

                if msg.get("pptx_data"):
                    st.download_button("📊 Download Slide Deck (.pptx)", data=msg["pptx_data"], file_name="presentation.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key=f"dl_pptx_btn_{idx}")

        # Chat Input Console
        user_input = st.chat_input("Ask a question, generate QR code, execute Python/math, analyze doc, or create slides...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Mega Rayquaza Core routing and synthesizing response..."):
                    # Dynamic Context Injection via Semantic Search
                    retrieved_context = ""
                    if st.session_state.get("persisted_doc_chunks"):
                        retrieved_context = retrieve_relevant_context(st.session_state.persisted_doc_chunks, user_input)

                    council_system = (
                        f"You are the deployed expert AI system created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        f"USER-CONFIGURED PERSONALITY & TRAITS:\n{st.session_state.ai_custom_trait}\n\n"
                        "OPERATIONAL DIRECTIVES:\n"
                        "1. Answer with clarity, authority, and thorough explanations.\n"
                        "2. IF THE USER ASKS FOR A QR CODE: Output `GENERATE_QR: <url or string>`. If they ask for a QR code of their uploaded document, use the live document link provided in context.\n"
                        "3. IF PERFORMING MATH, TABLE DATA, OR PLOTS: Provide Python code inside ```python ``` that assigns `fig` or prints calculation results.\n"
                        "4. IF CREATING A VIDEO: Output `VIDEO_PROMPT: <vivid visual prompt>` on the last line.\n"
                        "5. IF CREATING AN IMAGE: Output `IMAGE_PROMPT: <visual prompt>` on the last line.\n"
                        "6. IF CREATING SLIDES: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                        "7. IF WRITING A REPORT/PDF: Conclude with `GENERATE_PDF: <Title>`.\n"
                    )

                    if st.session_state.get("persisted_doc_url"):
                        council_system += f"\n\nLIVE DOCUMENT URL: {st.session_state.persisted_doc_url}\n"
                    if retrieved_context:
                        council_system += f"\n\n--- RELEVANT DOCUMENT EXCERPTS ---\n{retrieved_context}\n--- END EXCERPTS ---\n"

                    # --- UPGRADE 5: DYNAMIC INTENT & MODEL ROUTER ---
                    img_b64 = st.session_state.get("persisted_image_b64")
                    img_mime = st.session_state.get("persisted_image_mime", "image/png")
                    current_temp = float(st.session_state.ai_creativity)
                    current_tokens = int(st.session_state.ai_max_tokens)

                    if img_b64:
                        active_model = PRIMARY_VISION_MODEL
                        user_content = [
                            {"type": "text", "text": user_input},
                            {"type": "image_url", "image_url": {"url": f"data:{img_mime};base64,{img_b64}"}}
                        ]
                        messages = [{"role": "system", "content": council_system}, {"role": "user", "content": user_content}]
                    else:
                        active_model = PRIMARY_TEXT_MODEL
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            if m.get("text_content"):
                                messages.append({"role": m["role"], "content": m["text_content"]})

                    reply = call_groq(messages, model=active_model, max_tok=current_tokens, temp=current_temp)

                    if reply:
                        # Extract QR Generation
                        qr_bytes = None
                        qr_match = re.search(r"GENERATE_QR:\s*(.+)", reply, re.IGNORECASE)
                        if qr_match:
                            raw_qr = qr_match.group(1).strip()
                            if "document" in raw_qr.lower() and st.session_state.get("persisted_doc_url"):
                                raw_qr = st.session_state.persisted_doc_url
                            qr_bytes = build_qr_bytes(raw_qr)
                        elif "qr" in user_input.lower() and st.session_state.get("persisted_doc_url"):
                            qr_bytes = build_qr_bytes(st.session_state.persisted_doc_url)

                        # Extract Sandboxed Code Execution
                        repl_output = None
                        plot_fig = None
                        code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", reply, re.DOTALL)
                        if code_match and ("plt" in code_match.group(1) or "print" in code_match.group(1) or "sp." in code_match.group(1)):
                            code_to_exec = code_match.group(1)
                            success, stdout_txt, fig = run_sandboxed_python(code_to_exec)
                            if success:
                                repl_output = stdout_txt if stdout_txt.strip() else None
                                plot_fig = fig

                        # Extract Video Generation
                        video_bytes = None
                        visual_url = None
                        video_link = None
                        vid_match = re.search(r"VIDEO_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                        if vid_match:
                            raw_vid = re.sub(r"[^\w\s,.-]", "", vid_match.group(1).strip())
                            encoded_v = urllib.parse.quote(raw_vid[:220])
                            video_link = f"https://image.pollinations.ai/prompt/{encoded_v}?model=video&width=512&height=512"
                            visual_url = f"https://image.pollinations.ai/prompt/{encoded_v}?width=768&height=432&nologo=true"
                            v_bytes, c_type = fetch_media_bytes(video_link, timeout=25)
                            if v_bytes and "video" in (c_type or ""):
                                video_bytes = v_bytes

                        # Extract Image Generation
                        image_url = None
                        img_match = re.search(r"IMAGE_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                        if img_match and not vid_match:
                            raw_img = re.sub(r"[^\w\s,.-]", "", img_match.group(1).strip())
                            encoded_i = urllib.parse.quote(raw_img[:250])
                            image_url = f"https://image.pollinations.ai/prompt/{encoded_i}?width=768&height=512&nologo=true"

                        # Extract PDF Generation
                        pdf_data = None
                        pdf_title = "Document"
                        pdf_match = re.search(r"GENERATE_PDF:\s*(.+)", reply, re.IGNORECASE)
                        if pdf_match:
                            pdf_title = pdf_match.group(1).strip()
                            clean_doc = re.sub(r"GENERATE_PDF:\s*.+", "", reply, flags=re.IGNORECASE).strip()
                            pdf_data = build_pdf_bytes(pdf_title, clean_doc)

                        # Extract PPTX Generation
                        pptx_data = None
                        json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
                        if json_match:
                            try:
                                parsed = json.loads(json_match.group(1))
                                if "slides" in parsed:
                                    pptx_data = build_pptx_bytes(parsed)
                            except Exception:
                                pass

                        # Clean response text
                        cleaned = re.sub(r"GENERATE_QR:\s*.+", "", reply, flags=re.IGNORECASE)
                        cleaned = re.sub(r"VIDEO_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r"IMAGE_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r"GENERATE_PDF:\s*.+", "", cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", cleaned, flags=re.DOTALL)
                        cleaned = re.sub(r"```(?:python)?\s*.*?fig\s*=.*?\s*```", "", cleaned, flags=re.DOTALL).strip()

                        if cleaned:
                            st.markdown(cleaned)

                        if qr_bytes:
                            st.image(qr_bytes, caption="Scannable QR Code", width=220)

                        if repl_output:
                            st.markdown("```text\n" + repl_output + "\n```")

                        if video_bytes:
                            st.video(video_bytes)
                        elif visual_url:
                            st.image(visual_url, caption="Generated Visual Sequence", use_container_width=True)

                        if video_link:
                            st.markdown(f"🔗 [Direct Video Link / Browser Player]({video_link})")

                        if image_url:
                            st.image(image_url, caption="Visual Synthesizer Output", use_container_width=True)

                        if plot_fig:
                            st.pyplot(plot_fig)
                            plt.clf()

                        new_idx = len(st.session_state.chat_history)
                        if qr_bytes:
                            st.download_button("📥 Download QR Code (.png)", data=qr_bytes, file_name="qrcode.png", mime="image/png", key=f"dl_qr_live_{new_idx}")

                        if pdf_data:
                            st.download_button(f"📄 Download Document: {pdf_title}.pdf", data=pdf_data, file_name=f"{pdf_title.replace(' ', '_')}.pdf", mime="application/pdf", key=f"dl_pdf_live_{new_idx}")

                        if pptx_data:
                            st.download_button("📊 Download Slide Deck (.pptx)", data=pptx_data, file_name="presentation.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key=f"dl_pptx_live_{new_idx}")

                        st.session_state.chat_history.append({
                            "role": "assistant",
                            "text_content": cleaned,
                            "qr_bytes": qr_bytes,
                            "repl_output": repl_output,
                            "video_bytes": video_bytes,
                            "visual_url": visual_url,
                            "video_link": video_link,
                            "image_url": image_url,
                            "plot_fig": plot_fig,
                            "pdf_data": pdf_data,
                            "pdf_title": pdf_title,
                            "pptx_data": pptx_data
                        })

    # TAB 3: STANDALONE CODE & ONE-CLICK ZIP EXPORTER
    with tab3:
        st.subheader("Standalone Python Code & Deployment Bundle")
        st.caption("Download the raw code or a complete deployment-ready ZIP package (including requirements.txt and README.md):")
        
        zip_bytes = build_deployment_zip(app_info["source_code"], app_info["goal"])
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.download_button(
                "📦 Download Complete Deployment Bundle (.zip)",
                data=zip_bytes,
                file_name="custom_ai_package.zip",
                mime="application/zip",
                type="primary"
            )
        with col_z2:
            st.download_button(
                "📄 Download Single Source Code (.py)",
                data=app_info["source_code"],
                file_name="custom_ai_app.py",
                mime="text/plain"
            )

        st.markdown("---")
        st.code(app_info["source_code"], language="python")
