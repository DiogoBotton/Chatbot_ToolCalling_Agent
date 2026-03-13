import json
from typing import List, Tuple

from langchain_openai import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter
from sqlalchemy.orm import Session

from domains.document import Document
from domains.document_chunk import DocumentChunk, EMBEDDING_DIMENSIONS

CHUNK_SIZE = 1000
CHUNK_OVERLAP = 200
TOP_K_RESULTS = 4


class RagService:
    def __init__(self):
        self.embeddings = OpenAIEmbeddings(model="text-embedding-3-small", dimensions=EMBEDDING_DIMENSIONS)
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=CHUNK_SIZE,
            chunk_overlap=CHUNK_OVERLAP,
        )

    def embed_text(self, text: str) -> List[float]:
        return self.embeddings.embed_query(text)

    def process_and_save_document(
        self,
        text_by_page: List[Tuple[int | None, str]],
        filename: str,
        file_type: str,
        db: Session,
    ) -> Document:
        """
        Processa um documento, divide em chunks, gera embeddings e salva no banco.
        text_by_page: lista de tuplas (page_number, text).
        """
        document = Document(name=filename, file_type=file_type)
        db.add(document)
        db.flush()  # Garante o ID antes do commit

        chunk_index = 0
        for page_number, page_text in text_by_page:
            if not page_text.strip():
                continue

            chunks = self.text_splitter.split_text(page_text)
            for chunk_text in chunks:
                chunk = DocumentChunk(
                    content=chunk_text,
                    chunk_index=chunk_index,
                    document_id=document.id,
                    page_number=page_number,
                )
                chunk.embedding = self.embed_text(chunk_text)
                db.add(chunk)
                chunk_index += 1

        db.commit()
        db.refresh(document)
        return document

    def search(self, query: str, db: Session, top_k: int = TOP_K_RESULTS) -> str:
        """
        Busca os chunks mais similares à query usando distância cosseno do PGVector.
        Retorna um JSON com o contexto formatado e a lista de fontes.
        """
        query_embedding = self.embed_text(query)

        results: List[DocumentChunk] = (
            db.query(DocumentChunk)
            .order_by(DocumentChunk.embedding.cosine_distance(query_embedding))
            .limit(top_k)
            .all()
        )

        if not results:
            return json.dumps(
                {"context": "Nenhum documento relevante encontrado.", "sources": []},
                ensure_ascii=False,
            )

        context_parts = []
        sources = []

        for chunk in results:
            label = (
                f"[Fonte: {chunk.document.name}"
                + (f", Página {chunk.page_number}" if chunk.page_number is not None else "")
                + "]"
            )
            context_parts.append(f"{label}\n{chunk.content}")

            source_entry = {
                "document": chunk.document.name,
                "page": chunk.page_number,
                "chunk_index": chunk.chunk_index,
                "content": chunk.content,
            }
            if source_entry not in sources:
                sources.append(source_entry)

        return json.dumps(
            {"context": "\n\n---\n\n".join(context_parts), "sources": sources},
            ensure_ascii=False,
        )
