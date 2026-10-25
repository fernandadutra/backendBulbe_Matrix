from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field


class PedidoResumo(BaseModel):
    id: str = Field(examples=["ped_7f3a9c21"])
    numero_instalacao: str = Field(examples=["3013588579"])
    distribuidora: str = Field(examples=["CEMIG"])
    situacao: str = Field(examples=["em_andamento"], description="em_andamento, aprovado ou reprovado")
    etapa_atual_ordem: Optional[int] = Field(examples=[1])
    etapa_atual_nome: Optional[str] = Field(examples=["Em análise pela Bulbe"])
    criado_em: datetime = Field(examples=["2026-06-02T09:14:00-03:00"])


class _EtapaBase(BaseModel):
    ordem: int = Field(examples=[1])
    chave: str = Field(examples=["analise_bulbe"])
    nome: str = Field(examples=["Em análise pela Bulbe"])
    descricao: str = Field(examples=["Sua solicitação está sendo analisada pela equipe Bulbe."])
    situacao: str = Field(examples=["em_andamento"], description="pendente, em_andamento ou concluida")


class EtapaPedido(_EtapaBase):
    concluida_em: Optional[datetime] = None


class EtapaAtualPedido(_EtapaBase):
    iniciada_em: Optional[datetime] = Field(default=None, examples=["2026-06-02T09:14:00-03:00"])


class PrazoEstimado(BaseModel):
    minimo: int = Field(examples=[90])
    maximo: int = Field(examples=[120])


class StatusPedido(BaseModel):
    pedido_id: str = Field(examples=["ped_7f3a9c21"])
    numero_instalacao: str = Field(examples=["3013588579"])
    situacao: str = Field(examples=["em_andamento"])
    etapa_atual: Optional[EtapaAtualPedido]
    etapas: List[EtapaPedido]
    previsao_proxima_atualizacao: Optional[date] = Field(examples=["2026-09-15"])
    prazo_estimado_dias: PrazoEstimado
    consultado_em: Optional[datetime] = Field(examples=["2026-08-23T14:30:00-03:00"])
    dado_desatualizado: bool
