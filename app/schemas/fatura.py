from datetime import date
from typing import List, Optional

from pydantic import BaseModel, Field

from app.schemas.comum import Paginacao


class AcaoSugerida(BaseModel):
    rotulo: str = Field(examples=["Ver status do pedido"])
    destino: str = Field(examples=["status-pedido"])


class EstadoVazioComAcao(BaseModel):
    chave: str = Field(
        examples=["aguardando_homologacao"],
        description="sem_instalacao, aguardando_homologacao ou homologado_sem_fatura",
    )
    titulo: str = Field(examples=["Oops... Não encontrei nenhuma fatura."])
    mensagem: str = Field(
        examples=["Seu pedido ainda está em análise pela Cemig. A primeira fatura chega depois da aprovação."]
    )
    acao_sugerida: Optional[AcaoSugerida] = None


class FaturaResposta(BaseModel):
    id: str = Field(examples=["fat_08a2ce31"])
    competencia: str = Field(examples=["2026-08"])
    vencimento: date = Field(examples=["2026-09-10"])
    valor_centavos: int = Field(examples=[29750])
    economia_centavos: int = Field(examples=[5250])
    situacao: str = Field(examples=["aberta"], description="aberta, paga ou vencida")
    linha_digitavel: str = Field(examples=["00190000090123456789012345678901234567890123"])
    url_pdf: str = Field(examples=["https://cdn.bulbe.com.br/faturas/fat_08a2ce31.pdf"])


class PaginaFaturas(Paginacao[FaturaResposta]):
    estado_vazio: Optional[EstadoVazioComAcao] = Field(
        default=None, description="Só vem preenchido quando o cliente não tem nenhuma fatura."
    )


class PontoConsumo(BaseModel):
    competencia: str = Field(examples=["2026-08"], description="AAAA-MM na série mensal, AAAA na anual")
    consumo_kwh: int = Field(examples=[249])
    valor_pago_centavos: int = Field(examples=[29750])
    economia_centavos: int = Field(examples=[5250])


class TotaisConsumo(BaseModel):
    economia_acumulada_centavos: int = Field(examples=[10330])
    consumo_medio_kwh: int = Field(examples=[245])


class ConsumoResposta(BaseModel):
    instalacao: Optional[str] = Field(examples=["3013588579"])
    granularidade: str = Field(examples=["mensal"], description="mensal ou anual")
    serie: List[PontoConsumo]
    totais: TotaisConsumo
    estado_vazio: Optional[EstadoVazioComAcao] = Field(
        default=None, description="Só vem preenchido quando o cliente não tem nenhuma fatura."
    )
