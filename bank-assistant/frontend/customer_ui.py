from __future__ import annotations

import os
import textwrap

import httpx
import streamlit as st
from dotenv import load_dotenv

load_dotenv()


DEFAULT_API_BASE = os.getenv("API_BASE_URL", "http://127.0.0.1:8000")


def call_chat(api_base: str, message: str) -> dict:
    api_base = (api_base or "").rstrip("/")
    with httpx.Client(timeout=180.0) as client:
        r = client.post(f"{api_base}/chat", json={"message": message})
        r.raise_for_status()
        data = r.json()
        return {
            "response": data.get("response", ""),
            "sources": data.get("sources", []) or [],
        }


def inject_css() -> None:
    st.markdown(
        """
<style>
  :root{
    --bb-a: #7c3aed;   /* violet */
    --bb-b: #06b6d4;   /* cyan */
    --bb-c: #22c55e;   /* green */
    --bb-d: #f97316;   /* orange */
    --bb-card: rgba(255,255,255,0.08);
    --bb-border: rgba(255,255,255,0.14);
    --bb-text: rgba(255,255,255,0.92);
    --bb-muted: rgba(255,255,255,0.72);
  }

  /* page width */
  .block-container {
    padding-top: 0.6rem;
    padding-bottom: 0.6rem;
    max-width: 980px;
  }

  /* remove Streamlit chrome whitespace */
  header[data-testid="stHeader"] { display: none; }
  footer { visibility: hidden; height: 0; }
  #MainMenu { visibility: hidden; }

  /* remove extra top/bottom space around the whole app */
  [data-testid="stAppViewContainer"] > .main { padding-top: 0rem; padding-bottom: 0rem; }

  /* background */
  [data-testid="stAppViewContainer"]{
    background:
      radial-gradient(900px 500px at 10% 5%, rgba(124,58,237,0.35), transparent 60%),
      radial-gradient(700px 500px at 85% 10%, rgba(6,182,212,0.26), transparent 55%),
      radial-gradient(800px 550px at 40% 95%, rgba(34,197,94,0.20), transparent 55%),
      linear-gradient(180deg, rgba(2,6,23,0.98), rgba(2,6,23,0.92));
  }

  /* subtle pattern overlay so “empty” areas still look designed */
  [data-testid="stAppViewContainer"]::before{
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background:
      radial-gradient(circle at 20px 20px, rgba(255,255,255,0.06) 1px, transparent 1px);
    background-size: 34px 34px;
    opacity: 0.35;
    mix-blend-mode: overlay;
  }

  /* soft vignette */
  [data-testid="stAppViewContainer"]::after{
    content: "";
    position: fixed;
    inset: 0;
    pointer-events: none;
    background: radial-gradient(1200px 700px at 50% 10%, transparent 40%, rgba(0,0,0,0.55));
    opacity: 0.35;
  }

  /* sidebar background */
  [data-testid="stSidebar"] > div{
    background: linear-gradient(180deg, rgba(15,23,42,0.92), rgba(2,6,23,0.92));
    border-right: 1px solid rgba(255,255,255,0.08);
  }

  /* subtle gradient header */
  .bankbot-hero {
    border: 1px solid var(--bb-border);
    background:
      linear-gradient(135deg, rgba(124,58,237,0.30), rgba(6,182,212,0.18) 55%, rgba(34,197,94,0.16));
    padding: 18px 18px;
    border-radius: 18px;
    margin-bottom: 14px;
    box-shadow: 0 10px 30px rgba(0,0,0,0.35);
  }
  .bankbot-hero h1 { margin: 0; font-size: 1.6rem; line-height: 1.2; }
  .bankbot-hero p { margin: 6px 0 0 0; opacity: 0.92; color: var(--bb-text); }

  /* glass panels */
  .stExpander, [data-testid="stExpander"]{
    border: 1px solid rgba(255,255,255,0.10) !important;
    border-radius: 16px !important;
    background: rgba(255,255,255,0.04) !important;
    backdrop-filter: blur(10px);
  }

  /* chat bubbles: give them a bit more “card” feel */
  [data-testid="stChatMessage"]{
    border: 1px solid rgba(255,255,255,0.08);
    background: rgba(255,255,255,0.03);
    border-radius: 16px;
    padding: 10px 12px;
    margin: 10px 0;
    backdrop-filter: blur(10px);
  }

  /* make the chat input area feel grounded */
  [data-testid="stChatInput"]{
    border-top: 1px solid rgba(255,255,255,0.10);
    padding-top: 8px;
  }

  /* buttons */
  .stButton > button {
    border: 1px solid rgba(255,255,255,0.14) !important;
    border-radius: 14px !important;
    padding: 0.55rem 0.8rem !important;
    background: linear-gradient(135deg, rgba(124,58,237,0.82), rgba(6,182,212,0.70)) !important;
    color: white !important;
    box-shadow: 0 8px 18px rgba(0,0,0,0.35);
    transition: transform 120ms ease, filter 120ms ease, box-shadow 120ms ease;
  }
  .stButton > button:hover{
    transform: translateY(-1px) scale(1.01);
    filter: brightness(1.06);
    box-shadow: 0 10px 22px rgba(0,0,0,0.42);
  }
  .stButton > button:active{
    transform: translateY(0px) scale(0.99);
    filter: brightness(0.98);
  }

  /* text inputs */
  .stTextInput input{
    border-radius: 14px !important;
  }

  /* source cards */
  .source-card {
    border: 1px solid rgba(255,255,255,0.12);
    border-radius: 16px;
    padding: 12px 12px;
    margin: 10px 0;
    background:
      linear-gradient(135deg, rgba(255,255,255,0.06), rgba(255,255,255,0.03));
    box-shadow: 0 10px 26px rgba(0,0,0,0.25);
  }
  .source-url { font-size: 0.85rem; opacity: 0.92; word-break: break-word; }
  .source-snippet { margin-top: 6px; opacity: 0.88; font-size: 0.92rem; color: var(--bb-muted); }

  /* nicer sidebar sections */
  .sidebar-note {
    font-size: 0.9rem;
    opacity: 0.92;
    line-height: 1.4;
  }

  /* brighter text */
  .stMarkdown, .stCaption { color: var(--bb-text); }

  /* animated loader */
  .bb-loader-wrap{
    display:flex;
    align-items:center;
    gap:10px;
    padding: 10px 12px;
    border-radius: 14px;
    border: 1px solid rgba(255,255,255,0.10);
    background: rgba(255,255,255,0.04);
    backdrop-filter: blur(10px);
  }
  .bb-dot{
    width: 8px;
    height: 8px;
    border-radius: 999px;
    background: linear-gradient(135deg, var(--bb-b), var(--bb-a));
    animation: bb-bounce 1.0s infinite ease-in-out;
  }
  .bb-dot:nth-child(2){ animation-delay: 0.12s; opacity: 0.85; }
  .bb-dot:nth-child(3){ animation-delay: 0.24s; opacity: 0.70; }
  @keyframes bb-bounce{
    0%, 80%, 100% { transform: translateY(0); }
    40% { transform: translateY(-6px); }
  }
</style>
        """,
        unsafe_allow_html=True,
    )


