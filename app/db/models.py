"""
Modelos do SQLAlchemy: cada classe é uma tabela do banco.

Atenção: estes NÃO são os modelos do domínio. As dataclasses de app/models
continuam sendo o que os services recebem e devolvem. Estes aqui descrevem
apenas como os dados ficam guardados, e só os repositórios SQL os conhecem.

ordem_gravacao: vários repositórios devolvem listas "mais recentes primeiro,
e em empate de data vale a ordem de gravação". Os ids do domínio são textos
aleatórios, então guardamos a ordem de gravação numa coluna própria.
"""

from datetime import date, datetime
from typing import Optional

from sqlalchemy import (
    JSON,
    Boolean,
    Date,
    Float,
    ForeignKey,
    Integer,
    LargeBinary,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base
from app.db.tipos import DataHora

ID = String(40)


# Autenticação


class ClienteModel(Base):
    __tablename__ = "clientes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[Optional[str]] = mapped_column(String(254), unique=True, index=True)
    cpf: Mapped[Optional[str]] = mapped_column(String(11), unique=True, index=True)
    telefone: Mapped[Optional[str]] = mapped_column(String(20))
    senha_hash: Mapped[Optional[str]] = mapped_column(String(255))
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


class SessaoModel(Base):
    __tablename__ = "sessoes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    criada_em: Mapped[datetime] = mapped_column(DataHora)
    expira_em: Mapped[datetime] = mapped_column(DataHora)
    hash_token: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    revogada: Mapped[bool] = mapped_column(Boolean, default=False)

    hashes_usados: Mapped[list["HashTokenUsadoModel"]] = relationship(
        back_populates="sessao", cascade="all, delete-orphan", lazy="selectin"
    )


class HashTokenUsadoModel(Base):
    """Hashes de tokens de renovação já rotacionados (Sessao.hashes_usados)."""

    __tablename__ = "hashes_token_usados"

    hash: Mapped[str] = mapped_column(String(64), primary_key=True)
    sessao_id: Mapped[str] = mapped_column(ForeignKey("sessoes.id"), index=True)

    sessao: Mapped[SessaoModel] = relationship(back_populates="hashes_usados")


# Simulações


class SimulacaoModel(Base):
    __tablename__ = "simulacoes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[Optional[str]] = mapped_column(ForeignKey("clientes.id"), index=True)
    calculado_em: Mapped[datetime] = mapped_column(DataHora)
    distribuidora: Mapped[str] = mapped_column(String(40))
    consumo_kwh: Mapped[Optional[int]] = mapped_column(Integer)
    percentual_desconto: Mapped[float] = mapped_column(Float)
    valor_sem_desconto_centavos: Mapped[int] = mapped_column(Integer)
    valor_com_bulbe_centavos: Mapped[int] = mapped_column(Integer)
    economia_mensal_centavos: Mapped[int] = mapped_column(Integer)
    economia_anual_centavos: Mapped[int] = mapped_column(Integer)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


# Adesão


class InteressadoModel(Base):
    __tablename__ = "interessados"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    email: Mapped[str] = mapped_column(String(254), index=True)
    whatsapp: Mapped[str] = mapped_column(String(20))
    simulacao_id: Mapped[Optional[str]] = mapped_column(ForeignKey("simulacoes.id"))
    aceite_comunicacoes: Mapped[bool] = mapped_column(Boolean)
    criado_em: Mapped[datetime] = mapped_column(DataHora)
    hash_token_fluxo: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    token_expira_em: Mapped[datetime] = mapped_column(DataHora)
    situacao: Mapped[str] = mapped_column(String(20), default="novo")


class AdesaoModel(Base):
    """Adesão com os dados de negócio e o aceite embutidos (colunas opcionais)."""

    __tablename__ = "adesoes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    interessado_id: Mapped[str] = mapped_column(ForeignKey("interessados.id"), unique=True)
    criada_em: Mapped[datetime] = mapped_column(DataHora)
    situacao: Mapped[str] = mapped_column(String(20), default="em_preenchimento")
    cliente_id: Mapped[Optional[str]] = mapped_column(ForeignKey("clientes.id"))
    pedido_id: Mapped[Optional[str]] = mapped_column(ForeignKey("pedidos.id"))

    # Etapa "negocio" (DadosNegocio). Todas nulas enquanto a etapa não foi preenchida.
    negocio_numero_instalacao: Mapped[Optional[str]] = mapped_column(String(20))
    negocio_distribuidora: Mapped[Optional[str]] = mapped_column(String(40))
    negocio_titular_nome: Mapped[Optional[str]] = mapped_column(String(120))
    negocio_titular_documento: Mapped[Optional[str]] = mapped_column(String(14))
    negocio_cep: Mapped[Optional[str]] = mapped_column(String(8))
    negocio_classe_consumo: Mapped[Optional[str]] = mapped_column(String(20))

    # Etapa "termos" (Aceite). Todas nulas enquanto os termos não foram aceitos.
    aceite_versao_documentos: Mapped[Optional[str]] = mapped_column(String(20))
    aceite_aceito_em: Mapped[Optional[datetime]] = mapped_column(DataHora)
    aceite_registrado_em: Mapped[Optional[datetime]] = mapped_column(DataHora)
    aceite_ip: Mapped[Optional[str]] = mapped_column(String(45))
    aceite_user_agent: Mapped[Optional[str]] = mapped_column(String(500))

    anexos: Mapped[list["AnexoModel"]] = relationship(
        back_populates="adesao", cascade="all, delete-orphan", order_by="AnexoModel.ordem_gravacao", lazy="selectin"
    )


class AnexoModel(Base):
    __tablename__ = "anexos"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    adesao_id: Mapped[str] = mapped_column(ForeignKey("adesoes.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    nome_arquivo: Mapped[str] = mapped_column(String(255))
    tamanho_bytes: Mapped[int] = mapped_column(Integer)
    conteudo: Mapped[bytes] = mapped_column(LargeBinary)
    recebido_em: Mapped[datetime] = mapped_column(DataHora)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)

    adesao: Mapped[AdesaoModel] = relationship(back_populates="anexos")


# Pedidos e faturas


class PedidoModel(Base):
    __tablename__ = "pedidos"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    numero_instalacao: Mapped[str] = mapped_column(String(20))
    distribuidora: Mapped[str] = mapped_column(String(40))
    situacao: Mapped[str] = mapped_column(String(20))
    criado_em: Mapped[datetime] = mapped_column(DataHora)
    previsao_proxima_atualizacao: Mapped[Optional[date]] = mapped_column(Date)
    consultado_em: Mapped[Optional[datetime]] = mapped_column(DataHora)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)

    etapas: Mapped[list["EtapaPedidoModel"]] = relationship(
        back_populates="pedido", cascade="all, delete-orphan", order_by="EtapaPedidoModel.ordem", lazy="selectin"
    )


class EtapaPedidoModel(Base):
    __tablename__ = "etapas_pedido"

    pedido_id: Mapped[str] = mapped_column(ForeignKey("pedidos.id"), primary_key=True)
    ordem: Mapped[int] = mapped_column(Integer, primary_key=True)
    chave: Mapped[str] = mapped_column(String(40))
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(String(500))
    situacao: Mapped[str] = mapped_column(String(20))
    iniciada_em: Mapped[Optional[datetime]] = mapped_column(DataHora)
    concluida_em: Mapped[Optional[datetime]] = mapped_column(DataHora)

    pedido: Mapped[PedidoModel] = relationship(back_populates="etapas")


class FaturaModel(Base):
    __tablename__ = "faturas"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    pedido_id: Mapped[str] = mapped_column(ForeignKey("pedidos.id"), index=True)
    competencia: Mapped[str] = mapped_column(String(7))
    vencimento: Mapped[date] = mapped_column(Date)
    valor_centavos: Mapped[int] = mapped_column(Integer)
    economia_centavos: Mapped[int] = mapped_column(Integer)
    consumo_kwh: Mapped[int] = mapped_column(Integer)
    situacao: Mapped[str] = mapped_column(String(20))
    linha_digitavel: Mapped[str] = mapped_column(String(60))
    url_pdf: Mapped[str] = mapped_column(String(500))
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


# Clube de benefícios


class ParceiroModel(Base):
    __tablename__ = "parceiros"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    url_logo: Mapped[str] = mapped_column(String(500))
    cor_marca: Mapped[str] = mapped_column(String(20))
    destaque: Mapped[bool] = mapped_column(Boolean, default=False)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


class TrilhaModel(Base):
    __tablename__ = "trilhas"

    chave: Mapped[str] = mapped_column(String(20), primary_key=True)
    nome: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(String(500))
    regra_acesso: Mapped[str] = mapped_column(String(20))
    cor_tema: Mapped[str] = mapped_column(String(20))
    url_icone: Mapped[str] = mapped_column(String(500))
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


class BeneficioModel(Base):
    __tablename__ = "beneficios"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    trilha: Mapped[str] = mapped_column(ForeignKey("trilhas.chave"), index=True)
    parceiro_id: Mapped[str] = mapped_column(ForeignKey("parceiros.id"))
    titulo: Mapped[str] = mapped_column(String(120))
    descricao: Mapped[str] = mapped_column(String(500))
    regras_de_uso: Mapped[str] = mapped_column(String(1000))
    tipo: Mapped[str] = mapped_column(String(20))
    regra_acesso: Mapped[str] = mapped_column(String(20))
    validade_inicio: Mapped[date] = mapped_column(Date)
    validade_fim: Mapped[Optional[date]] = mapped_column(Date)
    ativo: Mapped[bool] = mapped_column(Boolean)
    dias_validade_resgate: Mapped[int] = mapped_column(Integer)
    instrucoes: Mapped[str] = mapped_column(String(1000))
    prefixo_codigo: Mapped[str] = mapped_column(String(20))
    url_acesso: Mapped[str] = mapped_column(String(500))
    total_resgates: Mapped[int] = mapped_column(Integer, default=0)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


class ResgateModel(Base):
    __tablename__ = "resgates"
    # A mesma chave de idempotência nunca gera dois resgates para o mesmo cliente.
    __table_args__ = (UniqueConstraint("cliente_id", "chave_idempotencia", name="uq_resgates_cliente_chave"),)

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    beneficio_id: Mapped[str] = mapped_column(ForeignKey("beneficios.id"), index=True)
    resgatado_em: Mapped[datetime] = mapped_column(DataHora)
    situacao: Mapped[str] = mapped_column(String(20))
    instrucoes: Mapped[str] = mapped_column(String(1000))
    codigo: Mapped[str] = mapped_column(String(40))
    url_acesso: Mapped[str] = mapped_column(String(500))
    expira_em: Mapped[datetime] = mapped_column(DataHora)
    chave_idempotencia: Mapped[str] = mapped_column(String(100))
    pedido_id: Mapped[Optional[str]] = mapped_column(ForeignKey("pedidos.id"))
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


# Indique e ganhe


class IndicacaoModel(Base):
    __tablename__ = "indicacoes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    nome: Mapped[str] = mapped_column(String(120))
    whatsapp: Mapped[str] = mapped_column(String(20), index=True)
    situacao: Mapped[str] = mapped_column(String(20))
    indicada_em: Mapped[date] = mapped_column(Date)
    convertida_em: Mapped[Optional[datetime]] = mapped_column(DataHora)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


class CodigoIndicacaoModel(Base):
    __tablename__ = "codigos_indicacao"

    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), primary_key=True)
    codigo: Mapped[str] = mapped_column(String(20), unique=True, index=True)


