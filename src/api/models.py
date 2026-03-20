from typing import List, Optional
from pydantic import BaseModel, Field, field_validator


class MoleculeBase(BaseModel):
    """Базовая модель молекулы"""
    smiles: str = Field(..., min_length=1, max_length=1000, description="SMILES строка молекулы")
    name: Optional[str] = Field(None, max_length=255, description="Название молекулы")

    @field_validator("smiles")
    @classmethod
    def validate_smiles(cls, v: str) -> str:
        """Валидация SMILES строки"""
        if not v or v.isspace():
            raise ValueError("SMILES не может быть пустым")
        return v


class MoleculeCreate(MoleculeBase):
    """Модель для СОЗДАНИЯ молекулы (POST запрос)"""
    pass


class MoleculeResponse(MoleculeBase):
    """Модель для ОТВЕТА (GET запрос)"""
    id: int = Field(..., description="Уникальный идентификатор молекулы")

    # важно для Pydantic V2
    model_config = {"from_attributes": True}


class MoleculeUpdate(BaseModel):
    """Модель для ОБНОВЛЕНИЯ молекулы (PUT запрос)"""
    smiles: Optional[str] = Field(None, min_length=1, max_length=1000, description="SMILES-строка молекулы")
    name: Optional[str] = Field(None, max_length=255, description="Название молекулы")


class SearchRequest(BaseModel):
    """Модель для запроса поиска"""
    substructure: str = Field(..., description="SMILES субструктуры для поиска")


class MoleculesList(BaseModel):
    """Модель для списка молекул с пагинацией"""
    molecules: List[MoleculeResponse]
    total: int
    page: int
    page_size: int
    total_pages: int