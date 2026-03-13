import io
from typing import List, Tuple

from fastapi import Depends, HTTPException, UploadFile
from pypdf import PdfReader
from sqlalchemy.orm import Session

from data.database import get_db
from features.base_handler import BaseHandler
from infrastructure.dtos.document.upload_result import DocumentUploadResult
from infrastructure.services.rag_service import RagService

ALLOWED_TYPES = {
    "application/pdf": "pdf",
    "text/plain": "txt",
    "text/markdown": "md",
    "text/x-markdown": "md",
}

MAX_FILE_SIZE_MB = 20


class UploadDocument(BaseHandler[UploadFile, DocumentUploadResult]):
    def __init__(self, db: Session = Depends(get_db), rag_service: RagService = Depends()):
        self.db = db
        self.rag_service = rag_service

    async def execute(self, request: UploadFile) -> DocumentUploadResult:
        file_type = self._validate_file(request)
        content = await request.read()

        self._validate_size(content)

        text_by_page = self._extract_text(content, file_type)
        document = self.rag_service.process_and_save_document(
            text_by_page=text_by_page,
            filename=request.filename,
            file_type=file_type,
            db=self.db,
        )

        return DocumentUploadResult(
            id=str(document.id),
            name=document.name,
            file_type=document.file_type,
            total_chunks=len(document.chunks),
        )

    def _validate_file(self, file: UploadFile) -> str:
        content_type = file.content_type or ""
        file_type = ALLOWED_TYPES.get(content_type)

        # Fallback para extensão do arquivo quando o content_type não é detectado corretamente
        if not file_type and file.filename:
            ext = file.filename.rsplit(".", 1)[-1].lower()
            if ext in ("txt", "md"):
                file_type = ext
            elif ext == "pdf":
                file_type = "pdf"

        if not file_type:
            raise HTTPException(
                status_code=400,
                detail="Tipo de arquivo não permitido. Envie arquivos PDF, TXT ou Markdown (.md).",
            )
        return file_type

    def _validate_size(self, content: bytes) -> None:
        size_mb = len(content) / (1024 * 1024)
        if size_mb > MAX_FILE_SIZE_MB:
            raise HTTPException(
                status_code=400,
                detail=f"Arquivo muito grande. Tamanho máximo permitido: {MAX_FILE_SIZE_MB} MB.",
            )

    def _extract_text(self, content: bytes, file_type: str) -> List[Tuple[int | None, str]]:
        if file_type == "pdf":
            return self._extract_pdf(content)
        return self._extract_text_file(content)

    def _extract_pdf(self, content: bytes) -> List[Tuple[int, str]]:
        reader = PdfReader(io.BytesIO(content))
        pages = []
        for page_num, page in enumerate(reader.pages, start=1):
            text = page.extract_text() or ""
            pages.append((page_num, text))
        return pages

    def _extract_text_file(self, content: bytes) -> List[Tuple[None, str]]:
        text = content.decode("utf-8", errors="replace")
        return [(None, text)]
