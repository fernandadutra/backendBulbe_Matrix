from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field, StrictStr


class IndicacaoRequisicao(BaseModel):
    # Tipos estritos. Nome vazio e quantidade de dígitos do WhatsApp são validados no service.
    nome: StrictStr = Field(examples=["João Silva"])
    whatsapp: StrictStr = Field(examples=["+5531988887777"], description="Com ou sem máscara; de 12 a 13 dígitos.")


class IndicacaoItem(BaseModel):
    id: str = Field(examples=["ind_a10"])
    nome_ofuscado: str = Field(examples=["Jo** S****"], description="O nome completo do indicado nunca é exibido.")
    situacao: str = Field(examples=["convertida"], description="pendente ou convertida")
    indicada_em: date = Field(examples=["2026-07-02"])


class FaixaIndicacao(BaseModel):
    chave: str = Field(examples=["economia_com_indicacoes"])
    nome: str = Field(examples=["Economia + indicações"])
    proxima_faixa: Optional[str] = Field(default=None, examples=["top_indicador"], description="Nulo na faixa TOP.")
    indicacoes_para_proxima_faixa: int = Field(examples=[7])


class PainelIndicacoes(BaseModel):
    codigo: str = Field(examples=["MARIA50"])
    url_compartilhamento: str = Field(examples=["https://bulbe.com.br/indique/MARIA50"])
    recompensa_por_indicacao_centavos: int = Field(examples=[5000])
    total_indicacoes: int = Field(examples=[3])
    indicacoes_convertidas: int = Field(examples=[2])
    credito_acumulado_centavos: int = Field(examples=[10000])
    faixa_atual: FaixaIndicacao
    indicacoes: List[IndicacaoItem]
