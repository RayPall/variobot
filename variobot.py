# variobot.py
import json
import io
import urllib.parse

import requests
import streamlit as st
from docx import Document

WEBHOOK_URL = "https://hook.eu2.make.com/6dobqwk57qdm23w6p09pgvnmrrl9qp72"

st.set_page_config(page_title="Vario Modul Popisek", page_icon="📝")

st.title("Generátor (a příjemce) popisků modulů ERP Vario")

# ---------- 1) FORM – ODESLAT NÁZEV MODULU DO MAKE ----------
st.header("🔸 Odeslat název modulu do Make")
with st.form(key="mod_form", clear_on_submit=True):
    module_name = st.text_input("Název modulu", placeholder="Např. Skladové hospodářství")
    submitted = st.form_submit_button("Odeslat")

if submitted:
    if not module_name.strip():
        st.warning("Prosím, vyplňte název modulu.")
        st.stop()

    payload_out = {"module_name": module_name.strip()}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload_out, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        st.error(f"❌ Nepodařilo se odeslat: {exc}")
    else:
        st.success("✅ Název modulu byl úspěšně odeslán do Make.")
        st.json(payload_out)

# ---------- 2) PŘEVZÍT JSON OD MAKE / UŽIVATELE ----------
st.divider()
st.header("🔸 Převzít a zpracovat JSON výstup")

# a) pokus se načíst ze query param ?payload=...
query_params = st.experimental_get_query_params()
qp_payload = query_params.get("payload", [None])[0]  # vrací první hodnotu nebo None

# b) nebo nech uživatele vložit ručně
json_input = st.text_area(
    "Vlož JSON string (nebo přidej do URL ?payload=…) :", 
    qp_payload or "", 
    height=150, 
    placeholder='{"module":"Sklad","hero":"…"}'
)

if st.button("Zpracovat JSON"):
    if not json_input.strip():
        st.warning("Do textového pole nic nebylo vloženo.")
        st.stop()

    # zkus rozparsovat
    try:
        payload_in = json.loads(json_input)
    except json.JSONDecodeError as e:
        st.error(f"JSON není validní: {e}")
        st.stop()

    st.success("✅ JSON načten.")
    st.subheader("📄 Náhled obsahu")
    st.json(payload_in)

    # ---------- 3) GENERUJ DOCX A NABÍDNI KE STAŽENÍ ----------
    def build_docx(data: dict) -> bytes:
        doc = Document()
        doc.add_heading(f"Vario modul – {data.get('module', 'Bez názvu')}", level=1)
        for key, val in data.items():
            if key == "module":
                continue
            doc.add_heading(key, level=2)
            doc.add_paragraph(str(val))
        buffer = io.BytesIO()
        doc.save(buffer)
        buffer.seek(0)
        return buffer.getvalue()

    docx_bytes = build_docx(payload_in)
    file_name = f"{payload_in.get('module', 'modul')}_landing.docx"

    st.download_button(
        label="💾 Stáhnout DOCX",
        data=docx_bytes,
        file_name=file_name,
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )

# 🛈  Všechno ostatní zůstává beze změny vůči původní aplikaci
