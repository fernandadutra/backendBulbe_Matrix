from typing import List

from pydantic import BaseModel, Field


class PassoBoasVindas(BaseModel):
    ordem: int = Field(examples=[1])
    titulo: str = Field(examples=["Energia solar que gera economia"])
    texto: str = Field(examples=["Nossas fazendas solares produzem energia limpa e renovável."])
    url_ilustracao: str = Field(examples=["https://cdn.bulbe.com.br/boas-vindas/passo-1.svg"])
    texto_alternativo: str = Field(examples=["Painéis solares em uma fazenda solar"])


class BoasVindasResposta(BaseModel):
    versao: str = Field(examples=["2026-08-01"])
    titulo: str = Field(examples=["Como funciona"])
    passos: List[PassoBoasVindas]
