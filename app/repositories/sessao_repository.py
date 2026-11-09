"""
Camada de Persistência, repositórios de Sessão (tokens de renovação).
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

from typing import Dict, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import HashTokenUsadoModel, SessaoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos
from app.models.sessao import Sessao


class SessaoRepository(Protocol):
    def salvar(self, sessao: Sessao) -> None: ...
    def obter_por_hash(self, hash_token: str) -> Optional[Sessao]: ...


class InMemorySessaoRepository:
    def __init__(self):
        self._sessoes: Dict[str, Sessao] = {}

    def salvar(self, sessao: Sessao) -> None:
        self._sessoes[sessao.id] = sessao

    def obter_por_hash(self, hash_token: str) -> Optional[Sessao]:
        # Também acha a sessão pelo hash de um token já rotacionado, para o serviço detectar o reuso.
        return next(
            (s for s in self._sessoes.values() if s.hash_token == hash_token or hash_token in s.hashes_usados), None
        )


def _para_dominio(m: SessaoModel) -> Sessao:
    return Sessao(
        id=m.id, cliente_id=m.cliente_id, criada_em=m.criada_em, expira_em=m.expira_em, hash_token=m.hash_token,
        hashes_usados={h.hash for h in m.hashes_usados}, revogada=m.revogada,
    )


def _gravar(sessao_db: Session, s: Sessao) -> None:
    modelo = sessao_db.get(SessaoModel, s.id)
    if modelo is None:
        modelo = SessaoModel(id=s.id)
        sessao_db.add(modelo)
    copiar_campos(
        modelo, cliente_id=s.cliente_id, criada_em=s.criada_em, expira_em=s.expira_em, hash_token=s.hash_token,
        revogada=s.revogada,
    )
    guardados = {h.hash for h in modelo.hashes_usados}
    for novo in s.hashes_usados - guardados:
        modelo.hashes_usados.append(HashTokenUsadoModel(hash=novo))
    for h in [h for h in modelo.hashes_usados if h.hash not in s.hashes_usados]:
        modelo.hashes_usados.remove(h)


class SqlSessaoRepository(RepositorioSql):
    def salvar(self, sessao: Sessao) -> None:
        with self._unidade() as u:
            _gravar(u.sessao, sessao)
            u.sessao.flush()
            u.rastrear(sessao, sessao.id, _gravar)

    def obter_por_hash(self, hash_token: str) -> Optional[Sessao]:
        # Também acha a sessão pelo hash de um token já rotacionado, para o serviço detectar o reuso.
        with self._unidade() as u:
            modelo = u.sessao.scalars(select(SessaoModel).where(SessaoModel.hash_token == hash_token)).first()
            if modelo is None:
                usado = u.sessao.get(HashTokenUsadoModel, hash_token)
                modelo = usado.sessao if usado else None
            if modelo is None:
                return None
            return u.obter(Sessao, modelo.id) or u.rastrear(_para_dominio(modelo), modelo.id, _gravar)
