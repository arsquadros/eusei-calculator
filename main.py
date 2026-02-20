import streamlit as st

st.set_page_config(page_title="EuSEI - Home", page_icon="⚖️", layout="centered")

def main() -> None:
    """
    Configura a Landing Page para entrada em salas de estimativa.
    """
    st.title("⚖️ EuSEI: Entity-user Synthetic Engineering Index")
    st.markdown("""
    Bem-vindo ao sistema de estimativa técnica para times de engenharia. 
    Insira os detalhes abaixo para entrar em uma sala de discussão.
    """)

    with st.container(border=True):
        room_id: str = st.text_input("🆔 ID da Sala", placeholder="Ex: squad-alpha-sprint-42")
        user_name: str = st.text_input("👤 Seu Nome", placeholder="Ex: Dev João")
        
        if st.button("Entrar na Sala 🚀", use_container_width=True):
            if room_id and user_name:
                # Persistência de estado para troca de página
                st.session_state["room_id"] = room_id.strip().replace(" ", "_")
                st.session_state["user_name"] = user_name.strip()
                
                st.switch_page("pages/room.py")
            else:
                st.error("Por favor, preencha todos os campos para prosseguir.")

if __name__ == "__main__":
    main()