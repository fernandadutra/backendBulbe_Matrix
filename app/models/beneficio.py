from dataclasses import dataclass
from datetime import date
from typing import Optional

REGRAS_ACESSO = ("livre", "pedido_aprovado", "fatura_ativa")
TIPOS_RESGATE = ("uso_unico", "recorrente")
CHAVES_TRILHA = ("connect", "movement", "experience")


@dataclass
class Parceiro:
    id: str
    nome: str
    url_logo: str
    cor_marca: str
    destaque: bool = False


@dataclass
class Trilha:
    chave: str
    nome: str
    descricao: str
    regra_acesso: str  # livre | pedido_aprovado | fatura_ativa
    cor_tema: str
    url_icone: str


@dataclass
class Beneficio:
    id: str
    trilha: str
    parceiro_id: str
    titulo: str
    descricao: str
    regras_de_uso: str
    tipo: str  # uso_unico | recorrente
    regra_acesso: str  # regra própria, somada à da trilha
    validade_inicio: date
    validade_fim: Optional[date]
    ativo: bool
    dias_validade_resgate: int
    instrucoes: str
    prefixo_codigo: str
    url_acesso: str
    total_resgates: int = 0

    def vigente_em(self, dia: date) -> bool:
        if not self.ativo or dia < self.validade_inicio:
            return False
        return self.validade_fim is None or dia <= self.validade_fim
