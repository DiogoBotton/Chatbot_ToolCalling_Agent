from fastapi import APIRouter, Body, Depends
from features.chat.methods import chatbot

router = APIRouter(tags=["Chat"], prefix="/chat")

@router.post("/")
async def chat_endpoint(command: chatbot.Command = Body(...),
               handler: chatbot.Chatbot = Depends()):
    return handler.execute(command)