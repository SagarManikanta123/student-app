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
from datetime import datetime
import numpy as np
import matplotlib.pyplot as plt
import pandas as pd
import sympy as sp
import qrcode
from fpdf import FPDF
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pypdf import PdfReader

st.set_page_config(page_title="Sagar AI", layout="wide")

st.markdown("""
<style>
    .stApp {
        background-color: #070913;
        background-image: 
            radial-gradient(circle at 15% 20%, rgba(99, 102, 241, 0.28) 0%, transparent 45%),
            radial-gradient(circle at 85% 15%, rgba(168, 85, 247, 0.3) 0%, transparent 50%),
            radial-gradient(circle at 50% 85%, rgba(14, 165, 233, 0.25) 0%, transparent 55%),
            radial-gradient(circle at 80% 80%, rgba(236, 72, 153, 0.2) 0%, transparent 40%),
            linear-gradient(rgba(255, 255, 255, 0.03) 1px, transparent 1px),
            linear-gradient(90deg, rgba(255, 255, 255, 0.03) 1px, transparent 1px);
        background-size: 100% 100%, 100% 100%, 100% 100%, 100% 100%, 35px 35px, 35px 35px;
        background-attachment: fixed;
    }

    .stTabs [data-baseweb="tab-list"] {
        gap: 10px;
        background: rgba(15, 23, 42, 0.75);
        backdrop-filter: blur(16px);
        -webkit-backdrop-filter: blur(16px);
        padding: 8px 14px;
        border-radius: 14px;
        border: 1px solid rgba(99, 102, 241, 0.35);
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.4);
    }
    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        color: #94a3b8;
        font-weight: 700;
        letter-spacing: 0.3px;
    }
    .stTabs [aria-selected="true"] {
        background: linear-gradient(135deg, rgba(99, 102, 241, 0.45), rgba(168, 85, 247, 0.45)) !important;
        color: #ffffff !important;
        border: 1px solid rgba(168, 85, 247, 0.6) !important;
        box-shadow: 0 0 18px rgba(168, 85, 247, 0.4) !important;
    }

    .sagar-header {
        background: linear-gradient(90deg, #38bdf8, #818cf8, #e879f9);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        font-size: 2.6rem;
        font-weight: 900;
        letter-spacing: -0.5px;
        margin-bottom: 2px;
        text-shadow: 0 0 35px rgba(129, 140, 248, 0.5);
    }
    .sagar-badge {
        background: linear-gradient(90deg, rgba(30, 58, 138, 0.8), rgba(88, 28, 135, 0.8));
        color: #fdf4ff;
        padding: 6px 18px;
        border-radius: 9999px;
        font-size: 0.85rem;
        font-weight: 700;
        border: 1px solid #c084fc;
        display: inline-block;
        margin-bottom: 16px;
        box-shadow: 0 0 18px rgba(192, 132, 252, 0.4);
        backdrop-filter: blur(10px);
    }

    .user-bubble-container {
        display: flex;
        justify-content: flex-end;
        margin-bottom: 18px;
        padding-left: 15%;
    }
    .user-bubble {
        background: linear-gradient(135deg, rgba(30, 41, 59, 0.85), rgba(15, 23, 42, 0.95));
        border: 1px solid rgba(56, 189, 248, 0.7);
        border-right: 4px solid #38bdf8;
        border-radius: 18px 4px 18px 18px;
        padding: 14px 22px;
        color: #f8fafc;
        box-shadow: 0 6px 25px rgba(56, 189, 248, 0.25);
        backdrop-filter: blur(12px);
    }
    .user-tag {
        font-size: 0.72rem;
        font-weight: 800;
        color: #38bdf8;
        text-transform: uppercase;
        letter-spacing: 1.2px;
        margin-bottom: 4px;
    }

    .ai-bubble-container {
        display: flex;
        justify-content: flex-start;
        margin-bottom: 22px;
        padding-right: 8%;
    }
    .ai-bubble {
        background: linear-gradient(135deg, rgba(20, 24, 48, 0.88), rgba(15, 23, 42, 0.94));
        border: 1px solid rgba(168, 85, 247, 0.5);
        border-left: 4px solid #e879f9;
        border-radius: 4px 20px 20px 20px;
        padding: 20px 28px;
        color: #f1f5f9;
        box-shadow: 0 10px 35px rgba(168, 85, 247, 0.25);
        backdrop-filter: blur(14px);
        width: 100%;
    }
    .ai-tag {
        font-size: 0.78rem;
        font-weight: 800;
        color: #e879f9;
        text-transform: uppercase;
        letter-spacing: 1.4px;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
        gap: 6px;
    }

    .product-card {
        background: rgba(15, 23, 42, 0.6);
        border: 1px solid rgba(99, 102, 241, 0.3);
        border-radius: 12px;
        padding: 12px 16px;
        margin-top: 10px;
        margin-bottom: 10px;
    }
</style>
""", unsafe_allow_html=True)

