import json

import requests
import streamlit as st

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

# ---------------------------------------------------------------------------
# Sidebar — Upload e listagem de documentos
# ---------------------------------------------------------------------------
with st.sidebar:
    st.header("📂 Documentos")
    st.caption("Envie arquivos PDF, TXT ou Markdown para o assistente consultar.")

    uploaded_file = st.file_uploader(
        "Selecione um arquivo",
        type=["pdf", "txt", "md"],
        label_visibility="collapsed",
    )

    if uploaded_file is not None:
        if st.button("Enviar documento", use_container_width=True):
            with st.spinner("Processando documento..."):
                try:
                    response = requests.post(
                        f"{API_URL}/documents/upload",
                        files={"file": (uploaded_file.name, uploaded_file.getvalue(), uploaded_file.type)},
                    )
                    response.raise_for_status()
                    result = response.json()
                    st.success(
                        f"✅ **{result['name']}** enviado com sucesso!\n\n"
                        f"Tipo: `{result['file_type']}` · {result['total_chunks']} chunk(s) indexado(s)."
                    )
                    st.rerun()
                except requests.HTTPError as e:
                    detail = e.response.json().get("detail", str(e))
                    st.error(f"Erro ao enviar: {detail}")
                except Exception as e:
                    st.error(f"Erro inesperado: {e}")

    st.divider()
    st.subheader("Documentos indexados")

    try:
        docs_response = requests.get(f"{API_URL}/documents/")
        docs_response.raise_for_status()
        documents = docs_response.json()
    except Exception:
        documents = []

    if not documents:
        st.caption("Nenhum documento enviado ainda.")
    else:
        for doc in documents:
            col_name, col_btn = st.columns([5, 1])
            ext_icon = {"pdf": "📄", "txt": "📝", "md": "📋"}.get(doc["file_type"], "📎")
            col_name.markdown(f"{ext_icon} {doc['name']}")
            if col_btn.button("✕", key=f"del_{doc['id']}", help="Excluir documento"):
                try:
                    del_response = requests.delete(f"{API_URL}/documents/{doc['id']}")
                    del_response.raise_for_status()
                    st.rerun()
                except requests.HTTPError as e:
                    st.error(f"Erro ao excluir: {e}")

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

SOURCE_MARKER = "__SOURCES__:"


def ensure_conversation_id() -> str:
    if st.session_state.conversation_id is not None:
        return st.session_state.conversation_id

    response = requests.post(f"{API_URL}/conversations/", json={})
    response.raise_for_status()
    conversation_id = response.json()["id"]
    st.session_state.conversation_id = conversation_id
    return conversation_id


def stream_chat_response(user_query: str, placeholder) -> tuple[str, list]:
    """
    Faz o streaming da resposta e retorna (conteúdo, lista_de_fontes).
    As fontes chegam ao final do stream como um marcador JSON especial.
    """
    conversation_id = ensure_conversation_id()
    payload = {"input": user_query, "conversation_id": conversation_id}

    full_response = ""
    sources = []
    buffer = ""  # acumula o final do stream para detectar o marcador

    with requests.post(f"{API_URL}/chat/stream", json=payload, stream=True) as response:
        response.raise_for_status()
        for chunk in response.iter_content(chunk_size=None, decode_unicode=True):
            if not chunk:
                continue

            buffer += chunk

            # Verifica se o marcador de fontes já chegou no buffer
            if SOURCE_MARKER in buffer:
                content_part, sources_part = buffer.split(SOURCE_MARKER, 1)
                full_response += content_part
                try:
                    sources = json.loads(sources_part)
                except json.JSONDecodeError:
                    pass
                buffer = ""
                placeholder.write(full_response)
                break  # marcador de fontes é sempre o último elemento

            # Se o buffer está crescendo sem o marcador, exibe o que estiver seguro
            # (mantém os últimos bytes reservados para possível início do marcador)
            safe_boundary = len(buffer) - len(SOURCE_MARKER)
            if safe_boundary > 0:
                safe_chunk = buffer[:safe_boundary]
                full_response += safe_chunk
                buffer = buffer[safe_boundary:]
                placeholder.write(full_response)

        # Garante que qualquer resto do buffer (sem marcador) seja exibido
        if buffer:
            full_response += buffer
            placeholder.write(full_response)

    return full_response, sources


def add_message(message: str, message_type: MessageType, sources: list = None):
    st.session_state.messages.append({
        "type": message_type,
        "message": message,
        "sources": sources or [],
    })


def render_sources(sources: list):
    if not sources:
        return
    with st.expander("📚 Fontes utilizadas"):
        for i, source in enumerate(sources):
            doc = source.get("document", "Desconhecido")
            page = source.get("page")
            chunk = source.get("chunk_index")
            content = source.get("content", "")

            header = f"**{doc}**"
            if page is not None:
                header += f" — Página {page}"
            if chunk is not None:
                header += f" (chunk {chunk})"

            st.markdown(header)
            if content:
                st.caption(content)
            if i < len(sources) - 1:
                st.divider()


# ---------------------------------------------------------------------------
# Renderiza histórico de mensagens
# ---------------------------------------------------------------------------
for message in st.session_state.messages:
    if message["type"] == "assistant":
        with st.chat_message("ai"):
            st.write(message["message"])
            render_sources(message.get("sources", []))
    elif message["type"] == "user":
        with st.chat_message("human"):
            st.write(message["message"])

# ---------------------------------------------------------------------------
# Input do usuário
# ---------------------------------------------------------------------------
user_query = st.chat_input("Digite sua mensagem aqui...")

if user_query:
    # Renderiza imediatamente a mensagem do usuário (UX melhor)
    with st.chat_message("human"):
        st.write(user_query)
        add_message(user_query, MessageType.USER.value)

    with st.chat_message("ai"):
        placeholder = st.empty()
        with st.spinner("Gerando resposta..."):
            ai_response, sources = stream_chat_response(user_query, placeholder)
        render_sources(sources)
        add_message(ai_response, MessageType.ASSISTANT.value, sources)

