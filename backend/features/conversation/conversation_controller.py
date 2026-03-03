from fastapi import APIRouter, Body, Depends

from infrastructure.dtos.generic.register_result import RegisterResult
from features.conversation.methods import create

router = APIRouter(tags=["Conversations"], prefix="/conversations")

@router.post("/", response_model=RegisterResult)
async def create_conversation_endpoint(
    command: create.Command = Body(...),
    handler: create.CreateConversation = Depends(),
):
    return handler.execute(command)
