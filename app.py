import streamlit as st
import requests
import re
import base64
import numpy as np
import matplotlib.pyplot as plt
from concurrent.futures import ThreadPoolExecutor

st.set_page_config(page_title="Creative Multi-Brain AI Factory", layout="wide")

st.title("Creative Multi-Brain AI Factory")
st.caption("14-Specialist Council: Vision, Creative Analogies, Manners/Tone, STEM, Humanities, Graphing & Master Synthesis")

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

def call_groq(messages, model=TEXT_MODEL, key=api_key, max_tok=800, temp=0.5):
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
        else:
            if "vision" in model:
                payload["model"] = "llama-3.2-90b-vision-preview"
                payload["max_tokens"] = 600
                fb = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload, timeout=35)
                if fb.status_code == 200:
                    msg = fb.json()["choices"][0]["message"]
                    return strip_internal_thoughts(msg.get("content") or msg.get("reasoning") or "")
                return f"Vision API Error: {fb.status_code} - {fb.text}"
            return f"API Error: {res.status_code} - {res.text}"
    except Exception as exc:
        return f"Request failed: {exc}"

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
    placeholder="e.g. Build an AI that understands photos, solves math and physics, creates graphs, and explains hardware with clear code and diagrams"
)

if st.button("Build Multi-Brain AI", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe what tool you want to create.")
    else:
        with st.status("Council Activating 14 Specialized Brains...", expanded=True) as status:
            req_lower = user_request.lower()

            active_specialists = [
                "Creative Analogy Specialist (Brain 1)",
                "Polite & Engaging Tone Specialist (Brain 2)",
                "Universal Study Tutor (Brain 3)"
            ]

            if any(w in req_lower for w in ["photo", "image", "picture", "scan", "document", "video", "see", "look", "diagram"]):
                active_specialists.append("Vision & Visual Media Specialist (Brain 4)")
            if any(w in req_lower for w in ["math", "sum", "equation", "calculus", "algebra", "arithmetic"]):
                active_specialists.append("Mathematics Specialist (Brain 5)")
            if any(w in req_lower for w in ["physics", "force", "motion", "gravity", "energy", "mechanics", "arduino", "circuit"]):
                active_specialists.append("Physics & Hardware Engineering Specialist (Brain 6)")
            if any(w in req_lower for w in ["chemistry", "reaction", "compound", "molecule", "element"]):
                active_specialists.append("Chemistry Specialist (Brain 7)")
            if any(w in req_lower for w in ["code", "coding", "program", "python", "developer", "software", "bug"]):
                active_specialists.append("Computer Science Specialist (Brain 8)")
            if any(w in req_lower for w in ["biology", "cell", "dna", "plant", "animal", "life", "medicine"]):
                active_specialists.append("Life Sciences Specialist (Brain 9)")
            if any(w in req_lower for w in ["history", "civics", "government", "social", "culture"]):
                active_specialists.append("History & Social Studies Specialist (Brain 10)")
            if any(w in req_lower for w in ["language", "english", "grammar", "literature", "essay"]):
                active_specialists.append("Language Arts Specialist (Brain 11)")
            if any(w in req_lower for w in ["graph", "plot", "draw", "chart", "visualize"]):
                active_specialists.append("Dynamic Visualization Engine (Brain 12)")

            active_specialists.append("Resilience & Guardrail Brain (Brain 13)")

            status.write(f"Active Specialists: {', '.join(active_specialists)}")

            def run_specialist_consult(name):
                prompt = (
                    f"You are the {name}. A user wants to build an AI for:\n'{user_request}'\n\n"
                    "Provide your 2 best rules to make this tool deeply creative, practical, and highly capable in your domain. "
                    "Focus on intuition, engaging explanations, and zero robotic jargon."
                )
                return name, call_groq([{"role": "user", "content": prompt}], max_tok=220, temp=0.6)

            status.write("🧠 Consulting active specialist brains in parallel...")
            specialist_directives = {}
            with ThreadPoolExecutor(max_workers=min(len(active_specialists), 6)) as executor:
                results = executor.map(run_specialist_consult, active_specialists)
                for name, directive in results:
                    if directive:
                        specialist_directives[name] = directive

            status.write("🧠 Brain 14: Council Synthesizer assembling full operational spec and code...")
            combined_domain_rules = "\n\n".join([f"### {k}\n{v}" for k, v in specialist_directives.items()])

            synthesis_prompt = (
                f"You are the Council Synthesizer (Brain 14). Combine these specialist directives for:\n'{user_request}'\n\n"
                f"Specialist Guidance:\n{combined_domain_rules}\n\n"
                "Synthesize a unified system directive that instructs the AI to be:\n"
                "1. Highly creative with clear analogies and examples.\n"
                "2. Respectful, encouraging, and articulate in manner.\n"
                "3. Thoroughly competent across all requested subjects (math, physics, hardware, circuits, code, photos).\n"
                "4. Free of meta-thinking or robotic outlines."
            )
            master_system_prompt = call_groq([{"role": "user", "content": synthesis_prompt}], max_tok=750, temp=0.4)

            code_prompt = (
                f"Write a standalone Python Streamlit app that implements this multi-domain assistant:\n{master_system_prompt}\n\n"
                "CRITICAL: Output ONLY valid Python code inside a single ```python ``` code block. Include all necessary imports."
            )
            raw_code = call_groq([{"role": "user", "content": code_prompt}], max_tok=1800, temp=0.1)
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_system_prompt,
                "source_code": clean_code,
                "active_specialists": active_specialists
            }
            st.session_state.chat_history = []
            status.update(label="Creative Multi-Brain AI Ready!", state="complete", expanded=False)
            st.rerun()

# Workspace UI
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live Custom AI Workspace", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Autonomous Multi-Brain Council Active")
        st.caption(f"Specialists: {', '.join(app_info['active_specialists'])}")

        st.markdown("#### 📷 Image & Media Input")
        uploaded_file = st.file_uploader(
            "Upload a photo, diagram, circuit, or document:",
            type=["png", "jpg", "jpeg"],
            key="domain_file_input"
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

        user_input = st.chat_input("Ask a question, request code/circuits, or explore any topic...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Council synthesizing response..."):
                    council_system = (
                        f"You are the deployed expert multi-domain AI tool created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "OPERATING DIRECTIVES:\n"
                        "1. Be creative, engaging, and articulate. Provide working code, step-by-step pinouts, and clear explanations.\n"
                        "2. Maintain a warm, encouraging tone.\n"
                        "3. When an image is attached, describe all elements, chips, labels, numbers, or text accurately.\n"
                        "4. Never output internal planning notes or 'We need to' meta-thinking.\n"
                        "5. If generating graphs, provide clean Python code using `matplotlib.pyplot as plt` and define `fig`.\n"
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
                        reply = call_groq(messages, model=VISION_MODEL, max_tok=1000, temp=0.5)
                    else:
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            messages.append({"role": m["role"], "content": m["content"]})
                        reply = call_groq(messages, model=TEXT_MODEL, max_tok=1000, temp=0.5)

                    if reply:
                        st.markdown(reply)

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
        st.caption("Complete code compiled across all active specialist brains:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
