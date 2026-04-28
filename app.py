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
    if fisiere_noi:
        for f in fisiere_noi:
            with open(os.path.join(user_path, f.name), "wb") as buffer:
                buffer.write(f.getbuffer())
        st.sidebar.success("Fișiere salvate!")
        st.rerun()

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

    text_context = citeste_text_din_folder(user_path)

    # ==========================================
    # INJECTAREA PROFILULUI ÎN CREIERUL AI-ULUI
    # ==========================================
    context_profil = ""
    if profil_curent.get("nume") or profil_curent.get("caen") or profil_curent.get("localitate") or profil_curent.get("obiective"):
        context_profil = f"""
        DATE DESPRE COMPANIA CLIENTULUI (pentru contextualizarea răspunsurilor):
        - Nume: {profil_curent.get("nume", "Nespecificat")}
        - Domeniu/CAEN: {profil_curent.get("caen", "Nespecificat")}
        - Localitate/Piață target: {profil_curent.get("localitate", "Nespecificată")}
        - Obiective principale: {profil_curent.get("obiective", "Nespecificate")}
        Te rog să ții cont obligatoriu de aceste date, de piața locală aferentă și de domeniu atunci când formulezi analizele și soluțiile.
        """

    context_system = f"""Ești un Senior Business Analyst assignment pe departamentul: {departament}. 
    Analizează documentele și oferă răspunsuri sub formă de Rezumat Executiv, folosind text cursiv. 
    {context_profil}
    DATE DIN DATA ROOM: {text_context}"""

    # ==========================================
    # AFIȘARE CHAT (STÂNGA) ȘI ISTORIC (DREAPTA)
    # ==========================================
    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    # Împărțim ecranul: 3 părți pentru chat, 1 parte pentru istoricul din dreapta
    col_chat, col_istoric = st.columns([3, 1])

    # --- ZONA DIN DREAPTA (Istoricul) ---
    with col_istoric:
        st.subheader("🕒 Memorie Chat")
        st.info(f"Mesaje în memorie: {len(st.session_state.mesaje)}")
        
        st.caption("AI-ul citește aceste mesaje pentru a înțelege contextul discuției curente.")
        
        # Buton pentru a șterge memoria AI-ului dacă vrem să începem o analiză complet nouă
        if st.button("🗑️ Șterge conversația", use_container_width=True):
            st.session_state.mesaje = []
            salveaza_istoric(st.session_state.utilizator_curent, [])
            st.rerun()

    # --- ZONA DIN STÂNGA (Chat-ul Principal) ---
    with col_chat:
        for m in st.session_state.mesaje:
            with st.chat_message(m["rol"]):
                st.markdown(m["continut"])

        # Chat Input
        if intrebare := st.chat_input("Întrebați ceva despre documentele din Data Room..."):
            st.session_state.mesaje.append({"rol": "user", "continut": intrebare})
            with st.chat_message("user"):
                st.markdown(intrebare)

            mesaje_api = [{"role": "system", "content": context_system}]
            for m in st.session_state.mesaje:
                mesaje_api.append({"role": m["rol"], "content": m["continut"]})

            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model="gpt-4-turbo", 
                    messages=mesaje_api,
                    stream=True
                )
                raspuns = st.write_stream(stream)
            
            st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns})
            salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)