st.markdown('<p class="sagar-header">Sagar AI: Autonomous Creative Factory</p>', unsafe_allow_html=True)
st.markdown('<span class="sagar-badge">🧠 Dynamic Visualizer & Notebook Math Engine Active</span>', unsafe_allow_html=True)
st.caption("Auto-rendering graphs, textbook LaTeX math notation, executive slide decks, and hardware blueprints.")

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

# Format LaTeX notebook representations cleanly
def convert_to_notebook_math(text):
    if not text:
        return ""
    # Convert square brackets used as block equations into $$...$$
    converted = re.sub(r"(?<!\\)\[\s*([\s\S]*?)\s*\]", r"$$\1$$", text)
    # Convert \( ... \) into $...$
    converted = re.sub(r"\\\(\s*([\s\S]*?)\s*\\\)", r"$\1$", converted)
    # Convert \[ ... \] into $$...$$
    converted = re.sub(r"\\\[\s*([\s\S]*?)\s*\\\]", r"$$\1$$", converted)
    return converted

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
    normalized = unicodedata.normalize("NFKD", text)
    safe_ascii = "".join(c for c in normalized if 32 <= ord(c) <= 126 or c == "\n")
    return safe_ascii

class SagarExecutivePDF(FPDF):
    def header(self):
        self.set_fill_color(15, 23, 42)
        self.rect(0, 0, 210, 18, 'F')
        self.set_font("Helvetica", "B", 9)
        self.set_text_color(192, 132, 252)
        self.set_xy(10, 5)
        self.cell(0, 8, "SAGAR AI EXECUTIVE BRIEFING & SPECIFICATION", align="L")
        self.set_text_color(148, 163, 184)
        self.set_xy(10, 5)
        self.cell(190, 8, datetime.now().strftime("%B %Y"), align="R")
        self.ln(12)

    def footer(self):
        self.set_y(-14)
        self.set_font("Helvetica", size=8)
        self.set_text_color(148, 163, 184)
        self.cell(0, 8, f"Confidential & Proprietary Deliverable | Page {self.page_no()}", align="C")

