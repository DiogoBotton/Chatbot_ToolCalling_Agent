from langchain.tools import tool

from data.database import SessionLocal
from infrastructure.services.rag_service import RagService

_rag_service = RagService()


@tool
def search_documents_tool(query: str) -> str:
    """
    Busca informações relevantes nos documentos enviados pelos usuários.
    Use esta ferramenta quando a pergunta exigir informações específicas que podem estar
    em documentos como manuais, guias, políticas, contratos ou outros arquivos enviados.
    Não use esta ferramenta para ações de criação, consulta ou atualização de processos de visto.
    Retorna trechos dos documentos mais relevantes junto com suas fontes de origem.
    """
    db = SessionLocal()
    try:
        return _rag_service.search(query, db)
    finally:
        db.close()
