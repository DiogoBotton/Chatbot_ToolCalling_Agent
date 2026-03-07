from fastapi import APIRouter, Body, Depends
from infrastructure.dtos.chat.message_result import MessageResult
from features.chat.methods import chatbot_stream, chatbot

router = APIRouter(tags=["Chat"], prefix="/chat")

@router.post("/stream")
async def chat_stream_endpoint(command: chatbot_stream.Command = Body(...),
               handler: chatbot_stream.Chatbot = Depends()):
    return handler.execute(command)

@router.post("/", response_model=MessageResult)
async def chat_endpoint(command: chatbot.Command = Body(...),
               handler: chatbot.Chatbot = Depends()):
    return handler.execute(command)