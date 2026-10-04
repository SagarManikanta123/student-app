UnicodeEncodeError: ... 'latin-1' codec can't encode characters in position ...
File "/usr/local/lib/python3.14/http/client.py", line 1359, in putheader
```[cite: 16, 17]

### Why did this error happen?
When pasting your Groq API key or the prompt into the browser, a **hidden non-ASCII character, smart-quote, or copy-paste whitespace character** got into the HTTP `Authorization` header (`Bearer <key>`). HTTP header values in Python must strictly be plain ASCII / Latin-1 bytes; any hidden Unicode character causes `http.client.putheader` to crash with `UnicodeEncodeError`[cite: 17].

Also, we can fetch all **active, working models directly from your Groq account** automatically via `GET [https://api.groq.com/openai/v1/models](https://api.groq.com/openai/v1/models)`, so you never have to guess or hardcode a model name again.

---

### Step 1: Open `app.py` on GitHub
1. Switch to your **`student-app/app.py at main`** GitHub tab[cite: 10, 11].
2. Click the **pencil icon** (Edit this file)[cite: 10].
3. Select everything (**Ctrl + A**) and hit **Delete**.

---

### Step 2: Paste this Code (Sanitizes Headers + Auto-Fetches Available Models)

```python
import streamlit as st
import requests
import json
import re

st.set_page_config(page_title="AI App Factory for Students", page_icon="⚙️", layout="wide")

st.title("⚙️️ AI App Factory")
st.caption("Enter a description to build and test a custom student tool.")

def clean_ascii(val):
    if not val:
        return ""
    # Strip spaces, newlines, and non-ASCII invisible characters from headers/keys
    return "".join(c for c in val.strip() if 32 <= ord(c) <= 126)

# Sidebar for configuration
with st.sidebar:
    st.header("Factory Settings")
    raw_key = st.text_input("Groq API Key (Free)", type="password", help="Get a free key from console.groq.com")
    api_key = clean_ascii(raw_key)
    st.markdown("[Get a free Groq API key here](https://console.groq.com/keys)")
    st.markdown("---")
    
    # Auto-load available models from the Groq account
    available_models = ["openai/gpt-oss-120b", "openai/gpt-oss-20b", "qwen/qwen3.8-27b"]
    if api_key:
        try:
            m_res = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5
            )
            if m_res.status_code == 200:
                fetched = [m["id"] for m in m_res.json().get("data", []) if "whisper" not in m["id"] and "guard" not in m["id"]]
                if fetched:
                    available_models = fetched
        except Exception:
            pass

    st.markdown("**Pipeline Brains:**")
    arch_model = st.selectbox("Architect Brain", available_models, index=0)
    build_model = st.selectbox("Builder Brain", available_models, index=min(1, len(available_models) - 1))

prompt = st.text_area("What tool do you want to build?", placeholder="e.g., Make an AI tool for C programming practice and debugging.")

def query_groq(prompt_text, system_instruction, model, key):
    headers = {
        "Authorization": f"Bearer {clean_ascii(key)}",
        "Content-Type": "application/json; charset=utf-8"
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

if st.button("🚀 Run AI Factory", type="primary"):
    if not api_key:
        st.warning("Please enter your Groq API Key in the sidebar.")
    elif not prompt.strip():
        st.warning("Please type a description of the student tool you want to build.")
    else:
        status = st.status("🏭 Factory running: Starting Brain Pipeline...", expanded=True)
        
        # Brain 1: Architect
        status.write(f"🧠 **Brain 1 (Architect - {arch_model}):** Designing app structure and UI blueprint...")
        arch_prompt = f"Design a simple, single-page Streamlit educational web app for this goal: '{prompt}'. Provide clean component specifications and logic."
        arch_spec = query_groq(arch_prompt, "You are a software architect.", arch_model, api_key)
        
        if arch_spec:
            # Brain 2: Builder
            status.write(f"⚡ **Brain 2 (Builder - {build_model}):** Writing clean Streamlit code...")
            build_prompt = f"Based on this specification:\n{arch_spec}\n\nWrite valid, standalone Streamlit Python code. Return ONLY pure python code inside a single ```python ``` code block. Do not add markdown explanation outside the code block."
            raw_code = query_groq(build_prompt, "You are an expert Streamlit and Python developer.", build_model, api_key)
            
            if raw_code:
                code_match = re.search(r"```python(.*?)```", raw_code, re.DOTALL)
                clean_code = code_match.group(1).strip() if code_match else raw_code.strip()
                
                status.update(label="✅ App Generated Successfully!", state="complete", expanded=False)
                
                tab1, tab2 = st.tabs(["💻 Generated Code", "▶️ Run Preview"])
                
                with tab1:
                    st.code(clean_code, language="python")
                    st.download_button("📥 Download App (.py)", data=clean_code, file_name="generated_app.py", mime="text/plain")
                
                with tab2:
                    st.info("Running live app preview below:")
                    try:
                        exec_scope = {}
                        exec(clean_code, exec_scope)
                    except Exception as e:
                        st.error(f"Error running preview: {e}")
