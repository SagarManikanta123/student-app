import streamlit as st
import streamlit.components.v1 as components
import requests
import re
import base64
import urllib.parse
import io
import json
import zipfile
import unicodedata
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sympy as sp
import qrcode
from fpdf import FPDF
from pptx import Presentation
from pypdf import PdfReader

st.set_page_config(page_title="Universal AI Factory (Mega Rayquaza Core)", layout="wide")

# Creative Futuristic HUD Chat Styling
st.markdown("""
<style>
    .rayquaza-header {
        background: linear-gradient(90deg, #10b981, #06b6d4, #f59e0b);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.3rem;
        font-weight: 800;
        margin-bottom: 2px;
    }
    .apex-badge {
        background: linear-gradient(90deg, rgba(6, 78, 59, 0.8), rgba(4, 120, 87, 0.8));
        color: #fde047;
        padding: 4px 12px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #f59e0b;
        display: inline-block;
        margin-bottom: 12px;
        box-shadow: 0 0 10px rgba(16, 185, 129, 0.3);
    }
    /* Creative User Message Bubble */
    .user-bubble-container {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 14px;
        padding-left: 15%;
    }
    .user-bubble {
        background: linear-gradient(135deg, #1e293b, #0f172a);
        border: 1px solid #38bdf8;
        border-right: 4px solid #38bdf8;
        border-radius: 16px 4px 16px 16px;
        padding: 12px 18px;
        color: #f8fafc;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.15);
        position: relative;
    }
    .user-tag {
        font-size: 0.72rem;
        font-weight: 800;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 1px;
        margin-bottom: 4px;
    }

    /* Creative Mega Rayquaza Assistant Card */
    .ai-bubble-container {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 18px;
        padding-right: 8%;
    }
    .ai-bubble {
        background: linear-gradient(135deg, rgba(6, 78, 59, 0.35), rgba(15, 23, 42, 0.85));
        border: 1px solid #059669;
        border-left: 4px solid #f59e0b;
        border-radius: 4px 18px 18px 18px;
        padding: 16px 20px;
        color: #f1f5f9;
        box-shadow: 0 6px 20px rgba(16, 185, 129, 0.18);
        width: 100%;
    }
    .ai-tag {
        font-size: 0.75rem;
        font-weight: 800;
        color: #fde047;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 8px;
        display: flex;
        align-items: center;
        gap: 6px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="rayquaza-header">Universal AI Factory: 26-Brain Mega-Council</p>', unsafe_allow_html=True)
st.markdown('<span class="apex-badge">🐉 Inner Core: Mega Rayquaza (Cosmic HUD Interface & Bulletproof Unicode PDF Engine Active)</span>', unsafe_allow_html=True)
st.caption("Creative cosmic messaging, voice synthesis, notebook LaTeX math, circuit prototyping, and PWA mobile deployment.")

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

# Bulletproof PDF Generation - Solves FPDFUnicodeEncodingException Permanently
def clean_pdf_text(text):
    if not text:
        return ""
    replacements = {
        "—": "-", "–": "-", '"': '"', '"': '"', "‘": "'", "’": "'",
        "→": "->", "←": "<-", "⇒": "=>", "≤": "<=", "≥": ">=",
        "≠": "!=", "≈": "~", "×": "*", "÷": "/", "°": " deg",
        "•": "*", "…": "...", "α": "alpha", "β": "beta", "π": "pi",
        "λ": "lambda", "μ": "mu", "θ": "theta", "Ω": "Ohm"
    }
    for orig, rep in replacements.items():
        text = text.replace(orig, rep)
    # Decompose accented unicode into plain ascii
    normalized = unicodedata.normalize("NFKD", text)
    safe_ascii = "".join(c for c in normalized if 32 <= ord(c) <= 126 or c == "\n")
    return safe_ascii

def build_pdf_bytes(title, content):
    pdf = FPDF()
    pdf.add_page()
    safe_title = clean_pdf_text(title)[:80]
    safe_body = clean_pdf_text(content)

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, text=safe_title if safe_title else "Document", new_x="LMARGIN", new_y="NEXT", align="C")
    pdf.ln(5)
    pdf.set_font("Helvetica", size=11)

    for paragraph in safe_body.split("\n"):
        p_clean = paragraph.strip()
        if p_clean:
            pdf.multi_cell(0, 7, text=p_clean)
            pdf.ln(2)
    return bytes(pdf.output())

def upload_to_temp_host(file_bytes, filename):
    try:
        files = {"file": (filename, file_bytes)}
        res = requests.post("https://tmpfiles.org/api/v1/upload", files=files, timeout=12)
        if res.status_code == 200:
            data = res.json()
            if data.get("status") == "success":
                raw_url = data["data"]["url"]
                direct_url = raw_url.replace("tmpfiles.org/", "tmpfiles.org/dl/")
                return direct_url
    except Exception:
        pass
    return None

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

def build_deployment_zip(app_code, goal_text):
    zip_buffer = io.BytesIO()
    reqs_txt = (
        "streamlit\nrequests\nnumpy\nmatplotlib\n"
        "fpdf2\npython-pptx\npypdf\nqrcode[pil]\npandas\nsympy\n"
    )
    readme_txt = f"# Deployed AI Application\nGenerated by Universal AI Factory.\n\n### Objective:\n{goal_text}\n"
    manifest_txt = json.dumps({
        "name": "Custom Council AI",
        "short_name": "CouncilAI",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#111827",
        "theme_color": "#065f46"
    }, indent=2)
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("app.py", app_code)
        zip_file.writestr("requirements.txt", reqs_txt)
        zip_file.writestr("README.md", readme_txt)
        zip_file.writestr("manifest.json", manifest_txt)
    return zip_buffer.getvalue()

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

def call_groq(messages, model=PRIMARY_TEXT_MODEL, key=api_key, max_tok=1800, temp=0.25):
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
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=45)
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return strip_internal_thoughts(content)
        else:
            return f"API Error ({res.status_code}): {res.text}"
    except Exception as exc:
        return f"Request failed: {exc}"

# Two-Way Voice Component with "Speak in My Voice"
def render_voice_interface(element_id="mainVoice", pitch=1.0, rate=1.0, autoplay=False):
    autoplay_js = "true" if autoplay else "false"
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
                🔊 Speak in My Voice
            </button>
        </div>
        <div id="{element_id}_status" style="
            font-size: 12px; color: #d1d5db; background: #1f2937; padding: 6px 10px;
            border-radius: 6px; min-height: 32px; border: 1px solid #059669;">
            Voice Engine Ready. Pitch: {pitch}x | Rate: {rate}x
        </div>
    </div>
    <script>
    const bIn = document.getElementById('{element_id}_in');
    const bOut = document.getElementById('{element_id}_out');
    const stat = document.getElementById('{element_id}_status');
    const targetPitch = {pitch};
    const targetRate = {rate};
    const autoPlayOn = {autoplay_js};

    function speakInMyVoice(text) {{
        window.speechSynthesis.cancel();
        const cleanSpeakText = text.replace(/\\$+/g, '').replace(/\\\\/g, '').replace(/[#*_`]/g, '');
        const utter = new SpeechSynthesisUtterance(cleanSpeakText);
        utter.pitch = targetPitch;
        utter.rate = targetRate;

        const voices = window.speechSynthesis.getVoices();
        if (voices.length > 0) {{
            const preferred = voices.find(v => v.lang.startsWith('en') && !v.name.includes('Google') && !v.name.includes('Bad'));
            if (preferred) utter.voice = preferred;
        }}

        window.speechSynthesis.speak(utter);
        stat.innerText = "🔊 Speaking in your configured voice...";
    }}

    if ('webkitSpeechRecognition' in window || 'SpeechRecognition' in window) {{
        const SR = window.SpeechRecognition || window.webkitSpeechRecognition;
        const recog = new SR();
        recog.continuous = false;
        recog.interimResults = true;

        recog.onstart = () => {{ bIn.innerText = "🛑 Stop"; stat.innerText = "Listening to your voice..."; }};
        recog.onresult = (e) => {{
            let str = '';
            for (let i = e.resultIndex; i < e.results.length; ++i) str += e.results[i][0].transcript;
            stat.innerText = str;
            navigator.clipboard.writeText(str);
        }};
        recog.onerror = (e) => {{ stat.innerText = "Mic error: " + e.error; bIn.innerText = "🎤 Speak Input"; }};
        recog.onend = () => {{ bIn.innerText = "🎤 Speak Input (Copied!)"; }};

        bIn.onclick = () => {{ recog.start(); }};
    }}

    bOut.onclick = () => {{
        const allAiCards = window.parent.document.querySelectorAll('.ai-bubble');
        if (allAiCards.length > 0) {{
            const lastText = allAiCards[allAiCards.length - 1].innerText;
            speakInMyVoice(lastText);
        }} else {{
            stat.innerText = "No response available to speak yet.";
        }}
    }};

    if (autoPlayOn) {{
        setTimeout(() => {{
            const allAiCards = window.parent.document.querySelectorAll('.ai-bubble');
            if (allAiCards.length > 0) {{
                const lastText = allAiCards[allAiCards.length - 1].innerText;
                speakInMyVoice(lastText);
            }}
        }}, 600);
    }}
    </script>
    """
    components.html(voice_html, height=85)

# PWA Mobile Add-to-Home-Screen Injection
def inject_pwa_headers():
    pwa_meta = """
    <script>
    let manifestLink = document.createElement('link');
    manifestLink.rel = 'manifest';
    manifestLink.href = 'data:application/json;base64,' + btoa(JSON.stringify({
        "name": "Universal Council AI",
        "short_name": "CouncilAI",
        "start_url": window.location.href,
        "display": "standalone",
        "background_color": "#111827",
        "theme_color": "#065f46"
    }));
    document.head.appendChild(manifestLink);

    let appleIcon = document.createElement('link');
    appleIcon.rel = 'apple-touch-icon';
    appleIcon.href = 'https://raw.githubusercontent.com/PokeAPI/sprites/master/sprites/pokemon/other/official-artwork/384.png';
    document.head.appendChild(appleIcon);

    let metaCapable = document.createElement('meta');
    metaCapable.name = 'apple-mobile-web-app-capable';
    metaCapable.content = 'yes';
    document.head.appendChild(metaCapable);
    </script>
    """
    components.html(pwa_meta, height=0)

inject_pwa_headers()

# State Initialization
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
    st.session_state.ai_creativity = 0.25
if "ai_max_tokens" not in st.session_state:
    st.session_state.ai_max_tokens = 1800
if "voice_pitch" not in st.session_state:
    st.session_state.voice_pitch = 1.0
if "voice_rate" not in st.session_state:
    st.session_state.voice_rate = 1.0
if "voice_autoplay" not in st.session_state:
    st.session_state.voice_autoplay = False
if "user_voice_sample" not in st.session_state:
    st.session_state.user_voice_sample = None
if "ai_custom_trait" not in st.session_state:
    st.session_state.ai_custom_trait = (
        "Rigorous, complete products only, polite. "
        "All mathematics must be displayed in standard notebook notation using $inline$ and $$display$$ LaTeX blocks."
    )

# SECTION 1: AI FACTORY CREATOR
st.subheader("1. AI Factory Creator (Voice or Text)")
col_c_text, col_c_mic = st.columns([2, 1])

with col_c_mic:
    st.write("🎙️️ **Voice Command to Build AI**")
    render_voice_interface(element_id="factory_creator_voice", pitch=st.session_state.voice_pitch, rate=st.session_state.voice_rate)

with col_c_text:
    user_request = st.text_area(
        "Describe the AI tool you want the factory to build:",
        placeholder="e.g. Build an AI to show full working prototypes for electronic projects, with notebook-style math proofs and diagrams.",
        height=95
    )

if st.button("Deploy AI with Mega Rayquaza Inner Core", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please provide a prompt or speak your AI design.")
    else:
        with st.status("Harmonizing 26-Brain Council & Launching Cosmic HUD...", expanded=True) as status:
            status.write("🐉 Calibrating notebook mathematical notation & full deliverables...")
            council_synthesis_prompt = (
                f"You are the Mega Rayquaza Core presiding over the Enterprise Council. Objective: '{user_request}'.\n"
                "Incorporate all 26 brain domains:\n"
                "1. Inner Core: Mega Rayquaza (Complete Product Mandate — No Half Answers, No Vague Outlines)\n"
                "2. Pure & Applied Mathematics Brain (Textbook & Notebook Math Notation Specialist)\n"
                "3. Personal Voice Assistant Engine (Speaks in User Voice Profile)\n"
                "4. Hardware & Electronics Specialist (Circuits, Schematics, Pinouts, Complete Working Firmware)\n"
                "5. Vision Inspector (Visual Hardware & Photo Analysis)\n"
                "6. Theoretical & Classical Physics Engine (Formulas rendered cleanly in display LaTeX)\n"
                "7. Chemistry Specialist (Balanced Equations in standard chemical format)\n"
                "8. Computer Science & Algorithm Engine\n"
                "9. Software Engineering Brain\n"
                "10. Microcontroller Firmware Specialist\n"
                "11. Dynamic Visualizer & Graph Plotter\n"
                "12. Motion & Video Specialist\n"
                "13. Still Image Prompt Specialist\n"
                "14. Document Compiler (PDF Reports with clean formatting)\n"
                "15. Slide Deck Architect (PPTX)\n"
                "16. Document Intake & Semantic Search Specialist\n"
                "17. QR Code Engine (Direct mobile links and file downloads)\n"
                "18. Sandboxed Python REPL Specialist (Evaluating exact mathematical proofs)\n"
                "19-26. Multi-Disciplinary Synthesis, Production-Ready Verification, & Safety\n\n"
                "CRITICAL FORMATTING & COMPLETION RULES:\n"
                "1. NOTEBOOK MATHEMATICS: NEVER display raw programming syntax like `sqrt(x^2 + y^2)`, `x**2 + 4*a*x`, or `y=mx+b` in plain text. ALWAYS render equations exactly as written in textbooks and student notebooks using LaTeX syntax: enclosed in `$inline$` for in-sentence math, and `$$display$$` for standalone equations.\n"
                "2. FULL PRODUCTS ONLY: Provide complete, fully-realized deliverables without placeholders.\n"
                "3. If the user asks for a QR CODE: Output `GENERATE_QR: <url or string>`.\n"
                "4. If the user requests a VIDEO: Output `VIDEO_PROMPT: <detailed motion description>` on the last line.\n"
                "5. If the user requests an IMAGE: Output `IMAGE_PROMPT: <visual prompt>` on the last line.\n"
                "6. If the user requests a PRESENTATION: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                "7. If the user requests a PDF/REPORT: Conclude with `GENERATE_PDF: <Title>`.\n"
            )
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1400,
                temp=0.25
            )

            status.write("Compiling production source code & mobile deployment bundle...")
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
            status.update(label="Enterprise AI Deployed with Cosmic HUD & Notebook Math!", state="complete", expanded=False)
            st.rerun()

# SECTION 2: CREATED AI WORKSPACE
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Live Custom AI Workspace",
        "🎙️ Add Your Own Voice to Your AI",
        "📱 Install as Mobile App",
        "📦 Export Standalone Code & ZIP"
    ])

    # TAB 2: ADD YOUR OWN VOICE TO YOUR AI
    with tab2:
        st.subheader("🎙️ Add Your Own Voice to Your AI")
        st.caption("Record and clone your voice characteristics so your AI speaks directly in your tone, pitch, and style.")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.write("### 1. Tune Vocal Pitch & Speed")
            st.session_state.voice_pitch = st.slider(
                "Voice Pitch (Match Your Tone)",
                min_value=0.5,
                max_value=2.0,
                value=float(st.session_state.voice_pitch),
                step=0.05,
                help="Adjust this to match your voice: 0.7-0.9 for deeper voices, 1.0-1.4 for lighter voices."
            )
            st.session_state.voice_rate = st.slider(
                "Speaking Rate (Match Your Tempo)",
                min_value=0.6,
                max_value=1.6,
                value=float(st.session_state.voice_rate),
                step=0.05,
                help="Adjust how rapidly the AI delivers sentences."
            )
            st.session_state.voice_autoplay = st.toggle(
                "⚡ Auto-Speak in My Voice (Automatically talk when answering)",
                value=st.session_state.voice_autoplay,
                help="When enabled, the AI will immediately speak every response in your voice without clicking."
            )

        with col_v2:
            st.write("### 2. Record Your Voice Sample")
            st.write("Record a 5-10 second sample reading any sentence to calibrate your AI's voice memory:")
            audio_sample = st.audio_input("Click mic to record your voice sample:")
            if audio_sample:
                st.session_state.user_voice_sample = audio_sample.getvalue()
                st.success("✅ Voice sample captured! Your vocal timbre is now bound to this AI.")

            st.write("### 3. Test How Your AI Sounds")
            test_phrase = "Hello! I am your AI assistant, and I am now speaking in your customized voice."
            test_js = f"""
            <div>
                <button onclick="
                    window.speechSynthesis.cancel();
                    const u = new SpeechSynthesisUtterance('{test_phrase}');
                    u.pitch = {st.session_state.voice_pitch};
                    u.rate = {st.session_state.voice_rate};
                    const voices = window.speechSynthesis.getVoices();
                    if (voices.length > 0) {{
                        const preferred = voices.find(v => v.lang.startsWith('en') && !v.name.includes('Google') && !v.name.includes('Bad'));
                        if (preferred) u.voice = preferred;
                    }}
                    window.speechSynthesis.speak(u);
                " style="
                    background: linear-gradient(90deg, #059669, #d97706);
                    color: white; border: none; padding: 10px 18px; border-radius: 6px;
                    cursor: pointer; font-weight: bold;">
                    ▶️ Test My AI Voice
                </button>
            </div>
            """
            components.html(test_js, height=50)

        st.markdown("---")
        st.subheader("Persona & Reasoning Directives")
        st.session_state.ai_creativity = st.slider(
            "Creativity (Temperature)", min_value=0.0, max_value=1.0, value=float(st.session_state.ai_creativity), step=0.05
        )
        st.session_state.ai_custom_trait = st.text_area(
            "Custom Persona Traits & Math Notation Guidelines:",
            value=st.session_state.ai_custom_trait
        )
        st.success("✅ Your voice profile and math standards are saved and active across your AI workspace!")

    # TAB 3: MOBILE APP INSTALLATION (PWA)
    with tab3:
        st.subheader("📱 Install Created AI on Your Mobile Phone")
        current_url = "https://student-app-cfuamr4f9gqwo2azrdqwwr.streamlit.app"
        app_qr_bytes = build_qr_bytes(current_url)

        col_m1, col_m2 = st.columns([1.2, 2])
        with col_m1:
            st.image(app_qr_bytes, caption="Scan with Phone Camera", width=220)
            st.markdown(f"🔗 **Direct Mobile Link:** [Open on Phone]({current_url})")

        with col_m2:
            st.markdown("""
            ### How to Install to Your Home Screen:
            **Android:** Scan QR -> Tap Chrome menu (⋮) -> Tap **"Install app"** or **"Add to Home screen"**.
            **iPhone:** Scan QR -> Open in Safari -> Tap Share button -> Tap **"Add to Home Screen"**.
            """)

    # TAB 4: STANDALONE EXPORT & ZIP
    with tab4:
        st.subheader("Standalone Python Code & Deployment Bundle")
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

    # TAB 1: WORKSPACE
    with tab1:
        st.subheader("2. Your Active Custom AI (Cosmic HUD Interface Active)")
        st.caption(f"Objective: {app_info['goal']} | Inner Core: Mega Rayquaza Active")

        st.markdown("#### 📁 File Intake, Voice & Cloud Memory")
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
                if not st.session_state.persisted_doc_url:
                    with st.spinner("Publishing document to cloud storage for instant QR download..."):
                        hosted_url = upload_to_temp_host(raw_bytes, uploaded_doc.name)
                        st.session_state.persisted_doc_url = hosted_url

        with col_mic:
            st.write("🎙️ **Voice Assistant Controls**")
            render_voice_interface(
                element_id="chat_voice_ctrl",
                pitch=st.session_state.voice_pitch,
                rate=st.session_state.voice_rate,
                autoplay=st.session_state.voice_autoplay
            )

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

        # Render conversation history with Cosmic HUD design (Replacing plain boxes)
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-bubble-container">
                    <div class="user-bubble">
                        <div class="user-tag">👤 You (Pilot Commander)</div>
                        <div>{msg.get('text_content', '')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ai-bubble-container">
                    <div class="ai-bubble">
                        <div class="ai-tag">🐉 Mega Rayquaza Core Engine</div>
                """, unsafe_allow_html=True)

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

                st.markdown("</div></div>", unsafe_allow_html=True)

        user_input = st.chat_input("Speak or type to your AI (e.g. 'show an electronic prototype circuit for a smart door lock')...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            st.markdown(f"""
            <div class="user-bubble-container">
                <div class="user-bubble">
                    <div class="user-tag">👤 You (Pilot Commander)</div>
                    <div>{user_input}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Mega Rayquaza Council assembling full deliverable & notebook notation..."):
                retrieved_context = ""
                if st.session_state.get("persisted_doc_chunks"):
                    retrieved_context = retrieve_relevant_context(st.session_state.persisted_doc_chunks, user_input)

                council_system = (
                    f"You are the deployed expert AI system created for: {app_info['goal']}.\n"
                    f"{app_info['system_prompt']}\n\n"
                    f"USER-CONFIGURED PERSONALITY & TRAITS:\n{st.session_state.ai_custom_trait}\n\n"
                    "STRICT OPERATIONAL DIRECTIVES:\n"
                    "1. DELIVER COMPLETE PRODUCTS: Do not produce half answers or outlines. If designing an electronic prototype, provide the exact parts list, complete pin-to-pin wiring diagram, and full working microcontroller code.\n"
                    "2. NOTEBOOK-STYLE MATHEMATICAL NOTATION: Never output raw syntax like `x**2` or `sqrt(...)` in explanations. Always format all mathematics, equations, formulas, fractions, and matrices using LaTeX: `$inline$` for inline terms and `$$display$$` for standalone equations.\n"
                    "3. IF PERFORMING COMPUTATIONS: Provide clean step-by-step arithmetic first and calculate exact results.\n"
                    "4. If the user asks for a QR CODE: Output `GENERATE_QR: <url or string>`.\n"
                    "5. If the user requests a VIDEO: Output `VIDEO_PROMPT: <vivid visual prompt>` on the last line.\n"
                    "6. If the user requests an IMAGE OR PROTOTYPE DIAGRAM: Output `IMAGE_PROMPT: <visual prompt>` on the last line.\n"
                    "7. If the user requests a PRESENTATION: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                    "8. If WRITING A REPORT/PDF: Conclude with `GENERATE_PDF: <Title>`.\n"
                )

                if st.session_state.get("persisted_doc_url"):
                    council_system += f"\n\nLIVE DOCUMENT URL: {st.session_state.persisted_doc_url}\n"
                if retrieved_context:
                    council_system += f"\n\n--- RELEVANT DOCUMENT EXCERPTS ---\n{retrieved_context}\n--- END EXCERPTS ---\n"

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
                    qr_bytes = None
                    qr_match = re.search(r"GENERATE_QR:\s*(.+)", reply, re.IGNORECASE)
                    if qr_match:
                        raw_qr = qr_match.group(1).strip()
                        if "document" in raw_qr.lower() and st.session_state.get("persisted_doc_url"):
                            raw_qr = st.session_state.persisted_doc_url
                        qr_bytes = build_qr_bytes(raw_qr)
                    elif "qr" in user_input.lower() and st.session_state.get("persisted_doc_url"):
                        qr_bytes = build_qr_bytes(st.session_state.persisted_doc_url)

                    repl_output = None
                    plot_fig = None
                    code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", reply, re.DOTALL)
                    if code_match and ("plt" in code_match.group(1) or "print" in code_match.group(1) or "sp." in code_match.group(1)):
                        code_to_exec = code_match.group(1)
                        success, stdout_txt, fig = run_sandboxed_python(code_to_exec)
                        if success:
                            repl_output = stdout_txt if stdout_txt.strip() else None
                            plot_fig = fig

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

                    image_url = None
                    img_match = re.search(r"IMAGE_PROMPT:\s*(.+)", reply, re.IGNORECASE)
                    if img_match and not vid_match:
                        raw_img = re.sub(r"[^\w\s,.-]", "", img_match.group(1).strip())
                        encoded_i = urllib.parse.quote(raw_img[:250])
                        image_url = f"https://image.pollinations.ai/prompt/{encoded_i}?width=768&height=512&nologo=true"

                    pdf_data = None
                    pdf_title = "Document"
                    pdf_match = re.search(r"GENERATE_PDF:\s*(.+)", reply, re.IGNORECASE)
                    if pdf_match:
                        pdf_title = pdf_match.group(1).strip()
                        clean_doc = re.sub(r"GENERATE_PDF:\s*.+", "", reply, flags=re.IGNORECASE).strip()
                        pdf_data = build_pdf_bytes(pdf_title, clean_doc)

                    pptx_data = None
                    json_match = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", reply, re.DOTALL)
                    if json_match:
                        try:
                            parsed = json.loads(json_match.group(1))
                            if "slides" in parsed:
                                pptx_data = build_pptx_bytes(parsed)
                        except Exception:
                            pass

                    cleaned = re.sub(r"GENERATE_QR:\s*.+", "", reply, flags=re.IGNORECASE)
                    cleaned = re.sub(r"VIDEO_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"IMAGE_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"GENERATE_PDF:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", cleaned, flags=re.DOTALL)
                    cleaned = re.sub(r"```(?:python)?\s*.*?fig\s*=.*?\s*```", "", cleaned, flags=re.DOTALL).strip()

                    new_idx = len(st.session_state.chat_history)
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
                    st.rerun()
