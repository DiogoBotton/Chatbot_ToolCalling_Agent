from fastapi import APIRouter, Body, Depends
from infrastructure.dtos.chat.message_result import MessageResult
from features.chat.methods import chatbot

router = APIRouter(tags=["Chat"])

@router.post("/chat", response_model=MessageResult)
async def chat_endpoint(command: chatbot.Command = Body(...),
               handler: chatbot.Chatbot = Depends()):
    return handler.execute(command)