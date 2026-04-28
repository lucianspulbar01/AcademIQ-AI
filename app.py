import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
from pptx import Presentation
import json
import os
import shutil
from datetime import datetime

# 1. Configurare Pagină
st.set_page_config(page_title="Strategio AI", page_icon="💼", layout="wide")

# ==========================================
# BAZA DE DATE UTILIZATORI (Fără st.secrets)
# ==========================================
UTILIZATORI_PERMISI = {
    "luca": "parola_luca_123",
    "director": "parola_director_123"
}

# ==========================================
# FUNCȚII DE GESTIONARE DATE
# ==========================================
def get_user_folder(utilizator):
    cale = f"data_room_{utilizator}"
    if not os.path.exists(cale):
        os.makedirs(cale)
    return cale

def incarca_conversatii(utilizator):
    """Încarcă toate sesiunile de chat ale utilizatorului."""
    nume_fisier = f"conversatii_{utilizator}.json"
    if os.path.exists(nume_fisier):
        try:
            with open(nume_fisier, "r", encoding="utf-8") as f:
                date = json.load(f)
                # Dacă formatul e cel vechi (o simplă listă), îl convertim la dicționar
                if isinstance(date, list):
                    return {"Conversația Inițială": date}
                return date
        except:
            return {}
    return {}

def salveaza_conversatii(utilizator, dict_conversatii):
    """Salvează toate sesiunile de chat."""
    nume_fisier = f"conversatii_{utilizator}.json"
    with open(nume_fisier, "w", encoding="utf-8") as f:
        json.dump(dict_conversatii, f, ensure_ascii=False, indent=4)

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
        if user_input in UTILIZATORI_PERMISI and UTILIZATORI_PERMISI[user_input] == pass_input:
            st.session_state.logat = True
            st.session_state.utilizator_curent = user_input
            
            # Inițializăm baza de conversații
            st.session_state.toate_conversatiile = incarca_conversatii(user_input)
            if not st.session_state.toate_conversatiile:
                st.session_state.toate_conversatiile = {"Analiza Principală": []}
            st.session_state.sesiune_curenta = list(st.session_state.toate_conversatiile.keys())[-1]
            st.rerun()
        else:
            st.error("Credențiale incorecte!")

