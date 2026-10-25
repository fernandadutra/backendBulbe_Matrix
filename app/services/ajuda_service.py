from datetime import datetime
from typing import List, Optional, Tuple

from app.core.erros import ErroApi
from app.models.dica import TELAS_COM_AJUDA, Dica
from app.repositories.ajuda_repository import AjudaRepository


def listar_dicas(
    tela: Optional[str], elemento: Optional[str], repositorio: AjudaRepository
) -> Tuple[List[Dica], Optional[datetime]]:
    if tela not in TELAS_COM_AJUDA:
        problema = "campo obrigatório" if tela is None else "tela desconhecida"
        raise ErroApi(
            400,
            "PARAMETRO_INVALIDO",
            "Informe uma tela válida: " + ", ".join(TELAS_COM_AJUDA) + ".",
            [{"campo": "tela", "problema": problema}],
        )
    dicas = repositorio.listar(tela, elemento)
    atualizado_em = max((d.atualizado_em for d in dicas), default=None)
    return dicas, atualizado_em
