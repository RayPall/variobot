import streamlit as st
import requests

WEBHOOK_URL = "https://hook.eu2.make.com/6dobqwk57qdm23w6p09pgvnmrrl9qp72"

st.set_page_config(page_title="Vario Modul Popisek", page_icon="📝")

st.title("Generátor popisků modulů ERP Vario")
st.write(
    """
    Zadejte název modulu ERP systému Vario.  
    Po odeslání bude název modulu předán do Make (Integromat) skrze připravený webhook,
    který následně spustí automatizaci pro vygenerování popisku.
    """
)

with st.form(key="mod_form", clear_on_submit=True):
    module_name = st.text_input("Název modulu", placeholder="Např. Skladové hospodářství")
    submitted = st.form_submit_button("Odeslat do Make")

if submitted:
    if not module_name.strip():
        st.warning("Prosím, vyplňte název modulu.")
        st.stop()

    payload = {"module_name": module_name.strip()}

    try:
        resp = requests.post(WEBHOOK_URL, json=payload, timeout=10)
        resp.raise_for_status()
    except requests.exceptions.RequestException as exc:
        st.error(f"❌ Nepodařilo se odeslat: {exc}")
    else:
        st.success("✅ Název modulu byl úspěšně odeslán do Make.")
        st.json(payload)  # zobrazí, co se odeslalo
