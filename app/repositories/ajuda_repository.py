from typing import Iterable, List, Optional

from app.models.dica import Dica


class AjudaRepository:
    def __init__(self, dicas: Iterable[Dica]):
        self._dicas = list(dicas)

    def listar(self, tela: str, elemento: Optional[str] = None) -> List[Dica]:
        return [d for d in self._dicas if d.tela == tela and (elemento is None or d.elemento == elemento)]
