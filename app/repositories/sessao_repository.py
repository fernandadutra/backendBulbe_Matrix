from typing import Dict, Optional

from app.models.sessao import Sessao


class SessaoRepository:
    def __init__(self):
        self._sessoes: Dict[str, Sessao] = {}

    def salvar(self, sessao: Sessao) -> None:
        self._sessoes[sessao.id] = sessao

    def obter_por_hash(self, hash_token: str) -> Optional[Sessao]:
        # Também acha a sessão pelo hash de um token já rotacionado, para o serviço detectar o reuso.
        return next(
            (s for s in self._sessoes.values() if s.hash_token == hash_token or hash_token in s.hashes_usados), None
        )
