"""
Camada de Persistência, repositórios de Interessado e Adesão.
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.

A adesão guarda os dados de negócio e o aceite em colunas da própria tabela
(nulas enquanto a etapa não foi feita) e os anexos numa tabela filha.
"""

from typing import Dict, Optional, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import AdesaoModel, AnexoModel, InteressadoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.adesao import Aceite, Adesao, Anexo, DadosNegocio, Interessado

_CAMPOS_INTERESSADO = (
    "nome", "email", "whatsapp", "simulacao_id", "aceite_comunicacoes", "criado_em", "hash_token_fluxo",
    "token_expira_em", "situacao",
)
_CAMPOS_NEGOCIO = ("numero_instalacao", "distribuidora", "titular_nome", "titular_documento", "cep", "classe_consumo")
_CAMPOS_ACEITE = ("versao_documentos", "aceito_em", "registrado_em", "ip", "user_agent")


class AdesaoRepository(Protocol):
    def salvar_interessado(self, interessado: Interessado) -> None: ...
    def obter_interessado(self, interessado_id: str) -> Optional[Interessado]: ...
    def interessado_por_email(self, email: str) -> Optional[Interessado]: ...
    def interessado_por_hash_token(self, hash_token: str) -> Optional[Interessado]: ...
    def salvar_adesao(self, adesao: Adesao) -> None: ...
    def obter_adesao(self, adesao_id: str) -> Optional[Adesao]: ...
    def adesao_do_interessado(self, interessado_id: str) -> Optional[Adesao]: ...


class InMemoryAdesaoRepository:
    def __init__(self):
        self._interessados: Dict[str, Interessado] = {}
        self._adesoes: Dict[str, Adesao] = {}

    def salvar_interessado(self, interessado: Interessado) -> None:
        self._interessados[interessado.id] = interessado

    def obter_interessado(self, interessado_id: str) -> Optional[Interessado]:
        return self._interessados.get(interessado_id)

    def interessado_por_email(self, email: str) -> Optional[Interessado]:
        return next((i for i in self._interessados.values() if i.email.lower() == email.lower()), None)

    def interessado_por_hash_token(self, hash_token: str) -> Optional[Interessado]:
        return next((i for i in self._interessados.values() if i.hash_token_fluxo == hash_token), None)

    def salvar_adesao(self, adesao: Adesao) -> None:
        self._adesoes[adesao.id] = adesao

    def obter_adesao(self, adesao_id: str) -> Optional[Adesao]:
        return self._adesoes.get(adesao_id)

    def adesao_do_interessado(self, interessado_id: str) -> Optional[Adesao]:
        return next((a for a in self._adesoes.values() if a.interessado_id == interessado_id), None)


# Conversões de Interessado


def _interessado_para_dominio(m: InteressadoModel) -> Interessado:
    return Interessado(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_INTERESSADO})


def _gravar_interessado(sessao: Session, i: Interessado) -> None:
    modelo = sessao.get(InteressadoModel, i.id)
    if modelo is None:
        modelo = InteressadoModel(id=i.id)
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(i, c) for c in _CAMPOS_INTERESSADO})


# Conversões de Adesão


def _adesao_para_dominio(m: AdesaoModel) -> Adesao:
    negocio = None
    if m.negocio_numero_instalacao is not None:
        negocio = DadosNegocio(**{c: getattr(m, f"negocio_{c}") for c in _CAMPOS_NEGOCIO})
    aceite = None
    if m.aceite_versao_documentos is not None:
        aceite = Aceite(**{c: getattr(m, f"aceite_{c}") for c in _CAMPOS_ACEITE})
    anexos = [
        Anexo(id=a.id, tipo=a.tipo, nome_arquivo=a.nome_arquivo, tamanho_bytes=a.tamanho_bytes, conteudo=a.conteudo,
              recebido_em=a.recebido_em)
        for a in m.anexos
    ]
    return Adesao(
        id=m.id, interessado_id=m.interessado_id, criada_em=m.criada_em, situacao=m.situacao, negocio=negocio,
        anexos=anexos, aceite=aceite, cliente_id=m.cliente_id, pedido_id=m.pedido_id,
    )


