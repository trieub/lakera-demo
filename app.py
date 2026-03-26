import streamlit as st
import asyncio, os
import httpx

# ══════════════════════════════════════════════════════════════════════════════
#  BACKEND: CORE LOGIC
# ══════════════════════════════════════════════════════════════════════════════

async def get_best_model(key: str):
    if not key: return "gemini-1.5-flash-latest"
    url = f"https://generativelanguage.googleapis.com/v1/models?key={key}"
    try:
        async with httpx.AsyncClient(timeout=10) as client:
            r = await client.get(url)
            r.raise_for_status()
            models = [m["name"].split("/")[-1] for m in r.json().get("models", [])
                      if "gemini" in m["name"].lower() and "generateContent" in m.get("supportedGenerationMethods", [])]
            flash = [m for m in models if "flash" in m]
            return sorted(flash, reverse=True)[0] if flash else sorted(models, reverse=True)[0]
    except:
        return "gemini-1.5-flash-latest"

async def lakera_scan(raw: str, key: str, pid: str):
    url = "https://api.lakera.ai/v2/guard"
    safe_prompt = str(raw).strip()
    payload = {
        "messages": [{"role": "user", "content": safe_prompt}],
        "project_id": str(pid).strip()
    }
    headers = {
        "Authorization": f"Bearer {key}",
        "Content-Type": "application/json",
        "X-Lakera-Source": "AI-Defense-Plane"
    }
    try:
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(url, headers=headers, json=payload)
            r.raise_for_status()
            res = r.json()
            return {"flagged": bool(res.get("flagged", False)), "pid": str(pid).strip()}
    except Exception as e:
        return {"flagged": True, "error": str(e), "pid": str(pid).strip()}

async def gemini_call(raw: str, key: str, model: str):
    url = f"https://generativelanguage.googleapis.com/v1/models/{model}:generateContent?key={key}"
    try:
        async with httpx.AsyncClient(timeout=30) as client:
            r = await client.post(url, json={"contents": [{"parts": [{"text": raw}]}]})
            r.raise_for_status()
            return r.json()["candidates"][0]["content"]["parts"][0]["text"]
    except Exception as e:
        return f"LLM Error: {str(e)}"

# ══════════════════════════════════════════════════════════════════════════════
#  UI
# ══════════════════════════════════════════════════════════════════════════════

st.set_page_config(page_title="AI Defense Plane — CheckPoint", layout="wide", initial_sidebar_state="collapsed")

for k, v in {
    "k_lk": os.getenv("LAKERA_API_KEY", ""),
    "k_gm": os.getenv("GEMINI_API_KEY", ""),
    "k_pid": os.getenv("PROJECT_ID", ""),
    "auto_model": None,
    "history": None
}.items():
    if k not in st.session_state:
        st.session_state[k] = v

is_active = st.session_state.auto_model is not None
badge_main_color = "#0E8A4A" if is_active else "#D6004F"
badge_bg_color = "#F0FBF5" if is_active else "#FFF0F3"
badge_border_color = "#B9EAD0" if is_active else "#FFCCD5"
badge_dot = "🟢" if is_active else "🔴"

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:wght@300;400;500;600;700&family=DM+Mono:wght@400;500&display=swap');

html, body, [class*="css"] {{
    font-family: 'DM Sans', sans-serif;
    background-color: #F7F8FA;
}}

.block-container {{ padding: 0 2rem 3rem 2rem !important; max-width: 1280px; }}

.topbar {{
    background: #FFFFFF;
    border-bottom: 3px solid #D6004F;
    padding: 1rem 2rem;
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin: 0 -2rem 2.5rem -2rem;
    box-shadow: 0 2px 12px rgba(0,0,0,0.06);
}}
.topbar-left {{ display: flex; align-items: center; gap: 14px; }}

.topbar-logo {{
    width: 140px; 
    height: auto;
    display: flex; 
    align-items: center; 
    justify-content: center;
}}
.topbar-logo img {{
    width: 100%;
    height: auto;
    object-fit: contain;
}}

.topbar-title {{
    font-size: 18px; font-weight: 800; color: #000000; letter-spacing: -0.3px;
}}
.topbar-sub {{
    font-size: 12px; font-weight: 600; color: #4A4F63; margin-top: 1px; letter-spacing: 0.5px; text-transform: uppercase;
}}

.topbar-badge {{
    background: {badge_bg_color}; 
    color: {badge_main_color}; 
    border: 1.5px solid {badge_border_color};
    font-size: 11px; font-weight: 800; padding: 4px 12px; border-radius: 20px;
    letter-spacing: 0.5px;
    display: flex; align-items: center; gap: 6px;
    animation: pulseBadge 2.5s infinite;
}}

.badge-dot {{
    font-size: 13px;
    animation: pulseDot 1.5s infinite;
}}