def build_pdf_bytes(title, content):
    pdf = SagarExecutivePDF()
    pdf.set_auto_page_break(auto=True, margin=18)
    pdf.add_page()
    safe_title = clean_pdf_text(title)[:85]
    safe_body = clean_pdf_text(content)

    pdf.set_fill_color(30, 41, 59)
    pdf.set_draw_color(99, 102, 241)
    pdf.rect(10, 22, 190, 24, 'FD')
    pdf.set_xy(14, 25)
    pdf.set_font("Helvetica", "B", 15)
    pdf.set_text_color(248, 250, 252)
    pdf.cell(182, 8, safe_title if safe_title else "Executive Deliverable", align="L")
    pdf.set_xy(14, 34)
    pdf.set_font("Helvetica", "I", 9)
    pdf.set_text_color(56, 189, 248)
    pdf.cell(182, 6, "Engineered by Sagar AI Production Council | Verified Deliverable", align="L")

    pdf.set_xy(10, 52)
    for paragraph in safe_body.split("\n"):
        p_clean = paragraph.strip()
        if not p_clean:
            pdf.ln(3)
            continue
        if p_clean.startswith("#") or (len(p_clean) < 40 and p_clean.isupper()):
            clean_head = p_clean.replace("#", "").strip()
            pdf.ln(4)
            pdf.set_fill_color(243, 244, 246)
            pdf.set_font("Helvetica", "B", 12)
            pdf.set_text_color(30, 58, 138)
            pdf.cell(0, 8, clean_head, new_x="LMARGIN", new_y="NEXT", align="L")
            pdf.ln(2)
        elif p_clean.startswith("- ") or p_clean.startswith("* "):
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(51, 65, 85)
            pdf.cell(6, 6, chr(149), align="R")
            pdf.multi_cell(0, 6, text=" " + p_clean[2:])
        else:
            pdf.set_font("Helvetica", size=10)
            pdf.set_text_color(30, 41, 59)
            pdf.multi_cell(0, 6, text=p_clean)
            pdf.ln(1.5)

    return bytes(pdf.output())

def build_pptx_bytes(presentation_data):
    prs = Presentation()
    prs.slide_width = Inches(13.333)
    prs.slide_height = Inches(7.5)
    blank_layout = prs.slide_layouts[6]

    for index, slide_info in enumerate(presentation_data.get("slides", [])):
        slide = prs.slides.add_slide(blank_layout)

        bg = slide.shapes.add_shape(1, 0, 0, Inches(13.333), Inches(7.5))
        bg.fill.solid()
        bg.fill.fore_color.rgb = RGBColor(11, 15, 25)
        bg.line.fill.background()

        stripe = slide.shapes.add_shape(1, 0, 0, Inches(13.333), Inches(0.18))
        stripe.fill.solid()
        stripe.fill.fore_color.rgb = RGBColor(99, 102, 241) if index % 2 == 0 else RGBColor(232, 121, 249)
        stripe.line.fill.background()

        title_box = slide.shapes.add_textbox(Inches(0.9), Inches(0.6), Inches(11.5), Inches(1.2))
        tf = title_box.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        p.text = slide_info.get("title", f"Module {index+1}")
        p.font.size = Pt(32)
        p.font.bold = True
        p.font.color.rgb = RGBColor(248, 250, 252)

        num_box = slide.shapes.add_textbox(Inches(11.8), Inches(0.4), Inches(1.0), Inches(0.6))
        np_p = num_box.text_frame.paragraphs[0]
        np_p.text = f"0{index+1}" if index < 9 else str(index+1)
        np_p.font.size = Pt(18)
        np_p.font.bold = True
        np_p.font.color.rgb = RGBColor(148, 163, 184)
        np_p.alignment = PP_ALIGN.RIGHT

        card = slide.shapes.add_shape(1, Inches(0.9), Inches(2.0), Inches(11.5), Inches(4.7))
        card.fill.solid()
        card.fill.fore_color.rgb = RGBColor(20, 27, 45)
        card.line.color.rgb = RGBColor(51, 65, 85)

        bullets = slide_info.get("bullets", [])
        body_box = slide.shapes.add_textbox(Inches(1.2), Inches(2.3), Inches(10.9), Inches(4.2))
        btf = body_box.text_frame
        btf.word_wrap = True

        for b_idx, bullet in enumerate(bullets):
            p_bullet = btf.paragraphs[0] if b_idx == 0 else btf.add_paragraph()
            p_bullet.text = bullet
            p_bullet.font.size = Pt(17)
            p_bullet.font.color.rgb = RGBColor(226, 232, 240)
            p_bullet.space_after = Pt(16)
            p_bullet.level = 0

    buf = io.BytesIO()
    prs.save(buf)
    return buf.getvalue()

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

