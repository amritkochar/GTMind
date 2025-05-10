"""
Streamlit UI for GTMind research agent.
Run with:  poetry run streamlit run src/gtmind/ui/app.py
"""
from __future__ import annotations

import itertools
import json
import os
from pathlib import Path

import requests
import streamlit as st

from gtmind.persistence import list_saved_reports

# ------------------------------------------------------------------------- #
# Config defaults (can override via env vars)
# ------------------------------------------------------------------------- #
BACKEND_URL = os.getenv("GTMIND_API_URL", "http://127.0.0.1:8000")
DEFAULT_DB = os.getenv("GTMIND_DB_PATH", "my.db")

st.set_page_config(page_title="GTMind Research UI", layout="wide")
st.title("🔎 GTMind Research Agent")

# ------------------------------------------------------------------------- #
# Sidebar – choose DB, then recent reports
# ------------------------------------------------------------------------- #
st.sidebar.header("📚 Saved Reports")

db_path = Path(DEFAULT_DB).expanduser()

if db_path.exists():
    recent_rows = list_saved_reports(db_path)[:5]
else:
    recent_rows = []
    st.sidebar.warning(f"No DB found at {db_path}")

selected_query = None
loaded_data = None

if recent_rows:
    def label(r):
        return f"{r.id} · {r.query[:50]}"
    choice = st.sidebar.selectbox("Select a report:", recent_rows, format_func=label)
    selected_query = choice.query
    loaded_data = json.loads(choice.json)
else:
    st.sidebar.info("No saved reports in this DB yet.")

# ------------------------------------------------------------------------- #
# Main input area
# ------------------------------------------------------------------------- #
query_input = st.text_input("Run a new query", value=selected_query or "AI in retail")
run_btn = st.button("🔄 Run Research")

data = None
if run_btn and query_input.strip():
    with st.spinner("Running pipeline… please wait"):
        resp = requests.get(f"{BACKEND_URL}/report", params={"q": query_input}, timeout=120)
    if resp.status_code == 200:
        data = resp.json()
        st.success("Done! Scroll for insights.")
    else:
        st.error(f"Backend error {resp.status_code}: {resp.text[:200]}")

# If user picked an existing report but didn’t click run
if loaded_data and not data:
    data = loaded_data
    st.info("Showing saved report from DB.")

if not data:
    st.stop()

# ------------------------------------------------------------------------- #
# Render sections
# ------------------------------------------------------------------------- #
st.subheader("🚀 Key Trends")
for t in data["trends"]:
    st.markdown(f"**• {t['text']}**")
    with st.expander("Sources"):
        for s in t["sources"]:
            st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

st.divider()

st.subheader("🏢 Companies Mentioned")
left, right = st.columns(2)
cols = itertools.cycle([left, right])
for c in data["companies"]:
    col = next(cols)
    with col:
        st.markdown(f"**{c['name']}**  \n_{c.get('context', 'context TBD')}_")
        with st.expander("Sources"):
            for s in c["sources"]:
                st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

st.divider()

st.subheader("💡 Whitespace Opportunities")
for w in data["whitespace_opportunities"]:
    st.markdown(
        f"<span style='color:green'>• {w['description']}</span>",
        unsafe_allow_html=True,
    )
    with st.expander("Sources"):
        for s in w["sources"]:
            st.markdown(f"- [{s['title'] or s['url']}]({s['url']})", unsafe_allow_html=True)

with st.expander("Raw JSON"):
    st.code(json.dumps(data, indent=2), language="json")
