import json
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
    
def stream_chat_response(user_query: str, response_placeholder, reasoning_placeholder) -> str:
    conversation_id = ensure_conversation_id()

    payload = {
        "input": user_query,
        "conversation_id": conversation_id,
    }

    full_reasoning = ""
    full_response = ""

    with requests.post(f"{API_URL}/chat/stream", json=payload, stream=True) as response:
        response.raise_for_status()
        for line in response.iter_lines(decode_unicode=True):
            if not line:
                continue
            data = json.loads(line)
            if data["type"] == "reasoning":
                full_reasoning += data["content"]
                reasoning_placeholder.expander("🧠 Raciocínio do modelo", expanded=True).markdown(full_reasoning)
            elif data["type"] == "text":
                full_response += data["content"]
                response_placeholder.write(full_response)

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
        reasoning_placeholder = st.empty()
        response_placeholder = st.empty()
        with st.spinner("Gerando resposta..."):
            ai_response = stream_chat_response(user_query, response_placeholder, reasoning_placeholder)
        add_message(ai_response, MessageType.ASSISTANT.value)