# Notificações


class NotificacaoModel(Base):
    __tablename__ = "notificacoes"

    id: Mapped[str] = mapped_column(ID, primary_key=True)
    cliente_id: Mapped[str] = mapped_column(ForeignKey("clientes.id"), index=True)
    tipo: Mapped[str] = mapped_column(String(40))
    titulo: Mapped[str] = mapped_column(String(200))
    mensagem: Mapped[str] = mapped_column(String(1000))
    lida: Mapped[bool] = mapped_column(Boolean, default=False)
    criada_em: Mapped[datetime] = mapped_column(DataHora)
    # Referência polimórfica (pedido, indicação ou fatura): por isso sem chave estrangeira.
    referencia_tipo: Mapped[str] = mapped_column(String(20))
    referencia_id: Mapped[str] = mapped_column(ID)
    ordem_gravacao: Mapped[int] = mapped_column(Integer)


# Conteúdo


class DicaModel(Base):
    """Texto de ajuda contextual. Os blocos (parágrafos e listas) ficam em JSON."""

    __tablename__ = "dicas"
    __table_args__ = (UniqueConstraint("tela", "elemento", name="uq_dicas_tela_elemento"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    tela: Mapped[str] = mapped_column(String(40), index=True)
    elemento: Mapped[str] = mapped_column(String(60))
    titulo: Mapped[str] = mapped_column(String(200))
    rotulo_acessivel: Mapped[str] = mapped_column(String(200))
    atualizado_em: Mapped[datetime] = mapped_column(DataHora)
    blocos: Mapped[list] = mapped_column(JSON)


class ConteudoBoasVindasModel(Base):
    __tablename__ = "conteudos_boas_vindas"

    versao: Mapped[str] = mapped_column(String(20), primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))

    passos: Mapped[list["PassoBoasVindasModel"]] = relationship(
        back_populates="conteudo", cascade="all, delete-orphan", order_by="PassoBoasVindasModel.ordem", lazy="selectin"
    )


class PassoBoasVindasModel(Base):
    __tablename__ = "passos_boas_vindas"

    versao: Mapped[str] = mapped_column(ForeignKey("conteudos_boas_vindas.versao"), primary_key=True)
    ordem: Mapped[int] = mapped_column(Integer, primary_key=True)
    titulo: Mapped[str] = mapped_column(String(200))
    texto: Mapped[str] = mapped_column(Text)
    url_ilustracao: Mapped[str] = mapped_column(String(500))
    texto_alternativo: Mapped[str] = mapped_column(String(300))

    conteudo: Mapped[ConteudoBoasVindasModel] = relationship(back_populates="passos")
