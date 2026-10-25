from datetime import datetime
from typing import Annotated, List, Literal, Optional, Union

from pydantic import BaseModel, Field


class ItemLista(BaseModel):
    titulo: Optional[str] = None
    texto: str


class BlocoParagrafo(BaseModel):
    tipo: Literal["paragrafo"] = "paragrafo"
    titulo: Optional[str] = None
    texto: str


class BlocoLista(BaseModel):
    tipo: Literal["lista"] = "lista"
    ordenada: bool
    itens: List[ItemLista]


Bloco = Annotated[Union[BlocoParagrafo, BlocoLista], Field(discriminator="tipo")]


class Dica(BaseModel):
    elemento: str = Field(examples=["titulo-status"])
    titulo: str = Field(examples=["Como funciona o acompanhamento"])
    rotulo_acessivel: str = Field(examples=["Entender as etapas do pedido"])
    blocos: List[Bloco]


class RespostaDicas(BaseModel):
    tela: str = Field(examples=["status-pedido"])
    atualizado_em: Optional[datetime] = Field(examples=["2026-08-20T11:00:00-03:00"])
    dicas: List[Dica]
