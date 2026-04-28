import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
from pptx import Presentation
import json
import os
import shutil

# 1. Configurare Pagină
st.set_page_config(page_title="Strategio AI", page_icon="💼", layout="wide")

# ==========================================
# FUNCȚII DE GESTIONARE DATE (FISIERE SI ISTORIC)
# ==========================================

def get_user_folder(utilizator):
    """Creează și returnează folderul personal al utilizatorului."""
    cale = f"data_room_{utilizator}"
    if not os.path.exists(cale):
        os.makedirs(cale)
    return cale

def incarca_istoric(utilizator):
    nume_fisier = f"istoric_{utilizator}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []

def salveaza_istoric(utilizator, mesaje):
    nume_fisier = f"istoric_{utilizator}.json"
    with open(nume_fisier, "w", encoding="utf-8") as f:
        json.dump(mesaje, f, ensure_ascii=False, indent=4)

def citeste_text_din_folder(folder_utilizator):
    """Citește toate fișierele salvate anterior în folderul utilizatorului."""
    text_total = ""
    for nume_fisier in os.listdir(folder_utilizator):
        cale_completa = os.path.join(folder_utilizator, nume_fisier)
        extensie = nume_fisier.split('.')[-1].lower()
        text_total += f"\n\n--- DOCUMENT: {nume_fisier} ---\n"
        try:
            if extensie == "pdf":
                with open(cale_completa, "rb") as f:
                    pdf_reader = PyPDF2.PdfReader(f)
                    for pagina in pdf_reader.pages:
                        text_total += pagina.extract_text() + "\n"
            elif extensie == "docx":
                doc = docx.Document(cale_completa)
                for p in doc.paragraphs:
                    text_total += p.text + "\n"
            elif extensie == "xlsx":
                df = pd.read_excel(cale_completa)
                text_total += df.to_string() + "\n"
            elif extensie == "txt":
                with open(cale_completa, "r", encoding="utf-8") as f:
                    text_total += f.read() + "\n"
        except Exception as e:
            text_total += f"[Eroare citire {nume_fisier}: {e}]\n"
    return text_total

# --- SISTEMUL DE LOGIN ---
if "logat" not in st.session_state:
    st.session_state.logat = False
    st.session_state.utilizator_curent = ""

if not st.session_state.logat:
    st.title("🔐 Portal Securizat: Strategio AI")
    user_input = st.text_input("Nume utilizator (ID Companie):")
    pass_input = st.text_input("Parolă:", type="password")
    
    if st.button("Autentificare"):
        if user_input in st.secrets["passwords"] and st.secrets["passwords"][user_input] == pass_input:
            st.session_state.logat = True
            st.session_state.utilizator_curent = user_input
            # Încărcăm istoricul imediat la login
            st.session_state.mesaje = incarca_istoric(user_input)
            st.rerun()
        else:
            st.error("Credențiale incorecte!")

# --- APLICAȚIA PRINCIPALĂ ---
else:
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    user_path = get_user_folder(st.session_state.utilizator_curent)

    st.title(f"💼 Strategio AI")
    
    # Sidebar
    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.rerun()

    departament = st.sidebar.selectbox(
        "Filtru Departamental:", 
        ("Management & Strategie", "Financiar", "Juridic", "Resurse Umane", "Marketing", "Vânzări", "Operațiuni & Logistică", "IT & Securitate")
    )

    # ==========================================
    # GESTIONARE DATA ROOM (SIDEBAR)
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Data Room (Documente Salvate)")
    
    # Upload fișiere noi
    fisiere_noi = st.sidebar.file_uploader("Încarcă documente noi:", accept_multiple_files=True)
    if fisiere_noi:
        for f in fisiere_noi:
            with open(os.path.join(user_path, f.name), "wb") as buffer:
                buffer.write(f.getbuffer())
        st.sidebar.success("Fișiere salvate!")
        st.rerun()

    # Listare fișiere existente + Buton Ștergere
    fisiere_existente = os.listdir(user_path)
    if fisiere_existente:
        for f_nume in fisiere_existente:
            col1, col2 = st.sidebar.columns([3, 1])
            col1.caption(f"📄 {f_nume}")
            if col2.button("🗑️", key=f_nume):
                os.remove(os.path.join(user_path, f_nume))
                st.rerun()
        
        if st.sidebar.button("⚠️ Șterge Tot"):
            shutil.rmtree(user_path)
            os.makedirs(user_path)
            st.rerun()
    else:
        st.sidebar.info("Data Room este gol.")

    # Pregătire text din toate documentele salvate
    text_context = citeste_text_din_folder(user_path)

    # Prompt de sistem
    context_system = f"""Ești un Senior Business Analyst assignment pe departamentul: {departament}. 
    Analizează documentele și oferă răspunsuri sub formă de Rezumat Executiv, folosind text cursiv. 
    DATE DIN DATA ROOM: {text_context}"""

    # Afișare chat
    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    for m in st.session_state.mesaje:
        with st.chat_message(m["rol"]):
            st.markdown(m["continut"])

    # Chat Input
    if intrebare := st.chat_input("Întrebați ceva despre documentele din Data Room..."):
        st.session_state.mesaje.append({"rol": "user", "continut": intrebare})
        with st.chat_message("user"):
            st.markdown(intrebare)

        # Apel API
        mesaje_api = [{"role": "system", "content": context_system}]
        for m in st.session_state.mesaje:
            mesaje_api.append({"role": m["rol"], "content": m["continut"]})

        with st.chat_message("assistant"):
            # Notă: Am corectat modelul la gpt-4 (sau gpt-3.5-turbo), gpt-5.4 nu există încă
            stream = client.chat.completions.create(
                model="gpt-4-turbo", 
                messages=mesaje_api,
                stream=True
            )
            raspuns = st.write_stream(stream)
        
        st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns})
        salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)
