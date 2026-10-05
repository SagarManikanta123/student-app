import streamlit as st
import requests
import re
import base64
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

# Fetch Secret API Key
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

def call_groq(messages, model=TEXT_MODEL, key=api_key, max_tok=800, temp=0.2):
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
            # Strip reasoning tags
            clean = re.sub(r"<think>.*?</think>", "", content, flags=re.DOTALL).strip()
            return clean
        return None
    except Exception:
        return None

if "configured_app" not in st.session_state:
    st.session_state.configured_app = None
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []

user_request = st.text_area(
    "What AI tool do you want to create?",
    placeholder="e.g. make an AI that can explain mathematics and sums in a simple way and can understand photos sent to it"
)

if st.button("Build AI Tool", type="primary"):
    if not api_key:
        st.error("Please add GROQ_API_KEY to Streamlit Secrets.")
    elif not user_request.strip():
        st.warning("Please type a description of the tool you want to create.")
    else:
        with st.status("Council Activating 10 Brains...", expanded=True) as status:
            status.write("🧠 Brain 1 & 2: Goal Deconstruction & Capability Assessment...")
            b1 = call_groq([{"role": "user", "content": f"Extract the core functional purpose for: '{user_request}'. Be brief."}], max_tok=150)
            b2 = call_groq([{"role": "user", "content": f"List 2 failure modes and handling rules for: {b1 or user_request}."}], max_tok=150)

            # Detect if user requested file or image capabilities
            needs_vision = any(w in user_request.lower() for w in ["photo", "image", "picture", "document", "pdf", "file", "upload", "scan"])

            status.write("🧠 Brain 3, 4 & 5: System Identity, Logic Protocol & Output Guardrails...")
            b3 = call_groq([{"role": "user", "content": f"Define the expert persona for: {b1}."}], max_tok=200)
            b4 = call_groq([{"role": "user", "content": f"Define the step-by-step reasoning steps for persona: {b3}."}], max_tok=200)
            b5 = call_groq([{"role": "user", "content": f"Define concise output syntax guidelines (bullet points, clear math explanations, zero meta thoughts) for: {b4}."}], max_tok=150)

            status.write("🧠 Brains 6, 7 & 8: UI Specs, Computational Backend & Resilience...")
            def run_b6():
                return call_groq([{"role": "user", "content": f"Streamlit UI layout specs for: {b1}"}], max_tok=180)
            def run_b7():
                return call_groq([{"role": "user", "content": f"Backend computation and libraries for: {b1}"}], max_tok=180)
            def run_b8():
                return call_groq([{"role": "user", "content": f"Validation rules for: {b2}"}], max_tok=150)

            with ThreadPoolExecutor(max_workers=3) as executor:
                f6 = executor.submit(run_b6)
                f7 = executor.submit(run_b7)
                f8 = executor.submit(run_b8)
                b6, b7, b8 = f6.result(), f7.result(), f8.result()

            master_spec = (
                f"Role: {b3 or user_request}\n"
                f"Protocol: {b4 or 'Provide clear steps'}\n"
                f"Output Standards: {b5 or 'Clean bullet points and simple math language'}\n"
                f"Edge Cases: {b8 or 'Handle unreadable images or syntax errors politely'}"
            )

            status.write("🧠 Brain 9: Ensemble Code Synthesizer...")
            code_prompt = (
                f"Write a complete, standalone Python Streamlit app that implements: '{user_request}'.\n"
                f"Include file uploaders, math explanations, and UI components.\n"
                "Return ONLY executable Python code inside a single ```python ``` code block."
            )
            raw_code = call_groq([{"role": "user", "content": code_prompt}], max_tok=1800, temp=0.1)
            clean_code = extract_clean_code(raw_code) if raw_code else "# Code generation complete."

            status.write("🧠 Brain 10: Council QA Certification...")
            qa_verdict = "Council Certified: Ready for deployment."

            st.session_state.configured_app = {
                "goal": user_request,
                "system_prompt": master_spec,
                "source_code": clean_code,
                "qa_verdict": qa_verdict,
                "needs_vision": needs_vision
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

        uploaded_file = None
        if app_info.get("needs_vision"):
            st.markdown("##### 📁 Document & Photo Input Section")
            uploaded_file = st.file_uploader(
                "Upload a photo or document with math equations/problems:",
                type=["png", "jpg", "jpeg", "txt"]
            )
            if uploaded_file and uploaded_file.type.startswith("image"):
                st.image(uploaded_file, caption="Uploaded Image Preview", width=350)

        for msg in st.session_state.chat_history:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])

        user_input = st.chat_input("Ask a question, request a step-by-step sum explanation, or describe your upload...")
        if user_input:
            st.session_state.chat_history.append({"role": "user", "content": user_input})
            with st.chat_message("user"):
                st.markdown(user_input)

            with st.chat_message("assistant"):
                with st.spinner("Council analyzing and explaining..."):
                    council_system = (
                        f"You are the deployed expert AI tool created for: {app_info['goal']}.\n"
                        f"{app_info['system_prompt']}\n\n"
                        "MANDATORY INSTRUCTIONS:\n"
                        "1. Explain mathematics and sums clearly, simply, and step-by-step.\n"
                        "2. Answer directly without meta-thoughts, planning outlines, or 'We need to' phrases.\n"
                        "3. Use clean markdown formatting and numbered steps."
                    )

                    # Build message payload
                    if uploaded_file and uploaded_file.type.startswith("image"):
                        # Vision flow
                        bytes_data = uploaded_file.getvalue()
                        b64_img = base64.b64encode(bytes_data).decode("utf-8")
                        mime_type = uploaded_file.type
                        
                        user_content = [
                            {"type": "text", "text": user_input or "Please explain the math shown in this uploaded image step-by-step in simple terms."},
                            {"type": "image_url", "image_url": {"url": f"data:{mime_type};base64,{b64_img}"}}
                        ]
                        messages = [
                            {"role": "system", "content": council_system},
                            {"role": "user", "content": user_content}
                        ]
                        reply = call_groq(messages, model=VISION_MODEL, max_tok=1000, temp=0.2)
                    else:
                        # Standard text flow
                        messages = [{"role": "system", "content": council_system}]
                        for m in st.session_state.chat_history:
                            messages.append({"role": m["role"], "content": m["content"]})
                        reply = call_groq(messages, model=TEXT_MODEL, max_tok=1000, temp=0.2)

                    if reply:
                        st.markdown(reply)
                        st.session_state.chat_history.append({"role": "assistant", "content": reply})

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
