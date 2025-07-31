# variobot.py
"""Streamlit app for Vario bot
--------------------------------
• Dropdown se seznamem modulů → odešle název vybraného modulu do Make.
• Automaticky přijímá text přes ?payload= a zobrazí ho + DOCX download.
"""

import io
import json
import urllib.parse
from typing import Any, Dict, Optional

import requests
import streamlit as st
from docx import Document

# ==============  Nastavení  ==============

WEBHOOK_URL = "https://hook.eu2.make.com/6dobqwk57qdm23w6p09pgvnmrrl9qp72"
PAGE_TITLE = "Vario Bot – Landing-page generátor"
PAGE_ICON = "📝"
REQUEST_TIMEOUT = 30  # s

MODULE_OPTIONS = [
    "Adresář",
    "Banka",
    "Bilanční přehledy",
    "CRM",
    "Majetek",
    "Mzdy",
    "Přijaté doklady",
    "Servis",
    "Skladové hospodářství",
    "Výroba",
    "Vydané doklady",
]

st.set_page_config(page_title=PAGE_TITLE, page_icon=PAGE_ICON, layout="centered")
st.title("📝 Generátor (a příjemce) popisků modulů ERP Vario")

# ============== Pomocné funkce ==============

def extract_text(payload_raw: str) -> Optional[str]:
    try:
        decoded = urllib.parse.unquote_plus(payload_raw)
        data: Dict[str, Any] = json.loads(decoded)
    except (json.JSONDecodeError, TypeError):
        return None
    return data.get("result") or data.get("text")


def build_docx(data: Dict[str, Any]) -> bytes:
    doc = Document()
    title = data.get("module", "Vario modul")
    doc.add_heading(title, level=1)

    text_block = data.get("Text") or data.get("result")
    if text_block:
        doc.add_paragraph(str(text_block))
    else:
        for key, val in data.items():
            if key == "module":
                continue
            doc.add_heading(str(key), level=2)
            doc.add_paragraph(str(val))

    buffer = io.BytesIO()
    doc.save(buffer)
    buffer.seek(0)
    return buffer.getvalue()


# ============== 1) Formulář – dropdown ==============

st.header("🔸 Vyber modul a odešli do Make")
with st.form(key="mod_form", clear_on_submit=True):
    module_name = st.selectbox("Modul", MODULE_OPTIONS, index=0)
    submitted = st.form_submit_button("Odeslat")

if submitted:
    payload_out = {"module_name": module_name}
    try:
        resp = requests.post(WEBHOOK_URL, json=payload_out, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        st.error(f"❌ Nepodařilo se odeslat: {exc}")
    else:
        st.success("✅ Název modulu byl odeslán do Make.")
        st.json(payload_out)

# ============== 2) Automatický příjem & zobrazení textu ==============

raw_payload = st.query_params.get("payload")
if isinstance(raw_payload, list):
    raw_payload = raw_payload[0]

final_text = extract_text(raw_payload) if raw_payload else None

if final_text:
    st.divider()
    st.success("✅ Text přijat z Make webhooku")
    st.subheader("📄 Výstupní text")
    st.markdown(final_text, unsafe_allow_html=True)

    docx_bytes = build_docx({"module": "Výstup z Make", "Text": final_text})
    st.download_button(
        "💾 Stáhnout DOCX",
        docx_bytes,
        file_name="landing_page.docx",
        mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )
    st.stop()

# ============== 3) Ruční JSON fallback ==============

st.divider()
st.header("🔸 Ruční JSON fallback")
json_input = st.text_area(
    "Vlož JSON, nebo přidej do URL ?payload= …:",
    value="",
    height=160,
)

if st.button("Zobraz JSON"):
    try:
        data_dict = json.loads(json_input)
    except json.JSONDecodeError as err:
        st.error(f"Neplatný JSON: {err}")
        st.stop()

    st.json(data_dict)
    text_part = data_dict.get("result") or data_dict.get("text")
    if text_part:
        st.markdown(text_part, unsafe_allow_html=True)
        docx_bytes = build_docx({"module": "Ruční JSON", "Text": text_part})
        st.download_button(
            "💾 Stáhnout DOCX",
            docx_bytes,
            file_name="landing_manual.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )
    else:
        st.info("V JSONu není klíč 'result' ani 'text'.")