@keyframes pulseDot {{
    0% {{ opacity: 1; transform: scale(1); }}
    50% {{ opacity: 0.4; transform: scale(0.9); }}
    100% {{ opacity: 1; transform: scale(1); }}
}}

@keyframes pulseBadge {{
    0% {{ box-shadow: 0 0 0 0 rgba({(214 if not is_active else 14)}, {(0 if not is_active else 138)}, {(79 if not is_active else 74)}, 0.4); }}
    70% {{ box-shadow: 0 0 0 8px rgba({(214 if not is_active else 14)}, {(0 if not is_active else 138)}, {(79 if not is_active else 74)}, 0); }}
    100% {{ box-shadow: 0 0 0 0 rgba({(214 if not is_active else 14)}, {(0 if not is_active else 138)}, {(79 if not is_active else 74)}, 0); }}
}}

.section-label {{
    font-size: 12px; font-weight: 800; letter-spacing: 1.2px;
    text-transform: uppercase; color: #2D334A;
    margin-bottom: 12px; display: flex; align-items: center; gap: 8px;
}}
.section-label::before {{
    content: ''; display: inline-block; width: 4px; height: 16px;
    background: #D6004F; border-radius: 2px;
}}

.card {{
    background: #FFFFFF;
    border: 1px solid #D1D5E0;
    border-radius: 14px;
    padding: 1.5rem;
    margin-bottom: 1.2rem;
    box-shadow: 0 2px 8px rgba(0,0,0,0.05);
}}
.card-title {{
    font-size: 12px; font-weight: 800; letter-spacing: 1px;
    text-transform: uppercase; color: #4A4F63; margin-bottom: 1rem;
    padding-bottom: 0.75rem; border-bottom: 2px solid #F0F1F5;
}}

