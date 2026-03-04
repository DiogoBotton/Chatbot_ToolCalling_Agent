from uuid import UUID


from fastapi import APIRouter, Body, Depends

from infrastructure.dtos.generic.register_result import RegisterResult
from features.conversation.methods import create, history
from infrastructure.dtos.chat.message_history import MessageHistory

router = APIRouter(tags=["Conversations"], prefix="/conversations")

@router.post("/", response_model=RegisterResult)
async def create_conversation_endpoint(
    command: create.Command = Body(...),
    handler: create.CreateConversation = Depends(),
):
    return handler.execute(command)

@router.get("/history/{conversation_id}", response_model=MessageHistory)
async def get_history_endpoint(conversation_id: UUID, 
                           handler: history.ChatHistory = Depends()):
    return handler.execute(history.Query(conversation_id=conversation_id))