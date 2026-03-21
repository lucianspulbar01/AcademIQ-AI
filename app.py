import streamlit as st
from openai import OpenAI
import PyPDF2
import docx
import pandas as pd
from pptx import Presentation
import json
import os

# 1. Am schimbat iconița și titlul paginii
st.set_page_config(page_title="CorporateAdvisor AI", page_icon="💼", layout="wide")

# ==========================================
# FUNCȚII NOI: SALVAREA ȘI ÎNCĂRCAREA ISTORICULUI
# ==========================================
def incarca_istoric(utilizator):
    nume_fisier = f"istoric_{utilizator}.json"
    if os.path.exists(nume_fisier):
        with open(nume_fisier, "r", encoding="utf-8") as f:
            return json.load(f)
    return []

def salveaza_istoric(utilizator, mesaje):
    nume_fisier = f"istoric_{utilizator}.json"
    try:
        with open(nume_fisier, "w", encoding="utf-8") as f:
            json.dump(mesaje, f, ensure_ascii=False, indent=4)
    except Exception as e:
        st.error(f"Eroare internă de salvare: {e}")

# --- SISTEMUL DE LOGIN ---
if "logat" not in st.session_state:
    st.session_state.logat = False
    st.session_state.utilizator_curent = ""

if not st.session_state.logat:
    # Un ecran de login mult mai "business"
    st.title("🔐 Portal Securizat: CorporateAdvisor AI")
    st.write("Vă rugăm să vă autentificați pentru a accesa platforma de analiză a documentelor.")
    
    user_input = st.text_input("Nume utilizator (ID angajat):")
    pass_input = st.text_input("Parolă:", type="password")
    
    if st.button("Autentificare"):
        if user_input in st.secrets["passwords"] and st.secrets["passwords"][user_input] == pass_input:
            st.session_state.logat = True
            st.session_state.utilizator_curent = user_input
            st.rerun()
        else:
            st.error("Credențiale incorecte. Acces refuzat!")

# --- APLICAȚIA PRINCIPALĂ ---
else:
    client = OpenAI(api_key=st.secrets["openai_api_key"])

    # 2. LOCUL PENTRU LOGO
    # Dacă ai o poză numită "logo.png" pusă pe GitHub lângă cod, șterge diez-ul (#) de la linia de mai jos:
    # st.sidebar.image("logo.png", width=200)

    st.title(f"💼 CorporateAdvisor AI")
    st.markdown(f"**Utilizator curent:** {st.session_state.utilizator_curent} | Încărcați documentele pentru analiză și sinteză strategică.")

    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.session_state.mesaje = []
        st.rerun()

    # 3. Departamente Corporate în loc de Materii
    departament = st.sidebar.selectbox("Filtru Departamental:", ("Management & Strategie", "Financiar", "Juridic", "Resurse Umane", "Marketing"))
    
    # ==========================================
    # ZONA NOUĂ: MULTIPLE FIȘIERE + MULTIPLE FORMATE
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📂 Documente Sursă (Data Room)")
    
    fisiere_incarcate = st.sidebar.file_uploader(
        "Încărcați contracte, bugete, prezentări (PDF, Word, Excel etc.)", 
        type=["pdf", "docx", "xlsx", "pptx", "txt"], 
        accept_multiple_files=True
    )
    
    text_curs = ""
    if fisiere_incarcate:
        with st.spinner('Procesez documentele...'):
            for fisier in fisiere_incarcate:
                nume_fisier = fisier.name
                extensie = nume_fisier.split('.')[-1].lower()
                
                text_curs += f"\n\n--- DOCUMENT: {nume_fisier} ---\n"
                
                try:
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
                    
        st.sidebar.success(f"{len(fisiere_incarcate)} document(e) procesate. Pregătit pentru analiză.")

    # ==========================================
    # 4. NOUL CREIER CORPORATE (Prompt-ul de sistem)
    # ==========================================
    # ==========================================
    # 4. NOUL CREIER CORPORATE (Prompt-ul de sistem)
    # ==========================================
    context = f"""Ești un Senior Business Analyst și Consultant Strategic la o firmă de top (Big 4).
În prezent, ești asignat STRICT pe departamentul: **{departament}**.

REGULĂ CRITICĂ: Dacă utilizatorul îți pune o întrebare care nu are legătură cu {departament}, ci ține clar de competența altui departament (ex. te întreabă de campanii publicitare când tu ești pe Juridic, sau de clauze legale când ești pe Marketing), NU îi oferi analiza. 
Răspunde-i scurt și politicos cu un mesaj de genul: "Observ că solicitarea dvs. face referire la [domeniul identificat], care depășește aria de expertiză a departamentului {departament}. Pentru a vă oferi cea mai bună analiză, vă rog să schimbați filtrul departamental din meniul lateral pe [Departamentul Corect]."

Rolul tău este să analizezi documentele primite, să identifici riscurile, să optimizezi costurile și să oferi recomandări acționabile.
Folosește un ton profesional, clar și concis. Utilizează terminologie de business adecvată atunci când contextul o cere.
Structurează-ți mereu răspunsurile logic: folosește paragrafe scurte, bullet points pentru enumerări și pune în bold (îngroșat) metricile sau deciziile importante."""

    if departament == "Financiar":
        context += "\nAnalizezi totul din perspectivă financiară. Pune accent pe cash-flow, profitabilitate, reducere de costuri (cost-cutting) și marginile de profit."
    elif departament == "Juridic":
        context += "\nAnalizezi totul din perspectivă legală. Evaluează clauzele contractuale, liability-ul (răspunderea), conformitatea (compliance) și riscurile de litigiu."
    elif departament == "Marketing":
        context += "\nAnalizezi din perspectiva brandului și a cotei de piață. Pune accent pe target audience, CAC (Cost of Customer Acquisition) și ratele de conversie."
    elif departament == "Resurse Umane":
        context += "\nAnalizezi din perspectiva capitalului uman. Pune accent pe retenție, recrutare, evaluarea performanței și cultura organizațională."
    elif departament == "Management & Strategie":
        context += "\nAnalizezi din perspectiva conducerii (C-level). Pune accent pe scalabilitate, OKRs, direcția generală a companiei și sinergii între departamente."

    if text_curs != "":
        context += f"\n\nTe rog să răspunzi la solicitările utilizatorului bazându-te STRICT pe următoarele documente (Data Room). Dacă o informație nu se regăsește în documente, specifică clar.\n\nDATE/DOCUMENTE DISPONIBILE:\n{text_curs}" 

    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    for mesaj in st.session_state.mesaje:
        with st.chat_message(mesaj["rol"]):
            st.markdown(mesaj["continut"])

    # Input schimbat
    if intrebare := st.chat_input("Adresați o solicitare de analiză către AI..."):
        
        with st.chat_message("user"):
            st.markdown(intrebare)
        
        st.session_state.mesaje.append({"rol": "user", "continut": intrebare})
        salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)

        mesaje_api = [{"role": "system", "content": context}]
        for m in st.session_state.mesaje:
            mesaje_api.append({"role": m["rol"], "content": m["continut"]})

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-5.4", 
                messages=mesaje_api,
                stream=True
            )
            raspuns_ai = st.write_stream(stream)
        
        st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns_ai})
        salveaza_istoric(st.session_state.utilizator_curent, st.session_state.mesaje)

