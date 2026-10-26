from datetime import datetime

from pydantic import BaseModel, Field, StrictBool

from app.schemas.comum import Paginacao


class ReferenciaNotificacao(BaseModel):
    tipo: str = Field(examples=["pedido"], description="pedido, indicacao ou fatura")
    id: str = Field(examples=["ped_7f3a9c21"])


class NotificacaoResposta(BaseModel):
    id: str = Field(examples=["not_c410aa7b"])
    tipo: str = Field(
        examples=["mudanca_etapa_pedido"],
        description="mudanca_etapa_pedido, pedido_criado, indicacao_convertida ou fatura_emitida",
    )
    titulo: str = Field(examples=["Seu pedido avançou de etapa"])
    mensagem: str = Field(examples=["Seu pedido está agora em: Enviado para Cemig."])
    lida: bool = Field(examples=[False])
    criada_em: datetime = Field(examples=["2026-08-22T09:00:00-03:00"])
    referencia: ReferenciaNotificacao


class PaginaNotificacoes(Paginacao[NotificacaoResposta]):
    nao_lidas: int = Field(examples=[1], description="Total de não lidas do cliente, sem paginação nem filtro.")


class NotificacaoRequisicao(BaseModel):
    lida: StrictBool = Field(examples=[True])
