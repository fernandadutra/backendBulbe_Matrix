from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional, Union

TELAS_COM_AJUDA = (
    "simular-desconto",
    "status-pedido",
    "beneficios",
    "impulsione-fatura",
    "faturas",
    "adesao",
    "indique-ganhe",
)


@dataclass
class ItemLista:
    texto: str
    titulo: Optional[str] = None


@dataclass
class BlocoParagrafo:
    texto: str
    titulo: Optional[str] = None


@dataclass
class BlocoLista:
    itens: List[ItemLista]
    ordenada: bool = False


Bloco = Union[BlocoParagrafo, BlocoLista]


@dataclass
class Dica:
    tela: str
    elemento: str
    titulo: str
    rotulo_acessivel: str
    atualizado_em: datetime
    blocos: List[Bloco] = field(default_factory=list)
