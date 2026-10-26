from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional

SITUACOES_INDICACAO = ("pendente", "convertida")

# Chave, nome e quantidade mínima de indicações de cada faixa, da menor para a maior.
CATALOGO_FAIXAS = (
    ("comece_a_indicar", "Comece a indicar", 0),
    ("primeira_indicacao", "Primeira indicação", 1),
    ("economia_com_indicacoes", "Economia + indicações", 2),
    ("top_indicador", "TOP indicador", 10),
)


@dataclass
class Indicacao:
    id: str
    cliente_id: str  # quem indicou
    nome: str
    whatsapp: str  # "+" seguido dos dígitos
    situacao: str  # pendente | convertida
    indicada_em: date
    convertida_em: Optional[datetime] = None
