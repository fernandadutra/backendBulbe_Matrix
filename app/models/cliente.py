from dataclasses import dataclass
from typing import Optional


@dataclass
class Cliente:
    id: str
    nome: str
    email: Optional[str] = None
    cpf: Optional[str] = None
    telefone: Optional[str] = None
    senha_hash: Optional[str] = None
