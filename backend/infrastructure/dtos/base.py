from pydantic import BaseModel

class BaseResult(BaseModel):
    class Config:
        from_attributes = True  # Permite converter de SQLAlchemy para Pydantic