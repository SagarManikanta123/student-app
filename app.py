import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory", layout="wide")

st.title("AI App Factory")
st.caption("Enter a description to build and test a custom student tool.")

def sanitize_text(text):
    if not text:
        return ""
    return "".join(c for c in text.strip() if 32 <= ord(c) <= 126)

with st.sidebar:
    st.header("Factory Settings")
    raw_key = st.text_input("Groq API Key", type="password")
    api_key = sanitize_text(raw_key)
    st.markdown("[Get a free Groq API key here](https://console.groq.com/keys)")
    st.markdown("---")
    
    default_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    models = default_models
    
    if api_key:
        try:
            m_res = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={
                    "Authorization": f"Bearer {api_key}",
                    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
                },
                timeout=5
            )
            if m_res.status_code == 200:
                fetched = [
                    m["id"] for m in m_res.json().get("data", [])
                    if not any(bad in m["id"].lower() for bad in ["whisper", "guard", "orpheus", "tts", "audio", "canopy"])
                ]
                if fetched:
                    models = fetched
        except Exception:
            pass

    st.markdown("**Pipeline Brains:**")
    arch_model = st.selectbox("Architect Brain", models, index=0)
    build_model = st.selectbox("Builder Brain", models, index=min(1, len(models) - 1))

prompt = st.text_area("What tool do you want to build?", placeholder="e.g. A C programming cheat sheet and syntax builder with copyable snippets")

def call_llm(prompt_text, system_instruction, model, key):
    clean_k = sanitize_text(key)
    headers = {
        "Authorization": f"Bearer {clean_k}",
        "Content-Type": "application/json",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"
    }
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.5
    }
    try:
        res = requests.post(
            "https://api.groq.com/openai/v1/chat/completions",
            headers=headers,
            json=payload,
            timeout=60
        )
        if res.status_code == 200:
            return res.json()["choices"][0]["message"]["content"]
        else:
            st.error(f"Error {res.status_code}: {res.text}")
            return None
    except Exception as exc:
        st.error(f"Request failed: {exc}")
        return None

if st.button("Run AI Factory", type="primary"):
    if not api_key:
        st.warning("Please enter your Groq API Key in the sidebar.")
    elif not prompt.strip():
        st.warning("Please type a description of the student tool you want to build.")
    else:
        status = st.status("Factory running: Starting Brain Pipeline...", expanded=True)
        
        status.write(f"Brain 1 (Architect - {arch_model}): Designing UI blueprint...")
        arch_prompt = f"Design a simple, single-page Streamlit educational web app for this goal: '{prompt}'. Provide clean component specifications and logic."
        arch_spec = call_llm(arch_prompt, "You are a software architect.", arch_model, api_key)
        
        if arch_spec:
            status.write(f"Brain 2 (Builder - {build_model}): Writing clean Streamlit code...")
            build_prompt = f"Based on this specification:\n{arch_spec}\n\nWrite valid, standalone Streamlit Python code. Return ONLY pure python code inside a single ```python ``` code block. Do not add markdown explanation outside the code block."
            raw_code = call_llm(build_prompt, "You are an expert Streamlit and Python developer.", build_model, api_key)
            
            if raw_code:
                code_match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
                clean_code = code_match.group(1).strip() if code_match else raw_code.strip()
                
                status.update(label="App Generated Successfully!", state="complete", expanded=False)
                
                tab1, tab2 = st.tabs(["Generated Code", "Run Preview"])
                
                with tab1:
                    st.code(clean_code, language="python")
                    st.download_button("Download App (.py)", data=clean_code, file_name="generated_app.py", mime="text/plain")
                
                with tab2:
                    st.info("Running live app preview below:")
                    try:
                        exec_scope = {}
                        exec(clean_code, exec_scope)
                    except Exception as e:
                        st.error(f"Error running preview: {e}")