# --- APLICAȚIA PRINCIPALĂ ---
else:
    cheie_api = os.environ.get("OPENAI_API_KEY")
    client = OpenAI(api_key=cheie_api)
    user_path = get_user_folder(st.session_state.utilizator_curent)

    st.title(f"💼 Strategio AI")
    
    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.rerun()

    departament = st.sidebar.selectbox(
        "Filtru Departamental:", 
        ("Management & Strategie", "Financiar", "Juridic", "Resurse Umane", "Marketing", "Vânzări", "Operațiuni & Logistică", "IT & Securitate")
    )

    # ==========================================
    # PROFILUL COMPANIEI
    # ==========================================
    profil_curent = incarca_profil(st.session_state.utilizator_curent)
    with st.sidebar.expander("🏢 Profil Companie (Context AI)", expanded=False):
        nume_comp = st.text_input("Nume Companie", value=profil_curent.get("nume", ""))
        caen_comp = st.text_input("Cod CAEN / Domeniu", value=profil_curent.get("caen", ""))
        loc_comp = st.text_input("Localitate / Zonă", value=profil_curent.get("localitate", ""))
        obj_comp = st.text_area("Obiective", value=profil_curent.get("obiective", ""))
        
        if st.button("Salvează Profilul"):
            salveaza_profil(st.session_state.utilizator_curent, {"nume": nume_comp, "caen": caen_comp, "localitate": loc_comp, "obiective": obj_comp})
            st.success("Salvat!")

    # ==========================================
    # DATA ROOM (DOCUMENTAȚIE)
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Data Room")
    fisiere_noi = st.sidebar.file_uploader("Încarcă documente:", accept_multiple_files=True)
    if fisiere_noi:
        for f in fisiere_noi:
            with open(os.path.join(user_path, f.name), "wb") as buffer:
                buffer.write(f.getbuffer())
        st.rerun()

    fisiere_existente = os.listdir(user_path)
    if fisiere_existente:
        for f_nume in fisiere_existente:
            col1, col2 = st.sidebar.columns([3, 1])
            col1.caption(f"📄 {f_nume}")
            if col2.button("🗑️", key=f_nume):
                os.remove(os.path.join(user_path, f_nume))
                st.rerun()
        if st.sidebar.button("⚠️ Golește Data Room"):
            shutil.rmtree(user_path)
            os.makedirs(user_path)
            st.rerun()

    # ==========================================
    # NOUL SISTEM DE CONVERSAȚII (THREADS)
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("💬 Conversații")

    # Buton creare conversație nouă
    if st.sidebar.button("➕ Chat Nou", use_container_width=True):
        nume_nou = f"Sesiunea {len(st.session_state.toate_conversatiile) + 1} ({datetime.now().strftime('%H:%M')})"
        st.session_state.toate_conversatiile[nume_nou] = []
        st.session_state.sesiune_curenta = nume_nou
        salveaza_conversatii(st.session_state.utilizator_curent, st.session_state.toate_conversatiile)
        st.rerun()

    # Selector conversații vechi
    sesiune_aleasa = st.sidebar.radio(
        "Istoric:",
        list(st.session_state.toate_conversatiile.keys()),
        index=list(st.session_state.toate_conversatiile.keys()).index(st.session_state.sesiune_curenta)
    )

    # Dacă utilizatorul dă click pe un chat vechi, încărcăm acel chat
    if sesiune_aleasa != st.session_state.sesiune_curenta:
        st.session_state.sesiune_curenta = sesiune_aleasa
        st.rerun()

    # Sincronizăm mesajele afișate cu sesiunea curentă selectată
    st.session_state.mesaje = st.session_state.toate_conversatiile[st.session_state.sesiune_curenta]

    # ==========================================
    # LOGICA AI ȘI AFIȘAREA (STÂNGA/DREAPTA)
    # ==========================================
    text_context = citeste_text_din_folder(user_path)
    
    context_profil = ""
    if profil_curent.get("nume") or profil_curent.get("caen"):
        context_profil = f"DATE COMPANIE: {profil_curent}. Ține cont de ele."

    context_system = f"Ești Senior Business Analyst pe departamentul {departament}. Răspuns tip Rezumat Executiv cursiv. {context_profil} DATE DATA ROOM: {text_context}"

    col_chat, col_istoric = st.columns([3, 1])

    with col_istoric:
        st.subheader("📊 Status Sesiune")
        st.info(f"Sesiune activă: {st.session_state.sesiune_curenta}")
        st.caption(f"Memoria reține {len(st.session_state.mesaje)} mesaje pentru context.")
        
        if st.button("🧹 Curăță chatul curent", use_container_width=True):
            st.session_state.toate_conversatiile[st.session_state.sesiune_curenta] = []
            salveaza_conversatii(st.session_state.utilizator_curent, st.session_state.toate_conversatiile)
            st.rerun()

    with col_chat:
        for m in st.session_state.mesaje:
            with st.chat_message(m["rol"]):
                st.markdown(m["continut"])

        if intrebare := st.chat_input("Adresați o întrebare despre documente..."):
            # Salvăm mesajul utilizatorului
            st.session_state.toate_conversatiile[st.session_state.sesiune_curenta].append({"rol": "user", "continut": intrebare})
            with st.chat_message("user"):
                st.markdown(intrebare)

            mesaje_api = [{"role": "system", "content": context_system}]
            for m in st.session_state.toate_conversatiile[st.session_state.sesiune_curenta]:
                mesaje_api.append({"role": m["rol"], "content": m["continut"]})

            with st.chat_message("assistant"):
                stream = client.chat.completions.create(
                    model="gpt-4-turbo", 
                    messages=mesaje_api,
                    stream=True
                )
                raspuns = st.write_stream(stream)
            
            # Salvăm răspunsul AI-ului
            st.session_state.toate_conversatiile[st.session_state.sesiune_curenta].append({"rol": "assistant", "continut": raspuns})
            salveaza_conversatii(st.session_state.utilizator_curent, st.session_state.toate_conversatiile)
