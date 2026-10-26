from typing import List

from pydantic import BaseModel, Field


class SessaoRequisicao(BaseModel):
    identificador: str = Field(examples=["cliente@exemplo.com.br"], description="E-mail ou CPF, com ou sem máscara.")
    senha: str = Field(examples=["********"])


class TokenRenovacaoRequisicao(BaseModel):
    token_renovacao: str = Field(examples=["trn_9d21ba0c7e"])


class ClienteSessao(BaseModel):
    id: str = Field(examples=["cli_3f81aa02"])
    nome: str = Field(examples=["Maria Souza"])
    possui_pedido_em_andamento: bool
    possui_fatura_emitida: bool


class SessaoResposta(BaseModel):
    token_acesso: str = Field(examples=["eyJhbGciOiJIUzI1NiIs..."])
    tipo_token: str = Field(examples=["Bearer"])
    expira_em_segundos: int = Field(examples=[900])
    token_renovacao: str = Field(examples=["trn_9d21ba0c7e"])
    cliente: ClienteSessao


class InstalacaoPerfil(BaseModel):
    numero: str = Field(examples=["3013588579"])
    distribuidora: str = Field(examples=["CEMIG"])
    pedido_id: str = Field(examples=["ped_7f3a9c21"])
    principal: bool


class Perfil(BaseModel):
    id: str = Field(examples=["cli_3f81aa02"])
    nome: str = Field(examples=["Maria Souza"])
    email: str = Field(examples=["cliente@exemplo.com.br"])
    telefone: str = Field(examples=["+5531999998888"])
    instalacoes: List[InstalacaoPerfil]
