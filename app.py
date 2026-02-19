import streamlit as st
from openai import OpenAI
import PyPDF2 # Unealta nouă pentru PDF-uri

st.set_page_config(page_title="AcademIQ AI", page_icon="🎓")

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

    cuvant_magic = st.sidebar.selectbox("Alege materia:", ("General", "Economie", "Drept", "Informatică", "Medicină"))

    # ==========================================
    # ZONA NOUĂ: Încărcarea și citirea PDF-ului
    # ==========================================
    st.sidebar.markdown("---")
    st.sidebar.subheader("📚 Baza de cunoștințe")
    fisier_pdf = st.sidebar.file_uploader("Încarcă un curs (PDF)", type="pdf")
    
    text_curs = ""
    if fisier_pdf is not None:
        # Dacă studentul a pus un fișier, extragem textul din el
        pdf_reader = PyPDF2.PdfReader(fisier_pdf)
        for pagina in pdf_reader.pages:
            text_curs += pagina.extract_text() + "\n"
        st.sidebar.success("Curs încărcat și citit cu succes!")

    # ==========================================

    # Construim contextul (Instrucțiunile secrete)
    context = "Ești un profesor universitar calm și răbdător."
    if cuvant_magic == "Drept":
        context = "Ești un profesor expert de Drept."
    
    # Dacă avem text din PDF, îi spunem AI-ului să îl folosească
    if text_curs != "":
        context += f"\n\nTe rog să răspunzi la întrebările studentului bazându-te STRICT pe următoarele notițe de curs. Dacă răspunsul nu se află în curs, spune-i asta clar. \n\nNOTIȚE CURS:\n{text_curs[:15000]}" 
        # Am pus o limită la primele ~15.000 de caractere ca să nu blocăm memoria AI-ului.

    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    for mesaj in st.session_state.mesaje:
        with st.chat_message(mesaj["rol"]):
            st.markdown(mesaj["continut"])

    if intrebare := st.chat_input("Scrie o întrebare din curs..."):
        with st.chat_message("user"):
            st.markdown(intrebare)
        
        st.session_state.mesaje.append({"rol": "user", "continut": intrebare})

        mesaje_api = [{"role": "system", "content": context}]
        for m in st.session_state.mesaje:
            mesaje_api.append({"role": m["rol"], "content": m["continut"]})

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-5.2",
                messages=mesaje_api,
                stream=True
            )
            raspuns_ai = st.write_stream(stream)
        
        st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns_ai})