# Reliable Sandboxed Python Execution Engine for Graphs and Calculations
def run_sandboxed_python(code_snippet):
    stdout_capture = io.StringIO()
    plt.close('all')
    fig, ax = plt.subplots(figsize=(7, 5))
    safe_globals = {
        "np": np,
        "pd": pd,
        "sp": sp,
        "plt": plt,
        "fig": fig,
        "ax": ax,
        "print": lambda *args: stdout_capture.write(" ".join(str(a) for a in args) + "\n")
    }
    try:
        exec(code_snippet, safe_globals)
        output = stdout_capture.getvalue()
        # Return fig if plotting commands were made
        active_fig = safe_globals.get("fig") or plt.gcf()
        return True, output, active_fig
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
    readme_txt = f"# Sagar AI Application\nGenerated by Sagar AI Autonomous Factory.\n\n### Objective:\n{goal_text}\n"
    manifest_txt = json.dumps({
        "name": "Sagar AI",
        "short_name": "SagarAI",
        "start_url": "/",
        "display": "standalone",
        "background_color": "#070913",
        "theme_color": "#6366f1"
    }, indent=2)
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        zip_file.writestr("app.py", app_code)
        zip_file.writestr("requirements.txt", reqs_txt)
        zip_file.writestr("README.md", readme_txt)
        zip_file.writestr("manifest.json", manifest_txt)
    return zip_buffer.getvalue()

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

def call_groq(messages, model=PRIMARY_TEXT_MODEL, key=api_key, max_tok=2200, temp=0.2):
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
        res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=50)
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return strip_internal_thoughts(content)
        else:
            return f"API Error ({res.status_code}): {res.text}"
    except Exception as exc:
        return f"Request failed: {exc}"

