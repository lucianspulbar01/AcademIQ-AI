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
# FUNCȚII DE GESTIONARE DATE (FISIERE, ISTORIC, PROFIL)
# ==========================================

def get_user_folder(utilizator):
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

def incarca_profil(utilizator):
    nume_fisier = f"profil_{utilizator}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return {}
    return {"nume": "", "caen": "", "localitate": "", "obiective": ""}

def salveaza_profil(utilizator, profil):
    nume_fisier = f"profil_{utilizator}.json"
    with open(nume_fisier, "w", encoding="utf-8") as f:
        json.dump(profil, f, ensure_ascii=False, indent=4)

def citeste_text_din_folder(folder_utilizator):
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
            st.session_state.mesaje = incarca_istoric(user_input)
            st.rerun()
        else:
            st.error("Credențiale incorecte!")

# --- APLICAȚIA PRINCIPALĂ ---
else:
    client = OpenAI(api_key=st.secrets["openai_api_key"])
    user_path = get_user_folder(st.session_state.utilizator_curent)

    st.title(f"💼 Strategio AI")
    
    # Buton Deconectare sus în sidebar
    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.rerun()

    # Meniul de departamente
    departament = st.sidebar.selectbox(
        "Filtru Departamental:", 
        ("Management & Strategie", "Financiar", "Juridic", "Resurse Umane", "Marketing", "Vânzări", "Operațiuni & Logistică", "IT & Securitate")
    )

    # ==========================================
    # ZONA NOUĂ: PROFILUL COMPANIEI
    # ==========================================
    profil_curent = incarca_profil(st.session_state.utilizator_curent)
    
    with st.sidebar.expander("🏢 Profil Companie (Context AI)", expanded=False):
        st.caption("Aceste date ajută AI-ul să ofere răspunsuri specifice pieței tale.")
        nume_comp = st.text_input("Nume Companie", value=profil_curent.get("nume", ""))
        caen_comp = st.text_input("Cod CAEN / Domeniu", value=profil_curent.get("caen", ""))
        loc_comp = st.text_input("Localitate / Zonă target", value=profil_curent.get("localitate", ""))
        obj_comp = st.text_area("Obiective (ex: Creștere profit cu 20%)", value=profil_curent.get("obiective", ""))
        
        if st.button("Salvează Profilul"):
            profil_nou = {
                "nume": nume_comp,
                "caen": caen_comp,
                "localitate": loc_comp,
                "obiective": obj_comp
            }
            salveaza_profil(st.session_state.utilizator_curent, profil_nou)
            st.success("Profil salvat cu succes!")

    # ==========================================
    # GESTIONARE DATA ROOM (SIDEBAR)
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Data Room (Documente Salvate)")
    
    fisiere_noi = st.sidebar.file_uploader("Încarcă documente noi:", accept_multiple_files=True)
    if fisiere_noi
