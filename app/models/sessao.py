from dataclasses import dataclass, field
from datetime import datetime
from typing import Set


@dataclass
class Sessao:
    id: str
    cliente_id: str
    criada_em: datetime
    expira_em: datetime
    hash_token: str
    hashes_usados: Set[str] = field(default_factory=set)
    revogada: bool = False
