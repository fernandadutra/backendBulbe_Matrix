from dataclasses import dataclass, field
from datetime import date, datetime
from typing import List, Optional

SITUACOES_PEDIDO = ("em_andamento", "aprovado", "reprovado")

# Ordem, chave, nome e descrição das quatro etapas fixas da homologação.
CATALOGO_ETAPAS = (
    (1, "analise_bulbe", "Em análise pela Bulbe", "Sua solicitação está sendo analisada pela equipe Bulbe."),
    (2, "enviado_cemig", "Enviado para Cemig", "Depois da primeira análise, o pedido é enviado para a Cemig."),
    (3, "analise_cemig", "Em análise pela Cemig", "A Cemig avalia e aprova o processo."),
    (4, "aprovado", "Aprovado", "Após a aprovação, os benefícios ficam disponíveis no ecossistema Bulbe."),
)


@dataclass
class Etapa:
    ordem: int
    chave: str
    nome: str
    descricao: str
    situacao: str  # pendente | em_andamento | concluida
    iniciada_em: Optional[datetime] = None
    concluida_em: Optional[datetime] = None


@dataclass
class Pedido:
    id: str
    cliente_id: str
    numero_instalacao: str
    distribuidora: str
    situacao: str  # em_andamento | aprovado | reprovado
    criado_em: datetime
    previsao_proxima_atualizacao: Optional[date]
    # Última consulta guardada: etapas e o momento em que foram obtidas.
    etapas: List[Etapa] = field(default_factory=list)
    consultado_em: Optional[datetime] = None

    @property
    def etapa_atual(self) -> Optional[Etapa]:
        for etapa in self.etapas:
            if etapa.situacao == "em_andamento":
                return etapa
        concluidas = [e for e in self.etapas if e.situacao == "concluida"]
        if concluidas:
            return concluidas[-1]
        return self.etapas[0] if self.etapas else None
