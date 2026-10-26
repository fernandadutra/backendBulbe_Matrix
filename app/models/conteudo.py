from dataclasses import dataclass, field
from typing import List


@dataclass
class Passo:
    ordem: int
    titulo: str
    texto: str
    url_ilustracao: str
    texto_alternativo: str


@dataclass
class ConteudoBoasVindas:
    versao: str
    titulo: str
    passos: List[Passo] = field(default_factory=list)
