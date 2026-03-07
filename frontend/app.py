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


def ensure_conversation_id() -> str:
    if st.session_state.conversation_id is not None:
        return st.session_state.conversation_id

    response = requests.post(f"{API_URL}/conversations/", json={})
    response.raise_for_status()
    conversation_id = response.json()["id"]
    st.session_state.conversation_id = conversation_id
    return conversation_id
    
def stream_chat_response(user_query: str, placeholder) -> str:
    conversation_id = ensure_conversation_id()

    payload = {
        "input": user_query,
        "conversation_id": conversation_id,
    }

    full_response = ""
    with requests.post(f"{API_URL}/chat/stream", json=payload, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue
            full_response += chunk
            placeholder.write(full_response)

    return full_response

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
        placeholder = st.empty()
        with st.spinner("Gerando resposta..."):
            ai_response = stream_chat_response(user_query, placeholder)
        add_message(ai_response, MessageType.ASSISTANT.value)
