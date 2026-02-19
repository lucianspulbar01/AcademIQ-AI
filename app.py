import streamlit as st
from openai import OpenAI

# Aceasta trebuie să fie prima comandă mereu
st.set_page_config(page_title="Tutor AI", page_icon="🎓")

# --- SISTEMUL DE MEMORIE PENTRU LOGIN ---
# Dacă userul abia a intrat pe site, setăm că NU este logat
if "logat" not in st.session_state:
    st.session_state.logat = False
    st.session_state.utilizator_curent = ""

# ==========================================
# ECRANUL DE LOGIN (Dacă nu este logat)
# ==========================================
if not st.session_state.logat:
    st.title("🔒 Acces Restricționat")
    st.write("Te rog să te conectezi pentru a folosi Asistentul AI.")
    
    # Căsuțele de text
    user_input = st.text_input("Nume utilizator:")
    pass_input = st.text_input("Parolă:", type="password") # type="password" ascunde caracterele cu steluțe
    
    # Butonul de conectare
    if st.button("Conectare"):
        # Verificăm dacă userul există în Seiful Streamlit și dacă parola este corectă
        if user_input in st.secrets["passwords"] and st.secrets["passwords"][user_input] == pass_input:
            st.session_state.logat = True
            st.session_state.utilizator_curent = user_input
            st.rerun() # Reîncărcăm pagina ca să dispară login-ul și să apară chat-ul
        else:
            st.error("Nume de utilizator sau parolă incorectă!")

# ==========================================
# APLICAȚIA PRINCIPALĂ (Dacă ESTE logat)
# ==========================================
else:
    # Conectarea la "Creier"
    client = OpenAI(api_key=st.secrets["openai_api_key"])

    # Salutăm utilizatorul pe nume!
    st.title(f"🎓 Asistent AI")
    st.write(f"Salut, **{st.session_state.utilizator_curent}**! Cu ce te pot ajuta azi?")

    # Buton de deconectare în meniul lateral
    if st.sidebar.button("🚪 Deconectare"):
        st.session_state.logat = False
        st.session_state.mesaje = [] # Ștergem chat-ul ca să nu-l vadă următorul
        st.rerun()

    cuvant_magic = st.sidebar.selectbox(
        "Alege materia:",
        ("General", "Drept", "Medicină", "Informatică", "Economie")
    )

    context = "Ești un profesor universitar calm și răbdător."
    if cuvant_magic == "Drept":
        context = "Ești un profesor expert de Drept. Citează legi relevante și explică clar."
    elif cuvant_magic == "Medicină":
        context = "Ești un doctor profesor. Explică anatomia clar și structurat."

    if "mesaje" not in st.session_state:
        st.session_state.mesaje = []

    for mesaj in st.session_state.mesaje:
        with st.chat_message(mesaj["rol"]):
            st.markdown(mesaj["continut"])

    if intrebare := st.chat_input("Scrie un mesaj aici..."):
        with st.chat_message("user"):
            st.markdown(intrebare)
        
        st.session_state.mesaje.append({"rol": "user", "continut": intrebare})

        mesaje_api = [{"role": "system", "content": context}]
        for m in st.session_state.mesaje:
            mesaje_api.append({"role": m["rol"], "content": m["continut"]})

        with st.chat_message("assistant"):
            stream = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=mesaje_api,
                stream=True
            )
            raspuns_ai = st.write_stream(stream)
        
        st.session_state.mesaje.append({"rol": "assistant", "continut": raspuns_ai})
