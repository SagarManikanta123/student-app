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

def extract_clean_code(text):
    if not text:
        return ""
    # Check for markdown code blocks
    match = re.search(r"```(?:python)?\s*(.*?)\s*```", text, re.DOTALL | re.IGNORECASE)
    if match:
        code = match.group(1).strip()
    else:
        # If no markdown fences, remove any conversational lines before the first import/def
        lines = text.strip().splitlines()
        code_lines = []
        started = False
        for line in lines:
            if re.match(r"^\s*(import|from|st\.|def|class|#)", line):
                started = True
            if started:
                code_lines.append(line)
        code = "\n".join(code_lines) if code_lines else text.strip()
    
    # Strip any stray backticks that could break exec
    return re.sub(r"^```.*$", "", code, flags=re.MULTILINE).strip()

with st.sidebar:
    st.header("Factory Settings")
    raw_key = st.text_input("Groq API Key", type="password")
    api_key = sanitize_text(raw_key)
    st.markdown("[Get a free Groq API key here](https://console.groq.com/keys)")
    st.markdown("---")
    
    supported_models = [
        "openai/gpt-oss-20b",
        "openai/gpt-oss-120b"
    ]

    st.markdown("**Pipeline Brains:**")
    arch_model = st.selectbox("Architect Brain", supported_models, index=0)
    build_model = st.selectbox("Builder Brain", supported_models, index=0)

prompt = st.text_area("What tool do you want to build?", placeholder="e.g. make an AI that draws graphs when user gives input equations")

def call_llm(prompt_text, system_instruction, model, key, max_tok=3500):
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
        "temperature": 0.2,
        "max_tokens": max_tok
    }
    try:
        res = requests.post(
            "[https://api.groq.com/openai/v1/chat/completions](https://api.groq.com/openai/v1/chat/completions)",
            headers=headers,
            json=payload,
            timeout=90
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
        
        # Brain 1: Architecture Blueprint
        status.write(f"Brain 1 (Architect - {arch_model}): Designing UI blueprint...")
        arch_prompt = f"Design a concise Streamlit app specification for: '{prompt}'. Focus on clear inputs, evaluating math functions, and rendering with matplotlib."
        arch_spec = call_llm(arch_prompt, "You are a concise software architect.", arch_model, api_key, max_tok=500)
        
        if arch_spec:
            # Brain 2: Streamlit Code Builder
            status.write(f"Brain 2 (Builder - {build_model}): Writing clean Streamlit code...")
            build_prompt = (
                f"Build a complete, standalone, bug-free Streamlit Python app based on this specification:\n{arch_spec}\n\n"
                "CRITICAL INSTRUCTIONS:\n"
                "1. Output ONLY executable Python code starting directly with imports.\n"
                "2. Do NOT write any introduction or explanation text before or after the code.\n"
                "3. Use 'matplotlib.pyplot' and 'st.pyplot(fig)' for plotting.\n"
                "4. Enclose all code within a single ```python ``` block."
            )
            raw_code = call_llm(build_prompt, "You are a pure Python code generator. Do not provide conversational filler.", build_model, api_key, max_tok=3500)
            
            if raw_code:
                clean_code = extract_clean_code(raw_code)
                
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
