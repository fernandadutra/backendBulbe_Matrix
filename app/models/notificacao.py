from dataclasses import dataclass
from datetime import datetime

# fatura_emitida só existe na semente: nenhum evento da API emite fatura ainda.
TIPOS_NOTIFICACAO = ("mudanca_etapa_pedido", "pedido_criado", "indicacao_convertida", "fatura_emitida")


@dataclass
class Notificacao:
    id: str
    cliente_id: str
    tipo: str
    titulo: str
    mensagem: str
    lida: bool
    criada_em: datetime
    referencia_tipo: str  # pedido | indicacao | fatura
    referencia_id: str
