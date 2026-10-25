import threading
from typing import Dict, Iterable, List, Optional, Tuple

from app.models.beneficio import Beneficio, Parceiro, Trilha
from app.models.resgate import Resgate


class BeneficioRepository:
    def __init__(
        self,
        parceiros: Iterable[Parceiro],
        trilhas: Iterable[Trilha],
        beneficios: Iterable[Beneficio],
    ):
        self._parceiros: Dict[str, Parceiro] = {p.id: p for p in parceiros}
        self._trilhas: List[Trilha] = list(trilhas)
        self._beneficios: Dict[str, Beneficio] = {b.id: b for b in beneficios}
        self._resgates: List[Resgate] = []
        self._chaves: Dict[Tuple[str, str], str] = {}
        # Quem decide um resgate segura a trava do começo das checagens até salvar_resgate.
        self.trava = threading.Lock()

    def listar_trilhas(self) -> List[Trilha]:
        return list(self._trilhas)

    def obter_parceiro(self, parceiro_id: str) -> Parceiro:
        return self._parceiros[parceiro_id]

    def listar_beneficios(self) -> List[Beneficio]:
        return list(self._beneficios.values())

    def obter_beneficio(self, beneficio_id: str) -> Optional[Beneficio]:
        return self._beneficios.get(beneficio_id)

    def resgate_por_chave(self, cliente_id: str, chave: str) -> Optional[Resgate]:
        resgate_id = self._chaves.get((cliente_id, chave))
        return next((r for r in self._resgates if r.id == resgate_id), None) if resgate_id else None

    def cliente_ja_resgatou(self, cliente_id: str, beneficio_id: str) -> bool:
        return any(r.cliente_id == cliente_id and r.beneficio_id == beneficio_id for r in self._resgates)

    def salvar_resgate(self, resgate: Resgate) -> None:
        """Grava resgate, contador e chave juntos. Chamar com a trava já tomada."""
        beneficio = self._beneficios[resgate.beneficio_id]
        chave = (resgate.cliente_id, resgate.chave_idempotencia)
        self._resgates.append(resgate)
        try:
            beneficio.total_resgates += 1
            self._chaves[chave] = resgate.id
        except Exception:
            self._resgates.remove(resgate)
            beneficio.total_resgates = max(0, beneficio.total_resgates - 1)
            self._chaves.pop(chave, None)
            raise

    def listar_resgates_por_cliente(self, cliente_id: str) -> List[Resgate]:
        # Mais recentes primeiro. Em empate de horário, vale a ordem de gravação.
        do_cliente = [r for r in reversed(self._resgates) if r.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda r: r.resgatado_em, reverse=True)
