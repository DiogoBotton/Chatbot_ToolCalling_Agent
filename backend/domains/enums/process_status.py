from enum import Enum

class ProcessStatus(Enum):
    RECEBIDO = "RECEBIDO"
    EM_ANALISE = "EM_ANALISE"
    PENDENTE = "PENDENTE"
    APROVADO = "APROVADO"
    FINALIZADO = "FINALIZADO"