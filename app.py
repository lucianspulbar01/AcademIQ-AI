import streamlit as st
from openai import OpenAI

# 1. Configurare
# Aici punem cheia (în mod normal se ascunde, dar pentru test e ok aici)
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 2. Titlul Aplicației și Design simplu
st.set_page_config(page_title="AcademIQ AI")
st.title("🎓 Alex Vocea României AI")
st.write("Salut! Cu ce te pot ajuta astăzi.")

# Alegerea materiei o punem într-o bară laterală (Sidebar) ca să arate mai bine
cuvant_magic = st.sidebar.selectbox(
    "Alege materia pentru azi:",
    ("General", "Economie", "Drept", "Informatică", "Medicină")
)

# Definim personalitatea în funcție de materie
context = "Ești un profesor universitar calm și răbdător."
if cuvant_magic == "Drept":
    context = "Ești un profesor expert de Drept. Citează legi relevante și explică clar."
elif cuvant_magic == "Medicină":
    context = "Ești un doctor profesor. Explică anatomia clar și structurat."

# 2. Inițializarea "Memoriei" (Session State)
# Dacă nu există o listă de mesaje în memorie, o creăm acum
if "mesaje" not in st.session_state:
    st.session_state.mesaje = []

# 3. Afișarea istoricului de mesaje pe ecran
for mesaj in st.session_state.mesaje:
    with st.chat_message(mesaj["rol"]): # "rol" poate fi "user" sau "assistant"
        st.markdown(mesaj["continut"])

# 4. Bara de chat de jos (unde scrie studentul)
if intrebare := st.chat_input("Scrie un mesaj aici..."):
    
    # a. Afișăm pe ecran ce a scris studentul
    with st.chat_message("user"):
        st.markdown(intrebare)
    
    # b. Salvăm întrebarea în memoria aplicației
    st.session_state.mesaje.append({"rol": "user", "continut": intrebare})

    # c. Pregătim istoricul complet pentru API-ul OpenAI (ca să nu uite despre ce vorbeați)
    # Punem instrucțiunea profesorului prima, apoi tot istoricul
    mesaje_api = [{"role": "system", "content": context}]
    for m in st.session_state.mesaje:
        mesaje_api.append({"role": m["rol"], "content": m["continut"]})

    # d. Cerem răspunsul de la AI și îl afișăm cu un efect frumos de "scriere în timp real" (Stream)
    with st.chat_message("assistant"):
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=mesaje_api,
            stream=True # Acest parametru face ca textul să apară cuvânt cu cuvânt!
        )
        raspuns_ai = st.write_stream(stream)
    
    # e. Salvăm răspunsul AI-ului în memorie
    st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns_ai})

# 6. Footer
st.markdown("---")

st.caption("Aplicație creată pentru studenți.")


