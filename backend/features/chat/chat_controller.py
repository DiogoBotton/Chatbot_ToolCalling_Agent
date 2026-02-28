from uuid import UUID

from fastapi import APIRouter, Body, Depends
from infrastructure.dtos.chat.message_history import MessageHistory
from infrastructure.dtos.chat.message_result import MessageResult
from features.chat.methods import chatbot, history

router = APIRouter(tags=["Chat"], prefix="/chat")

@router.post("/", response_model=MessageResult)
async def chat_endpoint(command: chatbot.Command = Body(...),
               handler: chatbot.Chatbot = Depends()):
    return handler.execute(command)

@router.get("/history/{conversation_id}", response_model=MessageHistory)
async def history_endpoint(conversation_id: UUID, 
                           handler: history.ChatHistory = Depends()):
    return handler.execute(history.Query(conversation_id=conversation_id))