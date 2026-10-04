import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory for Students", page_icon="⚙️", layout="wide")

st.title("⚙️ AI App Factory")
st.caption("Enter a description to build and test a custom student tool.")

# Sidebar for configuration
with st.sidebar:
    st.header("Factory Settings")
    api_key = st.text_input("Groq API Key (Free)", type="password", help="Get a free key from console.groq.com")
    st.markdown("[Get a free Groq API key here](https://console.groq.com/keys)")
    st.markdown("---")
    st.markdown("**Pipeline Brains:**")
    st.markdown("1. 🧠 **Architect:** DeepSeek-R1-Distill")
    st.markdown("2. ⚡ **Builder:** Qwen 2.5 Coder 32B")

prompt = st.text_area("What tool do you want to build?", placeholder="e.g., A C code generator with syntax explanations and copyable snippets.")

def query_groq(prompt_text, system_instruction, model, key):
    headers = {"Authorization": f"Bearer {key}", "Content-Type": "application/json"}
    payload = {
        "model": model,
        "messages": [
            {"role": "system", "content": system_instruction},
            {"role": "user", "content": prompt_text}
        ],
        "temperature": 0.6
    }
    res = requests.post("https://api.groq.com/openai/v1/chat/completions", headers=headers, json=payload)
    if res.status_code == 200:
        return res.json()["choices"][0]["message"]["content"]
    else:
        st.error(f"Error {res.status_code}: {res.text}")
        return None

if st.button("🚀 Run AI Factory", type="primary"):
    if not api_key:
        st.warning("Please provide a Groq API Key in the left sidebar to power the factory.")
    elif not prompt.strip():
        st.warning("Please describe what student app you want to create.")
    else:
        status = st.status("🏭 Factory running: Starting Brain Pipeline...", expanded=True)
        
        # Brain 1: Architect
        status.write("🧠 **Brain 1 (Architect - DeepSeek):** Designing system architecture and UI blueprint...")
        arch_prompt = f"Design a simple, single-page Streamlit educational web app for this goal: '{prompt}'. Provide clean component specifications and logic."
        arch_spec = query_groq(arch_prompt, "You are a software architect.", "deepseek-r1-distill-llama-70b", api_key)
        
        if arch_spec:
            # Brain 2: Builder
            status.write("⚡ **Brain 2 (Builder - Qwen Coder):** Writing clean Streamlit code...")
            build_prompt = f"Based on this specification:\n{arch_spec}\n\nWrite valid, standalone Streamlit Python code. Return ONLY pure python code inside a single ```python ``` code block. Do not add markdown text outside the code block."
            raw_code = query_groq(build_prompt, "You are an expert Streamlit and Python developer.", "qwen-2.5-coder-32b", api_key)
            
            if raw_code:
                # Clean markdown blocks
                code_match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
                clean_code = code_match.group(1).strip() if code_match else raw_code.strip()
                
                status.update(label="✅ App Generated Successfully!", state="complete", expanded=False)
                
                tab1, tab2 = st.tabs(["💻 Generated Code", "▶️ Run Preview"])
                
                with tab1:
                    st.code(clean_code, language="python")
                    st.download_button("📥 Download App (.py)", data=clean_code, file_name="generated_app.py", mime="text/plain")
                
                with tab2:
                    st.info("Running live app code below:")
                    try:
                        exec_scope = {}
                        exec(clean_code, exec_scope)
                    except Exception as e:
                        st.error(f"Error running generated app: {e}")