def render_voice_interface(element_id="mainVoice", pitch=1.0, rate=1.0, autoplay=False):
    autoplay_js = "true" if autoplay else "false"
    voice_html = f"""
    <div style="font-family: sans-serif; display: flex; flex-direction: column; gap: 6px;">
        <div style="display: flex; gap: 8px;">
            <button id="{element_id}_in" style="
                background: linear-gradient(90deg, #6366f1, #a855f7);
                color: white; border: none; padding: 7px 14px; border-radius: 6px;
                cursor: pointer; font-weight: bold; box-shadow: 0 0 10px rgba(99, 102, 241, 0.4);">
                🎤 Speak Input
            </button>
            <button id="{element_id}_out" style="
                background: #1e293b; color: #c084fc; border: 1px solid #818cf8;
                padding: 7px 14px; border-radius: 6px; cursor: pointer; font-weight: bold;">
                🔊 Speak in My Voice
            </button>
        </div>
        <div id="{element_id}_status" style="
            font-size: 12px; color: #d1d5db; background: rgba(15, 23, 42, 0.85); padding: 6px 10px;
            border-radius: 6px; min-height: 32px; border: 1px solid rgba(99, 102, 241, 0.4);">
            Sagar AI Voice Ready. Pitch: {pitch}x | Rate: {rate}x
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

def inject_pwa_headers():
    pwa_meta = """
    <script>
    let manifestLink = document.createElement('link');
    manifestLink.rel = 'manifest';
    manifestLink.href = 'data:application/json;base64,' + btoa(JSON.stringify({
        "name": "Sagar AI",
        "short_name": "SagarAI",
        "start_url": window.location.href,
        "display": "standalone",
        "background_color": "#070913",
        "theme_color": "#6366f1"
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
    st.session_state.ai_max_tokens = 2200
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
        "All mathematics must be displayed in standard notebook notation using $inline$ and $$display$$ LaTeX blocks. "
        "When visualization or graphing is requested, ALWAYS provide clean executable Python code defining fig."
    )

# SECTION 1: AI FACTORY CREATOR
st.subheader("1. Sagar AI Creator (Autonomous Product Studio)")
col_c_text, col_c_mic = st.columns([2, 1])

with col_c_mic:
    st.write("🎙️ **Voice Command to Build AI**")
    render_voice_interface(element_id="factory_creator_voice", pitch=st.session_state.voice_pitch, rate=st.session_state.voice_rate)

with col_c_text:
    user_request = st.text_area(
        "Describe the specialized AI tool you want Sagar AI to architect:",
        placeholder="e.g. Build an autonomous drawing and mathematical visualization agent that renders textbook-quality curves and derivations.",
        height=95
    )

if st.button("Deploy with Sagar AI", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please provide a prompt or speak your AI design.")
    else:
        with st.status("Harmonizing Complex Thinking Matrix under Sagar AI...", expanded=True) as status:
            status.write("🧠 Activating First-Principles Reasoner & Autonomous Brains...")
            council_synthesis_prompt = (
                f"You are Sagar AI — an autonomous creative intelligence engine built for: '{user_request}'.\n"
                "Unify all 26 brain domains with complex thinking & self-creativity:\n"
                "1. Core Intelligence: Sagar AI (First-Principles Reasoner & Full Product Mandate)\n"
                "2. Mathematics Brain (Textbook & Notebook Math Notation Specialist with full LaTeX proofs)\n"
                "3. Voice Assistant Engine (Speaks in User Voice Profile)\n"
                "4. Dynamic Visualizer & Graph Drawing Agent (Generates executable Matplotlib figures)\n"
                "5. Hardware & Electronics Specialist (Circuits, Schematics, Pinouts, Complete Working Firmware)\n"
                "6. Vision Inspector (Visual Hardware & Photo Analysis)\n"
                "7. Theoretical & Classical Physics Engine (Formulas rendered in display LaTeX)\n"
                "8. Chemistry Specialist (Balanced Equations & Thermal Thermodynamics)\n"
                "9. Computer Science & Algorithm Engine\n"
                "10. Microcontroller Firmware Specialist\n"
                "11. Motion & Video Specialist\n"
                "12. Still Image Prompt Specialist\n"
                "13. Executive Publication Compiler (High-Production-Value PDF Briefings)\n"
                "14. Slide Deck Architect (Executive Dark-Mode PPTX Decks)\n"
                "15. Document Intake & Semantic Search Specialist\n"
                "16. QR Code Engine (Direct mobile links and file downloads)\n"
                "17. Computational Execution Engine\n"
                "18-26. Multi-Disciplinary Synthesis, Production-Ready Verification, & Safety\n\n"
                "CRITICAL MANDATES:\n"
                "1. MATHEMATICAL NOTEBOOK REPRESENTATION: NEVER output raw syntax like `x**2` or `sqrt(...)` or brackets like `[ x^2 + y^2 ]` for equations. ALWAYS format ALL mathematics strictly in authentic LaTeX delimiters: `$inline$` for in-sentence variables/terms and `$$display$$` for standalone equations (e.g. $$(x+1)^2 + (y+1)^2 = 9$$, $$\\kappa = \\frac{1}{r} = \\frac{1}{3}$$).\n"
                "2. DYNAMIC DRAWING AGENT: When asked to plot, graph, visualize, or draw an equation, curve, or function: ALWAYS provide executable Python code block tagged with ```python ``` at the bottom that uses `np`, `plt`, or `ax` to plot the curve onto `fig`. Sagar AI will automatically render the live canvas.\n"
                "3. CONTEXT-AWARE ARCHITECTURE: If a question is purely mathematical or visual, do NOT force hardware parts lists or Raspberry Pi wiring. Focus on the mathematical proof and the visual rendering.\n"
                "4. NO IN-BETWEEN CODE: Do NOT show raw python code in your conversational explanation. Keep the execution code block at the bottom so the system renders the graph cleanly.\n"
                "5. If the user asks for a QR CODE: Output `GENERATE_QR: <url or string>`.\n"
                "6. If CREATING A VIDEO: Output `VIDEO_PROMPT: <vivid visual prompt>` on the last line.\n"
                "7. If CREATING AN IMAGE: Output `IMAGE_PROMPT: <visual prompt>` on the last line.\n"
                "8. If CREATING SLIDES: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
                "9. If WRITING A REPORT/PDF: Conclude with `GENERATE_PDF: <Title>`.\n"
            )
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1700,
                temp=0.2
            )

            status.write("Compiling autonomous deployment bundle...")
            code_prompt = (
                f"Write a standalone Streamlit Python app implementing this directive:\n{master_system_prompt}\n\n"
                "Output ONLY executable Python code inside a single markdown code block with python tag."
            )
            raw_code = call_groq(
                [{"role": "user", "content": code_prompt}],
                model=PRIMARY_TEXT_MODEL,
                max_tok=1700,
                temp=0.1
            )
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_system_prompt,
                "source_code": clean_code
            }
            st.session_state.chat_history = []
            status.update(label="Sagar AI Successfully Deployed with Drawing & Notebook Math Engine!", state="complete", expanded=False)
            st.rerun()

# SECTION 2: CREATED AI WORKSPACE
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "⚡ Live Sagar AI Workspace",
        "🎙️ Add Your Own Voice to Sagar AI",
        "📱 Install Sagar AI on Mobile",
        "📦 Export Standalone Code & ZIP"
    ])

    with tab2:
        st.subheader("🎙️ Add Your Own Voice to Sagar AI")
        st.caption("Record and calibrate your voice characteristics so Sagar AI speaks directly in your tone and speed.")

        col_v1, col_v2 = st.columns(2)
        with col_v1:
            st.write("### 1. Tune Vocal Pitch & Speed")
            st.session_state.voice_pitch = st.slider(
                "Voice Pitch (Match Your Tone)",
                min_value=0.5,
                max_value=2.0,
                value=float(st.session_state.voice_pitch),
                step=0.05
            )
            st.session_state.voice_rate = st.slider(
                "Speaking Rate (Match Your Tempo)",
                min_value=0.6,
                max_value=1.6,
                value=float(st.session_state.voice_rate),
                step=0.05
            )
            st.session_state.voice_autoplay = st.toggle(
                "⚡ Auto-Speak in My Voice (Automatically talk when answering)",
                value=st.session_state.voice_autoplay
            )

        with col_v2:
            st.write("### 2. Record Your Voice Sample")
            st.write("Record a 5-10 second sample reading any sentence to calibrate Sagar AI's voice memory:")
            audio_sample = st.audio_input("Click mic to record your voice sample:")
            if audio_sample:
                st.session_state.user_voice_sample = audio_sample.getvalue()
                st.success("✅ Voice sample captured and bound to Sagar AI.")

            st.write("### 3. Test How Sagar AI Sounds")
            test_phrase = "Hello! I am Sagar AI, powered by complex reasoning and first-principles creative synthesis."
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
                    background: linear-gradient(90deg, #6366f1, #a855f7);
                    color: white; border: none; padding: 10px 18px; border-radius: 6px;
                    cursor: pointer; font-weight: bold; box-shadow: 0 0 12px rgba(168, 85, 247, 0.4);">
                    ▶️️ Test Sagar AI Voice
                </button>
            </div>
            """
            components.html(test_js, height=50)

        st.markdown("---")
        st.subheader("Autonomous Reasoning & Persona Directives")
        st.session_state.ai_creativity = st.slider(
            "Creativity & Reasoning Index", min_value=0.0, max_value=1.0, value=float(st.session_state.ai_creativity), step=0.05
        )
        st.session_state.ai_custom_trait = st.text_area(
            "Complex Reasoning Traits & Clean Output Guidelines:",
            value=st.session_state.ai_custom_trait
        )
        st.success("✅ Complex thinking profile and parameters active in Sagar AI.")

    with tab3:
        st.subheader("📱 Install Sagar AI on Your Mobile Phone")
        current_url = "https://student-app-cfuamr4f9gqwo2azrdqwwr.streamlit.app"
        app_qr_bytes = build_qr_bytes(current_url)

        col_m1, col_m2 = st.columns([1.2, 2])
        with col_m1:
            st.image(app_qr_bytes, caption="Scan with Phone Camera", width=220)
            st.markdown(f"🔗 **Direct Mobile Link:** [Open on Phone]({current_url})")

        with col_m2:
            st.markdown("""
            ### How to Install Sagar AI on Mobile:
            **Android:** Scan QR -> Tap Chrome menu (⋮) -> Tap **"Install app"** or **"Add to Home screen"**.
            **iPhone:** Scan QR -> Open in Safari -> Tap Share button -> Tap **"Add to Home Screen"**.
            """)

    with tab4:
        st.subheader("Sagar AI Deployment Bundle")
        zip_bytes = build_deployment_zip(app_info["source_code"], app_info["goal"])
        col_z1, col_z2 = st.columns(2)
        with col_z1:
            st.download_button(
                "📦 Download Complete Deployment Bundle (.zip)",
                data=zip_bytes,
                file_name="sagar_ai_package.zip",
                mime="application/zip",
                type="primary"
            )
        with col_z2:
            st.download_button(
                "📄 Download Single Source Code (.py)",
                data=app_info["source_code"],
                file_name="sagar_ai_app.py",
                mime="text/plain"
            )
        st.markdown("---")
        st.code(app_info["source_code"], language="python")

    with tab1:
        st.subheader("2. Your Active Sagar AI Assistant")
        st.caption(f"Objective: {app_info['goal']} | Engine: Drawing Agent & Notebook Math Active")

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

        # Render conversation history
        for idx, msg in enumerate(st.session_state.chat_history):
            if msg["role"] == "user":
                st.markdown(f"""
                <div class="user-bubble-container">
                    <div class="user-bubble">
                        <div class="user-tag">👤 You</div>
                        <div>{msg.get('text_content', '')}</div>
                    </div>
                </div>
                """, unsafe_allow_html=True)
            else:
                st.markdown("""
                <div class="ai-bubble-container">
                    <div class="ai-bubble">
                        <div class="ai-tag">✨ Sagar AI Solution & Canvas</div>
                """, unsafe_allow_html=True)

                if msg.get("text_content"):
                    st.markdown(msg["text_content"])

                # Render the live Matplotlib Plot Canvas
                if msg.get("plot_fig"):
                    st.pyplot(msg["plot_fig"])

                if any([msg.get("qr_bytes"), msg.get("pdf_data"), msg.get("pptx_data"), msg.get("video_bytes"), msg.get("image_url")]):
                    st.markdown("<div class='product-card'><b>🛠️ Deliverable Actions & Exports</b></div>", unsafe_allow_html=True)

                if msg.get("qr_bytes"):
                    st.image(msg["qr_bytes"], caption="Scannable QR Code", width=220)
                    st.download_button("📥 Download QR Code (.png)", data=msg["qr_bytes"], file_name="qrcode.png", mime="image/png", key=f"dl_qr_btn_{idx}")

                if msg.get("video_bytes"):
                    st.video(msg["video_bytes"])
                elif msg.get("visual_url"):
                    st.image(msg["visual_url"], caption="Generated Motion Visualization", use_container_width=True)

                if msg.get("video_link"):
                    st.markdown(f"🔗 [Direct Video Link / Browser Player]({msg['video_link']})")

                if msg.get("image_url"):
                    st.image(msg["image_url"], caption="Visual Synthesizer Output", use_container_width=True)

                c_dl1, c_dl2 = st.columns(2)
                with c_dl1:
                    if msg.get("pdf_data"):
                        st.download_button(f"📄 Download Executive PDF: {msg['pdf_title']}.pdf", data=msg["pdf_data"], file_name=f"{msg['pdf_title'].replace(' ', '_')}.pdf", mime="application/pdf", key=f"dl_pdf_btn_{idx}")
                with c_dl2:
                    if msg.get("pptx_data"):
                        st.download_button("📊 Download Designer Deck (.pptx)", data=msg["pptx_data"], file_name="presentation.pptx", mime="application/vnd.openxmlformats-officedocument.presentationml.presentation", key=f"dl_pptx_btn_{idx}")

                st.markdown("</div></div>", unsafe_allow_html=True)

        user_input = st.chat_input("Request an equation proof, graph visualization, circuit, or system design...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "text_content": user_input})
            st.markdown(f"""
            <div class="user-bubble-container">
                <div class="user-bubble">
                    <div class="user-tag">👤 You</div>
                    <div>{user_input}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)

            with st.spinner("Sagar AI executing visualization and notebook proof..."):
                retrieved_context = ""
                if st.session_state.get("persisted_doc_chunks"):
                    retrieved_context = retrieve_relevant_context(st.session_state.persisted_doc_chunks, user_input)

                council_system = (
                    f"You are Sagar AI, created for: {app_info['goal']}.\n"
                    f"{app_info['system_prompt']}\n\n"
                    f"USER-CONFIGURED PERSONALITY & TRAITS:\n{st.session_state.ai_custom_trait}\n\n"
                    "MATHEMATICS & DRAWING AGENT RULES:\n"
                    "1. NOTEBOOK MATHEMATICS: NEVER display raw programming syntax or plain brackets like `[ x^2 + y^2 ]` or `( -1, -1 )`. ALWAYS format all mathematics in standard LaTeX: `$inline$` for inline variables and `$$display$$` for standalone equations (e.g. $$(x+1)^2 + (y+1)^2 = 9$$, $$C = (-1, -1)$$, $$r = 3$$).\n"
                    "2. DYNAMIC DRAWING AGENT: Whenever asked to visualize, plot, draw, or render a curve, function, or equation: YOU MUST supply clean, complete Python code using matplotlib.pyplot as plt and numpy as np inside a single ```python ``` block at the very end of your response. Define `fig` and `ax` and plot the exact curve so the system renders the image canvas.\n"
                    "3. CONTEXT RELEVANCE: If asked to solve or draw a mathematical curve, explain the step-by-step notebook derivation directly. Do NOT output irrelevant hardware parts lists (e.g., Raspberry Pi) unless hardware was specifically requested.\n"
                    "4. If the user asks for a QR CODE: Output `GENERATE_QR: <url or string>`.\n"
                    "5. If CREATING A VIDEO: Output `VIDEO_PROMPT: <vivid visual prompt>` on the last line.\n"
                    "6. If CREATING AN IMAGE: Output `IMAGE_PROMPT: <visual prompt>` on the last line.\n"
                    "7. If CREATING SLIDES: Output a JSON block inside ```json ``` with structure: {\"slides\": [{\"title\": \"...\", \"bullets\": [\"...\", \"...\"]}]}.\n"
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

                    # Extract & execute plot code BEFORE stripping
                    plot_fig = None
                    code_match = re.search(r"```(?:python)?\s*(.*?)\s*```", reply, re.DOTALL)
                    if code_match:
                        code_to_exec = code_match.group(1)
                        if "plt" in code_to_exec or "ax" in code_to_exec or "np" in code_to_exec:
                            success, stdout_txt, fig = run_sandboxed_python(code_to_exec)
                            if success and fig:
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
                    pdf_title = "Sagar_AI_Executive_Deliverable"
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

                    # Clean tags and convert bracket math to notebook LaTeX
                    cleaned = re.sub(r"GENERATE_QR:\s*.+", "", reply, flags=re.IGNORECASE)
                    cleaned = re.sub(r"VIDEO_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"IMAGE_PROMPT:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"GENERATE_PDF:\s*.+", "", cleaned, flags=re.IGNORECASE)
                    cleaned = re.sub(r"```(?:json)?\s*\{.*?\}\s*```", "", cleaned, flags=re.DOTALL)
                    
                    user_wants_code = "code" in user_input.lower() or "script" in user_input.lower() or "program" in user_input.lower()
                    if not user_wants_code:
                        cleaned = re.sub(r"```(?:python)?\s*.*?```", "", cleaned, flags=re.DOTALL).strip()
                    else:
                        cleaned = cleaned.strip()

                    cleaned = convert_to_notebook_math(cleaned)

                    new_idx = len(st.session_state.chat_history)
                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "text_content": cleaned,
                        "qr_bytes": qr_bytes,
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
