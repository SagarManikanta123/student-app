import streamlit as st
import requests
import re
import base64
import numpy as np
import matplotlib.pyplot as plt

st.set_page_config(page_title="Llama-3.3 70B Council Factory", layout="wide")

st.title("Universal AI Factory (14-Brain Mega-Council)")
st.caption("Powered by Meta Llama 3.3 70B Versatile & Llama 3.2 Vision")

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

# The most powerful text and vision models available on Groq
FLAGSHIP_MODEL = "llama-3.3-70b-versatile"
VISION_MODEL = "llama-3.2-11b-vision-preview"

def call_groq(messages, model=FLAGSHIP_MODEL, key=api_key, max_tok=1400, temp=0.5):
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
            timeout=45
        )
        if res.status_code == 200:
            msg = res.json()["choices"][0]["message"]
            content = msg.get("content") or msg.get("reasoning") or ""
            return strip_internal_thoughts(content)
        else:
            return f"API Error ({res.status_code}): {res.text}"
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
    placeholder="e.g. Build an AI that can inspect circuits/photos, solve complex math and physics, generate code, draw graphs, and explain everything with creative analogies."
)

if st.button("Deploy Mega-Council AI", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please describe what tool you want to create.")
    else:
        with st.status(f"Concurring 14-Brain Council via {FLAGSHIP_MODEL}...", expanded=True) as status:
            status.write("🧠 Phase 1: Synthesizing perspectives across all 14 specialist departments...")
            
            council_synthesis_prompt = (
                f"You are the supreme Council Moderator. A user wants to build an AI system designed to: '{user_request}'.\n\n"
                "Convene the 14 specialist brains:\n"
                "1. Vision & Media Inspector\n"
                "2. Creative Analogy Architect\n"
                "3. Polite Tone & Pedagogy Brain\n"
                "4. Mathematics Engine\n"
                "5. Physics & Mechanics Specialist\n"
                "6. Electrical & Microcontroller Engineering Specialist\n"
                "7. Computer Science & Coding Engine\n"
                "8. Chemistry & Material Science Specialist\n"
                "9. Life Sciences & Biology Specialist\n"
                "10. Humanities & History Brain\n"
                "11. Language & Prose Specialist\n"
                "12. Dynamic Visualization & Plotting Engine\n"
                "13. Resilience & Input Validation Brain\n"
                "14. Universal Cross-Disciplinary Tutor\n\n"
                "Synthesize their combined operational directive into a comprehensive, robust system prompt for this assistant. "
                "Ensure it demands high creativity, vivid real-world analogies, full code implementations, and zero meta-reasoning leaks. "
                "Output the final system prompt directly."
            )
            
            master_system_prompt = call_groq(
                [{"role": "user", "content": council_synthesis_prompt}],
                model=FLAGSHIP_MODEL,
                max_tok=1000,
                temp=0.4
            )

            status.write("🧠 Phase 2: Generating standalone production code package...")
            code_prompt = (
                f"Write a complete, bug-free standalone Python Streamlit app that implements this multi-brain system:\n{master_system_prompt}\n\n"
                "CRITICAL REQUIREMENTS:\n"
                "- Write fully functional, complete Python code.\n"
                "- Output ONLY valid Python code inside a single ```python ``` code block."
            )
            raw_code = call_groq(
                [{"role": "user", "content": code_prompt}],
                model=FLAGSHIP_MODEL,
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
            status.update(label="14-Brain Mega-Council Deployed Successfully!", state="complete", expanded=False)
            st.rerun()

# Workspace UI
if st.session_state.configured_app:
    app_info = st.session_state.configured_app
    st.markdown("---")

    tab1, tab2 = st.tabs(["⚡ Live 14-Brain Council Workspace", "📄 Standalone Code (.py)"])

    with tab1:
        st.subheader("Autonomous Mega-Council Active")
        st.caption(f"Engine: {FLAGSHIP_MODEL} | Objective: {app_info['goal']}")

        st.markdown("#### 📷 Image & Media Input")
        uploaded_file = st.file_uploader(
            "Upload an image, diagram, circuit photo, or document:",
            type=["png", "jpg", "jpeg"],
            key="mega_file_input"
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

        user_input = st.chat_input("Ask a question, request code, explain diagrams/circuits, or explore any subject...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("14-Brain Council analyzing with Llama 3.3 70B..."):
                    council_system = (
                        f"You are the deployed expert multi-domain AI tool created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "OPERATIONAL RULES:\n"
                        "1. Answer with creative depth, high intuition, and practical real-world analogies.\n"
                        "2. Maintain an articulate, polite, and encouraging tone.\n"
                        "3. Provide complete, fully detailed code solutions and pinout breakdowns where requested.\n"
                        "4. When an image is attached, inspect all labels, components, equations, or features thoroughly.\n"
                        "5. If generating graphs, provide clean Python code using `matplotlib.pyplot as plt` and define `fig`.\n"
                        "6. Never output meta-thoughts or 'We need to' notes.\n"
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
                        reply = call_groq(messages, model=VISION_MODEL, max_tok=1200, temp=0.5)
                    else:
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            messages.append({"role": m["role"], "content": m["content"]})
                        reply = call_groq(messages, model=FLAGSHIP_MODEL, max_tok=1400, temp=0.5)

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
        st.caption("Complete code compiled across the 14-brain council architecture:")
        st.code(app_info["source_code"], language="python")
        st.download_button(
            "Download Source Code (.py)",
            data=app_info["source_code"],
            file_name="custom_ai_app.py",
            mime="text/plain"
        )