def render_sources(sources: list[dict]) -> None:
    if not sources:
        st.caption("No sources returned.")
        return

    for s in sources[:2]:
        url = (s.get("url") or "").strip()
        snippet = (s.get("snippet") or "").strip()
        safe_snippet = textwrap.shorten(snippet.replace("\n", " "), width=280, placeholder="…")

        st.markdown(
            f"""
<div class="source-card">
  <div class="source-url"><a href="{url}" target="_blank">{url}</a></div>
  <div class="source-snippet">{safe_snippet}</div>
</div>
            """,
            unsafe_allow_html=True,
        )


def main() -> None:
    st.set_page_config(page_title="Conversational Banking Assistant", layout="centered")
    inject_css()

    st.markdown(
        """
<div class="bankbot-hero">
  <h1>Conversational Banking Assistant</h1>
  <p>Ask about Pakistani banks: profit rates, products, leadership, and SBP basics. Sources are shown when available.</p>
</div>
        """,
        unsafe_allow_html=True,
    )

    api_base = st.sidebar.text_input("API base URL", value=DEFAULT_API_BASE)
    st.sidebar.markdown("#### Quick prompts")
    st.sidebar.caption("Click one to fill the chat box.")

    c1, c2 = st.sidebar.columns(2)
    with c1:
        if st.button("SBP policy rate", use_container_width=True):
            st.session_state["draft"] = "What is the SBP policy rate today?"
        if st.button("Meezan CEO", use_container_width=True):
            st.session_state["draft"] = "Who is Meezan Bank CEO?"
    with c2:
        if st.button("HBL profit rates", use_container_width=True):
            st.session_state["draft"] = "What are HBL's latest profit rates?"
        if st.button("MCB home loans", use_container_width=True):
            st.session_state["draft"] = "Explain MCB home loan options and key requirements."

    st.sidebar.markdown("---")
    st.sidebar.markdown("#### Tips")
    st.sidebar.markdown(
        '<div class="sidebar-note">Try: “Compare HBL vs MCB home loans”, “Latest news about Bank Alfalah”, '
        'or “Meezan car ijarah markup”.</div>',
        unsafe_allow_html=True,
    )

    if "messages" not in st.session_state:
        st.session_state.messages = []

    for m in st.session_state.messages:
        with st.chat_message(m["role"], avatar="👤" if m["role"] == "user" else "🏦"):
            st.markdown(m["content"])
            if m["role"] == "assistant" and m.get("sources"):
                with st.expander("Sources", expanded=False):
                    render_sources(m["sources"])

    prompt = st.chat_input("Ask a question…", key="chat_input")
    draft = st.session_state.pop("draft", None)
    if draft and not prompt:
        prompt = draft

    if not prompt:
        return

    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user", avatar="👤"):
        st.markdown(prompt)

    with st.chat_message("assistant", avatar="🏦"):
        loader_slot = st.empty()
        loader_slot.markdown(
            """
<div class="bb-loader-wrap">
  <div class="bb-dot"></div><div class="bb-dot"></div><div class="bb-dot"></div>
  <div style="opacity:0.85;">Thinking…</div>
</div>
            """,
            unsafe_allow_html=True,
        )
        try:
            with st.spinner("Generating response…"):
                result = call_chat(api_base, prompt)
            answer = (result.get("response") or "").strip() or "(No response)"
            sources = result.get("sources") or []
        except Exception as e:
            answer = f"**Error:** {e}"
            sources = []
        finally:
            loader_slot.empty()

        st.markdown(answer)
        if sources:
            with st.expander("Sources", expanded=False):
                render_sources(sources)

    st.session_state.messages.append(
        {"role": "assistant", "content": answer, "sources": sources}
    )


if __name__ == "__main__":
    main()

