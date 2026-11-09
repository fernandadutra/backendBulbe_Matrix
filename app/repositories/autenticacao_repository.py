"""
Camada de Persistência, repositórios de Cliente.

- AutenticacaoRepository: o CONTRATO (interface). Diz quais métodos existem.
- InMemoryAutenticacaoRepository: a versão em dicionário, útil em testes unitários.
- SqlAutenticacaoRepository: a versão com banco de dados, usada pela API.

Os services só conhecem o contrato. Por isso eles não mudam.
"""

from typing import Dict, Iterable, List, Optional, Protocol

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.models import ClienteModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.cliente import Cliente


class AutenticacaoRepository(Protocol):
    def obter(self, cliente_id: str) -> Optional[Cliente]: ...
    def obter_por_email(self, email: str) -> Optional[Cliente]: ...
    def obter_por_cpf(self, cpf: str) -> Optional[Cliente]: ...
    def listar(self) -> List[Cliente]: ...
    def salvar(self, cliente: Cliente) -> None: ...


class InMemoryAutenticacaoRepository:
    def __init__(self, clientes: Iterable[Cliente] = ()):
        self._clientes: Dict[str, Cliente] = {c.id: c for c in clientes}

    def obter(self, cliente_id: str) -> Optional[Cliente]:
        return self._clientes.get(cliente_id)

    def obter_por_email(self, email: str) -> Optional[Cliente]:
        return next((c for c in self._clientes.values() if c.email and c.email.lower() == email.lower()), None)

    def obter_por_cpf(self, cpf: str) -> Optional[Cliente]:
        return next((c for c in self._clientes.values() if c.cpf == cpf), None)

    def listar(self) -> List[Cliente]:
        return list(self._clientes.values())

    def salvar(self, cliente: Cliente) -> None:
        self._clientes[cliente.id] = cliente


def _para_dominio(m: ClienteModel) -> Cliente:
    return Cliente(id=m.id, nome=m.nome, email=m.email, cpf=m.cpf, telefone=m.telefone, senha_hash=m.senha_hash)


def _gravar(sessao: Session, c: Cliente) -> None:
    modelo = sessao.get(ClienteModel, c.id)
    if modelo is None:
        modelo = ClienteModel(id=c.id, ordem_gravacao=proxima_ordem(sessao, ClienteModel))
        sessao.add(modelo)
    copiar_campos(modelo, nome=c.nome, email=c.email, cpf=c.cpf, telefone=c.telefone, senha_hash=c.senha_hash)


class SqlAutenticacaoRepository(RepositorioSql):
    """Mesmos métodos, agora lendo e gravando no banco com SQLAlchemy."""

    def _entregar(self, unidade, modelo: Optional[ClienteModel]) -> Optional[Cliente]:
        if modelo is None:
            return None
        return unidade.obter(Cliente, modelo.id) or unidade.rastrear(_para_dominio(modelo), modelo.id, _gravar)

    def obter(self, cliente_id: str) -> Optional[Cliente]:
        with self._unidade() as u:
            return self._entregar(u, u.sessao.get(ClienteModel, cliente_id))

    def obter_por_email(self, email: str) -> Optional[Cliente]:
        with self._unidade() as u:
            # E-mail sem diferenciar maiúsculas, como na versão em memória.
            consulta = select(ClienteModel).where(func.lower(ClienteModel.email) == email.lower())
            return self._entregar(u, u.sessao.scalars(consulta).first())

    def obter_por_cpf(self, cpf: str) -> Optional[Cliente]:
        with self._unidade() as u:
            return self._entregar(u, u.sessao.scalars(select(ClienteModel).where(ClienteModel.cpf == cpf)).first())

    def listar(self) -> List[Cliente]:
        with self._unidade() as u:
            modelos = u.sessao.scalars(select(ClienteModel).order_by(ClienteModel.ordem_gravacao))
            return [self._entregar(u, m) for m in modelos]

    def salvar(self, cliente: Cliente) -> None:
        with self._unidade() as u:
            _gravar(u.sessao, cliente)
            u.sessao.flush()
            u.rastrear(cliente, cliente.id, _gravar)