.metric-row {{ display: flex; gap: 14px; margin-bottom: 1.2rem; }}
.metric-box {{
    flex: 1; background: #FFFFFF; border: 1.5px solid #E2E8F0;
    border-radius: 12px; padding: 1rem 1.25rem;
}}
.metric-label {{ font-size: 11px; font-weight: 700; color: #5A607F; letter-spacing: 0.8px; text-transform: uppercase; }}
.metric-value {{ font-size: 20px; font-weight: 800; color: #0D1117; margin-top: 4px; }}
.metric-value.danger {{ color: #D6004F; }}
.metric-value.success {{ color: #0E8A4A; }}

.badge-blocked {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #FFF0F3; color: #C62828; border: 2px solid #FFCDD2;
    font-size: 12px; font-weight: 800; padding: 6px 14px; border-radius: 8px;
}}
.badge-clean {{
    display: inline-flex; align-items: center; gap: 6px;
    background: #F0FBF5; color: #0E8A4A; border: 2px solid #B9EAD0;
    font-size: 12px; font-weight: 800; padding: 6px 14px; border-radius: 8px;
}}

.captured-block {{
    background: #F1F3F9; border: 1px solid #D1D5E0;
    border-left: 4px solid #D6004F;
    border-radius: 8px; padding: 1rem;
    font-family: 'DM Mono', monospace; font-size: 13px;
    color: #1A1C23; line-height: 1.6; word-break: break-word;
    margin-top: 10px; margin-bottom: 12px;
}}

.response-block {{
    background: #F8FAFC; border: 1.5px solid #E2E8F0; border-radius: 10px;
    padding: 1rem 1.2rem; font-size: 14px; color: #1A1C23;
    line-height: 1.7; min-height: 80px;
}}
.response-block.blocked {{
    background: #FFF5F7; border-color: #FFCDD2; color: #8A1C2B;
}}

.stTextArea textarea {{
    border: 2px solid #CBD5E1 !important; border-radius: 10px !important;
    font-family: 'DM Sans', sans-serif !important; font-size: 14px !important;
    color: #000000 !important; background: #FFFFFF !important;
}}
.stTextArea textarea:focus {{ border-color: #D6004F !important; }}

.stButton > button[kind="primary"] {{
    background: #D6004F !important; color: white !important;
    border: none !important; border-radius: 10px !important;
    font-weight: 800 !important;
}}

.footer {{
    text-align: center; padding: 2.5rem 0 1.5rem;
    font-size: 12px; font-weight: 700; color: #4A4F63;
    letter-spacing: 1px; text-transform: uppercase; border-top: 2px solid #EEF0F5;
}}

#MainMenu, footer, header {{ visibility: hidden; }}
</style>

<div class="topbar">
    <div class="topbar-left">
        <div class="topbar-logo">
            <img src="https://upload.wikimedia.org/wikipedia/commons/thumb/f/f3/Check_Point_logo_2022.svg/1280px-Check_Point_logo_2022.svg.png">
        </div>
        <div>
            <div class="topbar-title"><span style="color:#D6004F">Secure Your AI Transformation</span></div>
            <div class="topbar-sub">AI Defense Plane</div>
        </div>
    </div>
    <div class="topbar-badge"><span class="badge-dot">{badge_dot}</span> Live Protection</div>
</div>
""", unsafe_allow_html=True)

# ── SETTINGS ──────────────────────────────────────────────────────────────────
with st.expander("⚙️  Configuration", expanded=not st.session_state.auto_model):
    st.markdown('<div style="font-size:14px;font-weight:600;color:#2D334A;margin-bottom:1rem;">Connect your API credentials to enable Lakera threat detection and Gemini inference.</div>', unsafe_allow_html=True)
    c1, c2, c3 = st.columns([1, 1, 1])
    with c1:
        lk = st.text_input("Lakera API Key", value=st.session_state.k_lk, type="password", placeholder="lk-…")
    with c2:
        gm = st.text_input("Gemini API Key", value=st.session_state.k_gm, type="password", placeholder="AIza…")
    with c3:
        pid = st.text_input("Project ID", value=st.session_state.k_pid, placeholder="project-uuid")

    sc1, sc2 = st.columns([1, 3])
    with sc1:
        if st.button("⚡  Apply & Sync", use_container_width=True):
            loop = asyncio.new_event_loop()
            st.session_state.auto_model = loop.run_until_complete(get_best_model(gm))
            st.session_state.k_lk, st.session_state.k_gm, st.session_state.k_pid = lk, gm, pid
            st.rerun()
    with sc2:
        if st.session_state.auto_model:
            st.markdown(f'<div style="padding-top:8px"><span class="model-pill" style="color:#1E3A8A; background:#DBEAFE; border:1px solid #3B82F6; padding: 4px 12px; border-radius: 6px; font-weight:700;">✦ Active model: {st.session_state.auto_model}</span></div>', unsafe_allow_html=True)

st.markdown("<hr style='border-top: 2px solid #E2E8F0;'>", unsafe_allow_html=True)

# ── MAIN COLUMNS ──────────────────────────────────────────────────────────────
col_l, col_r = st.columns([1, 1], gap="large")

with col_l:
    st.markdown('<div class="section-label">Input Interface</div>', unsafe_allow_html=True)
    u_prompt = st.text_area("prompt_input", height=320, label_visibility="collapsed", placeholder="Enter a prompt to scan and analyze...")
    
    if st.session_state.auto_model:
        exec_btn = st.button("▶  Run Analysis", use_container_width=True, type="primary")
    else:
        st.button("▶  Run Analysis", use_container_width=True, type="primary", disabled=True)
        exec_btn = False

    if exec_btn and u_prompt and st.session_state.auto_model:
        with st.spinner("Scanning..."):
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            l_res = loop.run_until_complete(lakera_scan(u_prompt, st.session_state.k_lk, st.session_state.k_pid))
        if l_res["flagged"]:
            g_res = "Request blocked — policy violation detected by Lakera Guard."
        else:
            with st.spinner("Querying Gemini..."):
                g_res = loop.run_until_complete(gemini_call(u_prompt, st.session_state.k_gm, st.session_state.auto_model))
        st.session_state.history = {"l": l_res, "g": g_res, "raw": u_prompt, "mod": st.session_state.auto_model}
        st.rerun()

with col_r:
    st.markdown('<div class="section-label">Security Analytics</div>', unsafe_allow_html=True)
    if st.session_state.history:
        h = st.session_state.history
        is_bad = h["l"]["flagged"]
        verdict_html = '<span class="badge-blocked">🛑&nbsp; High Risk — Blocked</span>' if is_bad else '<span class="badge-clean">✅&nbsp; Clean — Passed</span>'

        st.markdown(f"""
        <div class="metric-row">
            <div class="metric-box"><div class="metric-label">Lakera Result</div><div class="metric-value {'danger' if is_bad else 'success'}">{'BLOCKED' if is_bad else 'PASSED'}</div></div>
            <div class="metric-box"><div class="metric-label">Model Used</div><div class="metric-value" style="font-size:14px;">{h['mod']}</div></div>
        </div>
        <div class="card">
            <div class="card-title">Audit Log</div>
            <div style="font-size:12px;font-weight:800;color:#2D334A;margin-bottom:4px;">CAPTURED INPUT</div>
            <div class="captured-block">{h['raw']}</div>
            <div style="font-size:12px;font-weight:800;color:#2D334A;margin-bottom:8px;">VERDICT</div>
            {verdict_html}
        </div>
        <div class="card">
            <div class="card-title">AI Response</div>
            <div class="response-block {'blocked' if is_bad else ''}">{h['g']}</div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.markdown('<div class="empty-state" style="height:420px; border: 2px dashed #CBD5E1; border-radius: 14px; display: flex; align-items: center; justify-content: center; color: #4A4F63; font-weight:600;">📊 Awaiting analysis — enter a prompt and run.</div>', unsafe_allow_html=True)

st.markdown('<div class="footer">Check Point Software Technology &copy; 2026 &nbsp;·&nbsp; AI Defense Plane</div>', unsafe_allow_html=True)
