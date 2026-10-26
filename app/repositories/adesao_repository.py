from typing import Dict, Optional

from app.models.adesao import Adesao, Interessado


class AdesaoRepository:
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
