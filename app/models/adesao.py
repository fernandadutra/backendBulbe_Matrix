from dataclasses import dataclass, field
from datetime import datetime
from typing import List, Optional

ETAPAS_ADESAO = ("contato", "negocio", "termos", "confirmacao")
CLASSES_CONSUMO = ("residencial", "comercial", "industrial", "rural")


@dataclass
class Interessado:
    id: str
    nome: str
    email: str
    whatsapp: str
    simulacao_id: Optional[str]
    aceite_comunicacoes: bool
    criado_em: datetime
    hash_token_fluxo: str
    token_expira_em: datetime
    situacao: str = "novo"  # novo | convertido


@dataclass
class DadosNegocio:
    numero_instalacao: str
    distribuidora: str
    titular_nome: str
    titular_documento: str
    cep: str
    classe_consumo: str  # residencial | comercial | industrial | rural


@dataclass
class Anexo:
    id: str
    tipo: str
    nome_arquivo: str
    tamanho_bytes: int
    conteudo: bytes
    recebido_em: datetime


@dataclass
class Aceite:
    versao_documentos: str
    aceito_em: datetime
    registrado_em: datetime
    ip: str
    user_agent: Optional[str]


@dataclass
class Adesao:
    id: str
    interessado_id: str
    criada_em: datetime
    situacao: str = "em_preenchimento"  # em_preenchimento | submetida
    negocio: Optional[DadosNegocio] = None
    anexos: List[Anexo] = field(default_factory=list)
    aceite: Optional[Aceite] = None
    cliente_id: Optional[str] = None
    pedido_id: Optional[str] = None
