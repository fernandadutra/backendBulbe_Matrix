from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, Field, StrictInt, StrictStr


class SimulacaoRequisicao(BaseModel):
    # Tipos estritos: "35000" como texto é erro de corpo. A faixa é regra de negócio, validada no service.
    valor_fatura_centavos: StrictInt = Field(examples=[35000], description="Valor da fatura em centavos.")
    consumo_kwh: Optional[StrictInt] = Field(default=None, examples=[249])
    distribuidora: Optional[StrictStr] = Field(default="CEMIG", examples=["CEMIG"])


class RotulosSimulacao(BaseModel):
    economia_mensal: str = Field(examples=["Você vai economizar por mês"])
    economia_anual: str = Field(examples=["Sua economia anual estimada"])
    valor_sem_desconto: str = Field(examples=["Sem desconto, tarifa cheia"])
    valor_com_bulbe: str = Field(examples=["Com Bulbe, até 15% desconto"])


class LinhaMemoriaCalculo(BaseModel):
    fonte: str = Field(examples=["Bulbe Energia"])
    consumo_kwh: Optional[int]
    valor_centavos: int
    valor_com_desconto_centavos: Optional[int]
    possui_desconto: bool


class SubtotalMemoriaCalculo(BaseModel):
    rotulo: str = Field(examples=["Subtotal"])
    consumo_kwh: Optional[int]
    valor_centavos: int


class MemoriaCalculo(BaseModel):
    consumo_total_kwh: Optional[int]
    linhas: List[LinhaMemoriaCalculo]
    subtotal: SubtotalMemoriaCalculo
    observacao: str


class SimulacaoResposta(BaseModel):
    id: str = Field(examples=["sim_2c81b40e"])
    calculado_em: datetime = Field(examples=["2026-08-23T14:30:00-03:00"])
    percentual_desconto: float = Field(examples=[0.15])
    valor_sem_desconto_centavos: int = Field(examples=[35000])
    valor_com_bulbe_centavos: int = Field(examples=[29750])
    economia_mensal_centavos: int = Field(examples=[5250])
    economia_anual_centavos: int = Field(examples=[63000])
    rotulos: RotulosSimulacao
    memoria_calculo: MemoriaCalculo


class SimulacaoResumo(BaseModel):
    id: str = Field(examples=["sim_2c81b40e"])
    calculado_em: datetime
    valor_sem_desconto_centavos: int
    economia_mensal_centavos: int
