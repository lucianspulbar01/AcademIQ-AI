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

    # 3. Meniul de Departamente extins
    departament = st.sidebar.selectbox(
        "Filtru Departamental:", 
        (
            "Management & Strategie", 
            "Financiar", 
            "Juridic", 
            "Resurse Umane", 
            "Marketing",
            "Vânzări", 
            "Operațiuni & Logistică", 
            "IT & Securitate"
        )
    )
    

    # ==========================================
    # 4. NOUL CREIER CORPORATE (Prompt-ul de sistem)
    # ==========================================
    context = f"""Ești un Senior Business Analyst și Consultant Strategic la o firmă de top.
În prezent, ești asignat STRICT pe departamentul: **{departament}**.

REGULĂ CRITICĂ: Dacă utilizatorul îți pune o întrebare care nu are legătură cu {departament}, nu îi oferi analiza. Spune-i politicos să schimbe filtrul departamental din meniul lateral.

REGULĂ DE FORMATARE: Răspunde SCURT, concis și direct la obiect. Folosește EXCLUSIV text cursiv (paragrafe legate). ESTE STRICT INTERZISĂ folosirea listelor cu liniuțe (bullet points) sau a enumerărilor. Formulează răspunsul ca un rezumat executiv (Executive Summary) de maxim 3-4 paragrafe.

Rolul tău este să analizezi documentele primite și să oferi recomandări de business clare, folosind un ton profesional."""

    # Setările specifice pentru fiecare departament (inclusiv cele noi)
    if departament == "Financiar":
        context += "\nAnalizezi totul din perspectivă financiară (cash-flow, profitabilitate, costuri, ROI)."
    elif departament == "Juridic":
        context += "\nAnalizezi totul din perspectivă legală (clauze, riscuri de litigiu, liability, compliance)."
    elif departament == "Marketing":
        context += "\nAnalizezi din perspectiva brandului și a cotei de piață (conversii, audiență, CAC, campanii)."
    elif departament == "Resurse Umane":
        context += "\nAnalizezi din perspectiva capitalului uman (retenție, recrutare, cultură organizațională, performanță)."
    elif departament == "Management & Strategie":
        context += "\nAnalizezi din perspectiva conducerii (scalabilitate, OKRs, direcție generală, achiziții, viziune pe termen lung)."
    elif departament == "Vânzări":
        context += "\nAnalizezi din perspectiva generării de venituri (pipeline, strategii de negociere, conversia lead-urilor, retenția clienților B2B/B2C)."
    elif departament == "Operațiuni & Logistică":
        context += "\nAnalizezi din perspectiva eficienței (supply chain, fluxuri de procese, managementul stocurilor, optimizarea timpilor de livrare)."
    elif departament == "IT & Securitate":
        context += "\nAnalizezi din perspectiva tehnologică (arhitectură de sistem, audituri de securitate cibernetică, protecția datelor/GDPR, infrastructură cloud)."

    if text_curs != "":
        context += f"\n\nTe rog să răspunzi la solicitările utilizatorului bazându-te STRICT pe următoarele documente. Dacă informația lipsește, spune clar asta.\n\nDATE DISPONIBILE:\n{text_curs}"
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

