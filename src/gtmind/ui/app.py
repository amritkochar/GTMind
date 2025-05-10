"""
Minimal Streamlit UI for GTMind research agent.
Run with:  poetry run streamlit run src/gtmind/ui/app.py
"""
from __future__ import annotations

import json
import os
import requests
import streamlit as st

BACKEND_URL = os.getenv("GTMIND_API_URL", "http://127.0.0.1:8000")

st.set_page_config(page_title="GTMind Research UI", layout="wide")
st.title("🔎 GTMind Research Agent")

query = st.text_input("Enter your topic (e.g., 'AI in retail')", value="AI in retail")

if st.button("Run Research") and query.strip():
    with st.spinner("Running pipeline… this may take 30-60 s"):
        resp = requests.get(f"{BACKEND_URL}/report", params={"q": query}, timeout=120)
    if resp.status_code != 200:
        st.error(f"Backend error {resp.status_code}: {resp.text[:200]}")
        st.stop()

    data = resp.json()
    st.success("Done! Scroll for insights.")

    # --- TRENDS ------------------------------------------------------------
    st.subheader("🚀 Key Trends")
    for t in data["trends"]:
        st.markdown(f"**• {t['text']}**")
        with st.expander("Sources"):
            for s in t["sources"]:
                st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

    # --- COMPANIES ---------------------------------------------------------
    st.subheader("🏢 Companies Mentioned")
    for c in data["companies"]:
        st.markdown(f"**• {c['name']}** — _{c.get('context', 'context TBD')}_")
        with st.expander("Sources"):
            for s in c["sources"]:
                st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

    # --- WHITESPACE --------------------------------------------------------
    st.subheader("💡 Whitespace Opportunities")
    for w in data["whitespace_opportunities"]:
        st.markdown(f"**• {w['description']}**")
        with st.expander("Sources"):
            for s in w["sources"]:
                st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

    # --- RAW JSON ----------------------------------------------------------
    with st.expander("Raw JSON"):
        st.code(json.dumps(data, indent=2), language="json")
