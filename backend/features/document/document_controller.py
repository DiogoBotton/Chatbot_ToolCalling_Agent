from typing import List
from uuid import UUID

from fastapi import APIRouter, Depends, File, Response, UploadFile

from features.document.methods import delete, list, upload
from infrastructure.dtos.document.document_result import DocumentResult
from infrastructure.dtos.document.upload_result import DocumentUploadResult

router = APIRouter(tags=["Documents"], prefix="/documents")


@router.post("/upload", response_model=DocumentUploadResult)
async def upload_document_endpoint(
    file: UploadFile = File(...),
    handler: upload.UploadDocument = Depends(),
):
    return await handler.execute(file)


@router.get("/", response_model=List[DocumentResult])
def list_documents_endpoint(
    handler: list.ListDocuments = Depends(),
):
    return handler.execute()


@router.delete("/{document_id}", status_code=204)
def delete_document_endpoint(
    document_id: UUID,
    handler: delete.DeleteDocument = Depends(),
):
    handler.execute(delete.Command(document_id=document_id))
    return Response(status_code=204)
