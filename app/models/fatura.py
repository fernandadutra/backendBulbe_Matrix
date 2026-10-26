from dataclasses import dataclass
from datetime import date

SITUACOES_FATURA = ("aberta", "paga", "vencida")
GRANULARIDADES = ("mensal", "anual")


@dataclass
class Fatura:
    id: str
    cliente_id: str
    pedido_id: str
    competencia: str  # YYYY-MM
    vencimento: date
    valor_centavos: int
    economia_centavos: int
    consumo_kwh: int
    situacao: str  # aberta | paga
    linha_digitavel: str
    url_pdf: str

    def situacao_em(self, dia: date) -> str:
        # "vencida" é derivada da data: guardá-la deixaria a fatura desatualizada com o passar do tempo.
        if self.situacao == "aberta" and self.vencimento < dia:
            return "vencida"
        return self.situacao
