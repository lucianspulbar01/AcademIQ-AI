import streamlit as st
from openai import OpenAI

# 1. Configurare
# Aici punem cheia (în mod normal se ascunde, dar pentru test e ok aici)
client = OpenAI(api_key=st.secrets["openai_api_key"])

# 2. Titlul Aplicației și Design simplu
st.set_page_config(page_title="AcademIQ AI")
st.title("🎓 AcademIQ AI")
st.write("Salut! Sunt aici să te ajut să înțelegi materia mai ușor.")

# 3. Alegerea materiei (pentru a personaliza AI-ul)
materie = st.selectbox(
    "Pentru ce materie ai nevoie de ajutor?",
    ("Drept", "Economie", "Informatică", "Medicină", "General")
)

# 4. Căsuța unde studentul scrie întrebarea
intrebare = st.text_area("Scrie întrebarea ta aici:", height=150)

# 5. Butonul care declanșează AI-ul
if st.button("Explică-mi!"):
    if not intrebare:
        st.warning("Te rog scrie o întrebare întâi.")
    else:
        # Aici definim personalitatea AI-ului în funcție de materie
        context = ""
        if materie == "Drept":
            context = "Ești un profesor expert de Drept. Citează legi relevante și folosește limbaj juridic explicat simplu."
        elif materie == "Economie":
            context = "Ești un doctor profesor. Explică anatomia și procesele biologice clar, structurat."
        elif materie == "Informatică":
            context = "Ești un inginer software senior. Oferă exemple de cod și explică algoritmii pas cu pas."
        else:
            context = "Ești un profesor universitar răbdător și clar."

        # Aici trimitem cererea către "Creier" (API)
        with st.spinner('Mă gândesc la răspuns...'):
            try:
                response = client.chat.completions.create(
                    model="gpt-3.5-turbo", # Sau "gpt-4" dacă vrei mai deștept, dar e mai scump
                    messages=[
                        {"role": "system", "content": context}, # Instrucțiunea secretă
                        {"role": "user", "content": intrebare}  # Întrebarea studentului
                    ],
                    temperature=0.7 # Creativitate (0 e robot, 1 e poet)
                )
                
                # Extragem răspunsul
                raspuns_ai = response.choices[0].message.content
                
                # Îl afișăm pe ecran
                st.success("Iată explicația:")
                st.markdown(raspuns_ai)
                
            except Exception as e:
                st.error(f"A apărut o eroare: {e}")

# 6. Footer
st.markdown("---")
st.caption("Aplicație demonstrativă creată pentru studenți.")