import streamlit as st
from openai import OpenAI
import PyPDF2 # Unealta nouă pentru PDF-uri
import docx # Pentru Word
import pandas as pd # Pentru Excel
from pptx import Presentation # Pentru PowerPoint
import json # Unealta nouă pentru salvarea chaturilor
import os   # Unealta nouă pentru a verifica dacă dosarul există

st.set_page_config(page_title="CorporateAdvisor AI", page_icon="🎓")

# ==========================================
# FUNCȚII NOI: SALVAREA ȘI ÎNCĂRCAREA ISTORICULUI
# ==========================================
def incarca_istoric(utilizator):
    """Caută dosarul utilizatorului și citește mesajele trecute."""
    nume_fisier = f"istoric_{utilizator}.json"
    if os.path.exists(nume_fisier):
        with open(nume_fisier, "r", encoding="utf-8") as f:
            return json.load(f)
    return [] # Dacă nu are istoric, returnăm o listă goală

def salveaza_istoric(utilizator, mesaje):
    """Scrie mesajele noi în dosarul utilizatorului."""
    nume_fisier = f"istoric_{utilizator}.json"
    try:
        with open(nume_fisier, "w", encoding="utf-8") as f:
            json.dump(mesaje, f, ensure_ascii=False, indent=4)
    except Exception as e:
        # Dacă serverul blochează salvarea, ne va da un mesaj roșu de eroare
        st.error(f"Eroare la salvarea memoriei: {e}")

# --- SISTEMUL DE LOGIN ---
if "logat" not in st.session_state:
    st.session_state.logat = False
    st.session_state.utilizator_curent = ""

if not st.session_state.logat:
    st.title("🔒 Acces Restricționat")
    user_input = st.text_input("Nume utilizator:")
    pass_input = st.text_input("Parolă:", type="password")
    
    if st.button("Conectare"):
        if user_input in st.secrets["passwords"] and st.secrets["passwords"][user_input] == pass_input:
            st.session_state.logat = True
            st.session_state.utilizator_curent = user_input
            st.rerun()
        else:
            st.error("Nume sau parolă incorectă!")

# --- APLICAȚIA PRINCIPALĂ ---
else:
    client = OpenAI(api_key=st.secrets["openai_api_key"])

    st.title(f"🎓 AcademIQ AI")
    st.write(f"Salut, **{st.session_state.utilizator_curent}**! Încarcă un curs și hai să învățăm.")

    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.session_state.mesaje = []
        st.rerun()

    cuvant_magic = st.sidebar.selectbox("Alege materia:", ("Financiar", "Juridic", "Resurse Umane", "Marketing"))
  # ==========================================
    # ZONA NOUĂ: MULTIPLE FIȘIERE + MULTIPLE FORMATE
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Baza de cunoștințe")
    
    # 1. Am adăugat accept_multiple_files=True și am listat toate formatele!
    fisiere_incarcate = st.sidebar.file_uploader(
        "Încarcă cursuri, seminarii etc.", 
        type=["pdf", "docx", "xlsx", "pptx", "txt"], 
        accept_multiple_files=True
    )
    
    text_curs = ""
    if fisiere_incarcate:
        with st.spinner('Citesc documentele...'):
            # 2. Luăm fiecare fișier la rând
            for fisier in fisiere_incarcate:
                nume_fisier = fisier.name
                extensie = nume_fisier.split('.')[-1].lower()
                
                # Punem un titlu invizibil pentru AI ca să știe din ce document citește
                text_curs += f"\n\n--- DOCUMENT: {nume_fisier} ---\n"
                
                try:
                    # 3. Deschidem cu cheia potrivită în funcție de format
                    if extensie == "pdf":
                        pdf_reader = PyPDF2.PdfReader(fisier)
                        for pagina in pdf_reader.pages:
                            text_curs += pagina.extract_text() + "\n"
                            
                    elif extensie == "docx":
                        doc = docx.Document(fisier)
                        for paragraf in doc.paragraphs:
                            text_curs += paragraf.text + "\n"
                            
                    elif extensie == "xlsx":
                        df = pd.read_excel(fisier)
                        text_curs += df.to_string() + "\n"
                        
                    elif extensie == "pptx":
                        prezentare = Presentation(fisier)
                        for slide in prezentare.slides:
                            for forma in slide.shapes:
                                if hasattr(forma, "text"):
                                    text_curs += forma.text + "\n"
                                    
                    elif extensie == "txt":
                        text_curs += fisier.getvalue().decode("utf-8") + "\n"
                        
                except Exception as e:
                    st.sidebar.error(f"Eroare la citirea {nume_fisier}: {e}")
                    
        st.sidebar.success(f"{len(fisiere_incarcate)} document(e) citite cu succes!")

    # ==========================================

    # Construim contextul (Aici e modelul vechi de limită, poți să-l lași fără [:] dacă folosești GPT-5)
    context = "Ești un analist de business de top la o firmă de consultanță globală. Rolul tău este să analizezi documentele primite, să identifici riscurile, să optimizezi costurile și să oferi recomandări strategice clare, bazate strict pe datele din fișiere, argumentând logic fiecare propunere."
    if cuvant_magic == "Consultanta":
        context = "Ești un expert in consultanta corporativă."
    
    if text_curs != "":
        context += f"\n\nTe rog să răspunzi la întrebările studentului bazându-te STRICT pe următoarele materiale. Dacă răspunsul nu se află în ele, spune clar.\n\nMATERIALE:\n{text_curs}" 

    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    for mesaj in st.session_state.mesaje:
        with st.chat_message(mesaj["rol"]):
            st.markdown(mesaj["continut"])

    # Când utilizatorul scrie o întrebare nouă
    if intrebare := st.chat_input("Scrie o întrebare din cursuri..."):
        
        # 1. O afișăm pe ecran
        with st.chat_message("user"):
            st.markdown(intrebare)
        
        # 2. O adăugăm în memoria scurtă
        st.session_state.mesaje.append({"rol": "user", "continut": intrebare})
        
        # 3. O SALVĂM ÎN DOSAR (Memoria lungă)
        salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)

        # Pregătim mesajul pentru API
        mesaje_api = [{"role": "system", "content": context}]
        for m in st.session_state.mesaje:
            mesaje_api.append({"role": m["rol"], "content": m["continut"]})

        # Primim răspunsul
        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-5.2", # Sau gpt-4o / gpt-3.5-turbo în funcție de ce ai lăsat
                messages=mesaje_api,
                stream=True
            )
            raspuns_ai = st.write_stream(stream)
        
        # Salvăm și răspunsul AI-ului în memoria scurtă și lungă!
        st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns_ai})
        salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)











