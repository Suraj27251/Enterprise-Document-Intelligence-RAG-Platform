"""Streamlit dashboard for uploading documents and asking RAG questions."""

from __future__ import annotations

import requests
import streamlit as st

API_BASE = st.secrets.get("api_base", "http://localhost:8000/api/v1")

st.set_page_config(page_title="Enterprise Document Intelligence", layout="wide")
st.title("📄 Enterprise Document Intelligence Platform")

with st.sidebar:
    st.subheader("Authentication")
    username = st.text_input("Username", value="demo-user")
    role = st.selectbox("Role", options=["User", "Admin"], index=0)
    auth_clicked = st.button("Generate token")

if "token" not in st.session_state:
    st.session_state["token"] = ""

if auth_clicked:
    response = requests.post(f"{API_BASE}/auth/token", json={"username": username, "role": role}, timeout=20)
    if response.ok:
        st.session_state["token"] = response.json()["access_token"]
        st.success("Token generated.")
    else:
        st.error(f"Failed to generate token: {response.text}")

st.write("### Upload documents")
files = st.file_uploader("Upload .txt and .pdf documents", type=["txt", "pdf"], accept_multiple_files=True)
if st.button("Upload & Index", disabled=not files):
    multipart = [("files", (file.name, file.getvalue(), file.type or "application/octet-stream")) for file in files]
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    resp = requests.post(f"{API_BASE}/upload", files=multipart, headers=headers, timeout=60)
    if resp.ok:
        st.success(resp.json())
    else:
        st.error(resp.text)

st.write("### Ask a question")
query = st.text_input("Natural language query", placeholder="What are the key obligations in the MSA?")
if st.button("Search", disabled=not query.strip()):
    headers = {"Authorization": f"Bearer {st.session_state['token']}"}
    resp = requests.get(f"{API_BASE}/search", params={"query": query}, headers=headers, timeout=60)
    if resp.ok:
        payload = resp.json()
        st.markdown("#### Answer")
        st.write(payload["answer"])
        st.markdown("#### Relevant context")
        for source in payload.get("sources", []):
            st.info(f"Source: {source['source']} (chunk {source['chunk_id']})\n\n{source['text']}")
    else:
        st.error(resp.text)
