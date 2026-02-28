from langchain.tools import tool
from sqlalchemy.orm import Session
from data.database import SessionLocal
from domains.user import User
from domains.process import Process
from domains.enums.process_status import ProcessStatus
import random

# Criar processo
@tool
def create_process_tool(email: str) -> dict:
    """Cria um novo processo de visto com status RECEBIDO. Necessário informar email."""
    
    db: Session = SessionLocal()
    
    user = db.query(User).filter(User.email == email).first()
    if not user:
        user = User(email=email)
        db.add(user)
        db.commit()
        db.refresh(user)

    number_process = ''.join(random.choices('0123456789', k=15))
    process = Process(number=number_process, user_id=user.id)
    
    db.add(process)
    db.commit()
    db.refresh(process)
    
    return {
        "number": process.number,
        "status": process.status.value
    }


@tool
def get_process_tool(number: str) -> dict:
    """Consulta um processo de visto pelo número do processo."""
    
    db: Session = SessionLocal()
    
    process = db.query(Process).filter(Process.number == number).first()
    
    if not process:
        return {"error": "Processo não encontrado"}
    
    return {
        "number": process.number,
        "status": process.status.value
    }


@tool
def update_process_status_tool(number: str, status: str) -> dict:
    """
    Atualiza o status de um processo de visto.
    Status permitidos: RECEBIDO, EM_ANALISE, PENDENTE, APROVADO, FINALIZADO.
    É necessário informar o número do processo e o novo status.
    """
    
    db: Session = SessionLocal()
    
    process = db.query(Process).filter(Process.number == number).first()
    
    if not process:
        return {"error": "Processo não encontrado"}
    
    process.status = ProcessStatus(status)
    db.commit()
    
    return {
        "number": process.number,
        "status": process.status.value
    }