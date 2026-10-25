from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Simulacao:
    id: str
    cliente_id: Optional[str]
    calculado_em: datetime
    distribuidora: str
    consumo_kwh: Optional[int]
    percentual_desconto: float
    valor_sem_desconto_centavos: int
    valor_com_bulbe_centavos: int
    economia_mensal_centavos: int
    economia_anual_centavos: int
