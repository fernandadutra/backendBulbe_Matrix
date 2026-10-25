from dataclasses import dataclass
from datetime import datetime
from typing import Optional


@dataclass
class Resgate:
    id: str
    cliente_id: str
    beneficio_id: str
    resgatado_em: datetime
    situacao: str  # confirmado
    instrucoes: str
    codigo: str
    url_acesso: str
    expira_em: datetime
    chave_idempotencia: str
    pedido_id: Optional[str] = None
