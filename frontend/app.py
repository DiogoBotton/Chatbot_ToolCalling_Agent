import streamlit as st
import requests
from enums import MessageType
import os

API_URL = os.getenv("API_URL", "http://localhost:8000")

# Configurações
st.set_page_config(page_title="Seu assistente virtual 🤖", page_icon="🤖")
st.title("Seu assistente virtual 🤖")

if "conversation_id" not in st.session_state:
    st.session_state.conversation_id = None

if "messages" not in st.session_state:
    st.session_state.messages = []
    
def send_message(user_query: str):
    payload = {
        "input": user_query,
        "conversation_id": st.session_state.conversation_id
    }

    response = requests.post(f"{API_URL}/chat", json=payload)
    response.raise_for_status()

    data = response.json()

    # Atualiza conversation_id se for nova
    st.session_state.conversation_id = data["conversation_id"]
    
    return data["response"]

def add_message(message: str, message_type: MessageType):
    st.session_state.messages.append({
        "type": message_type,
        "message": message
    })

for message in st.session_state.messages:
    if message["type"] == "assistant":
        with st.chat_message("ai"):
            st.write(message["message"])
    elif message["type"] == "user":
        with st.chat_message("human"):
            st.write(message["message"])

user_query = st.chat_input("Digite sua mensagem aqui...")

if user_query:
    # Renderiza imediatamente a mensagem do usuário (UX melhor)
    with st.chat_message("human"):
        st.write(user_query)
        add_message(user_query, MessageType.USER.value)

    with st.chat_message("ai"):
        with st.spinner("Gerando resposta..."):
            ai_response = send_message(user_query)
        st.write(ai_response)
        add_message(ai_response, MessageType.ASSISTANT.value)
