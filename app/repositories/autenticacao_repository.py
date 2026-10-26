from typing import Dict, Iterable, List, Optional

from app.models.cliente import Cliente


class AutenticacaoRepository:
    def __init__(self, clientes: Iterable[Cliente]):
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