def _gravar_adesao(sessao: Session, a: Adesao) -> None:
    modelo = sessao.get(AdesaoModel, a.id)
    if modelo is None:
        modelo = AdesaoModel(id=a.id)
        sessao.add(modelo)
    copiar_campos(
        modelo, interessado_id=a.interessado_id, criada_em=a.criada_em, situacao=a.situacao, cliente_id=a.cliente_id,
        pedido_id=a.pedido_id,
    )
    copiar_campos(modelo, **{f"negocio_{c}": getattr(a.negocio, c) if a.negocio else None for c in _CAMPOS_NEGOCIO})
    copiar_campos(modelo, **{f"aceite_{c}": getattr(a.aceite, c) if a.aceite else None for c in _CAMPOS_ACEITE})

    # Anexos só são acrescentados; o conteúdo (bytes) nunca é reescrito.
    guardados = {anexo.id for anexo in modelo.anexos}
    novos = [anexo for anexo in a.anexos if anexo.id not in guardados]
    primeira_ordem = proxima_ordem(sessao, AnexoModel) if novos else 0
    for deslocamento, anexo in enumerate(novos):
        modelo.anexos.append(AnexoModel(
            id=anexo.id, tipo=anexo.tipo, nome_arquivo=anexo.nome_arquivo, tamanho_bytes=anexo.tamanho_bytes,
            conteudo=anexo.conteudo, recebido_em=anexo.recebido_em, ordem_gravacao=primeira_ordem + deslocamento,
        ))
    ids = {anexo.id for anexo in a.anexos}
    for removido in [anexo for anexo in modelo.anexos if anexo.id not in ids]:
        modelo.anexos.remove(removido)


class SqlAdesaoRepository(RepositorioSql):
    def _entregar_interessado(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Interessado, modelo.id) or u.rastrear(
            _interessado_para_dominio(modelo), modelo.id, _gravar_interessado
        )

    def _entregar_adesao(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Adesao, modelo.id) or u.rastrear(_adesao_para_dominio(modelo), modelo.id, _gravar_adesao)

    def salvar_interessado(self, interessado: Interessado) -> None:
        with self._unidade() as u:
            _gravar_interessado(u.sessao, interessado)
            u.sessao.flush()
            u.rastrear(interessado, interessado.id, _gravar_interessado)

    def obter_interessado(self, interessado_id: str) -> Optional[Interessado]:
        with self._unidade() as u:
            return self._entregar_interessado(u, u.sessao.get(InteressadoModel, interessado_id))

    def interessado_por_email(self, email: str) -> Optional[Interessado]:
        with self._unidade() as u:
            consulta = select(InteressadoModel).where(func.lower(InteressadoModel.email) == email.lower())
            return self._entregar_interessado(u, u.sessao.scalars(consulta).first())

    def interessado_por_hash_token(self, hash_token: str) -> Optional[Interessado]:
        with self._unidade() as u:
            consulta = select(InteressadoModel).where(InteressadoModel.hash_token_fluxo == hash_token)
            return self._entregar_interessado(u, u.sessao.scalars(consulta).first())

    def salvar_adesao(self, adesao: Adesao) -> None:
        with self._unidade() as u:
            _gravar_adesao(u.sessao, adesao)
            u.sessao.flush()
            u.rastrear(adesao, adesao.id, _gravar_adesao)

    def obter_adesao(self, adesao_id: str) -> Optional[Adesao]:
        with self._unidade() as u:
            return self._entregar_adesao(u, u.sessao.get(AdesaoModel, adesao_id))

    def adesao_do_interessado(self, interessado_id: str) -> Optional[Adesao]:
        with self._unidade() as u:
            consulta = select(AdesaoModel).where(AdesaoModel.interessado_id == interessado_id)
            return self._entregar_adesao(u, u.sessao.scalars(consulta).first())
