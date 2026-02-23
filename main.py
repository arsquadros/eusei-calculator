import streamlit as st

from google.cloud import firestore
from google.oauth2 import service_account

from dotenv import load_dotenv
load_dotenv()

st.set_page_config(page_title="EuSEI - Home", page_icon="⚖️", layout="centered")

# Função auxiliar para o Firestore (mesma lógica do tmp.py)
def get_db_client():
    if "db" not in st.session_state:
        creds_info = st.secrets["firestore"]
        creds = service_account.Credentials.from_service_account_info(creds_info)
        st.session_state["db"] = firestore.Client(credentials=creds)
    return st.session_state["db"]

def main() -> None:
    st.title("⚖️ EuSEI: Entity-user Synthetic Engineering Index")
    st.markdown("""
    Bem-vindo ao sistema de estimativa técnica para times de engenharia. 
    Insira os detalhes abaixo para entrar em uma sala de discussão.
    """)

    db = get_db_client()

    with st.container(border=True):
        room_id_input: str = st.text_input("🆔 ID da Sala", placeholder="Ex: squad-alpha-sprint-42")
        user_name_input: str = st.text_input("👤 Seu Nome", placeholder="Ex: Dev João")
        
        if st.button("Entrar na Sala 🚀", use_container_width=True):
            if room_id_input and user_name_input:
                room_id = room_id_input.strip().replace(" ", "_")
                user_name = user_name_input.strip()
                
                collection_name = f"{st.secrets['firestore']['collection_name']}-{st.secrets['firestore']['environment']}"

                # Referências
                room_ref = db.collection(collection_name).document(room_id)
                user_ref = room_ref.collection("users").document(user_name)
                
                # Lógica de definição de Owner:
                # Se a subcoleção de usuários estiver vazia, este usuário é o owner.
                users_exists = list(room_ref.collection("users").limit(1).stream())
                user_type = "owner" if not users_exists else "squad"
                
                room_ref = db.collection(collection_name).document(room_id)
    
                # Inicializa a sala com uma tarefa padrão se ela não existir
                room_doc = room_ref.get()
                if not room_doc.exists:
                    room_ref.set({
                        "current_task_id": "task_1",
                        "created_at": firestore.SERVER_TIMESTAMP
                    })

                # Salva o usuário no banco
                user_ref.set({
                    "user_type": user_type
                })
                
                # Persistência de estado local
                st.session_state["room_id"] = room_id
                st.session_state["user_name"] = user_name
                st.session_state["user_type"] = user_type
                
                st.switch_page("pages/room.py")
            else:
                st.error("Por favor, preencha todos os campos para prosseguir.")

if __name__ == "__main__":
    main()