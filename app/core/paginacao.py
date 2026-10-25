from dataclasses import dataclass
from typing import List, Sequence, Tuple, TypeVar

from app.core.erros import ErroApi

T = TypeVar("T")


@dataclass
class ParametrosPaginacao:
    pagina: int
    limite: int


def parametros_paginacao(pagina: int = 1, limite: int = 20) -> ParametrosPaginacao:
    detalhes = []
    if pagina < 1:
        detalhes.append({"campo": "pagina", "problema": "deve ser maior ou igual a 1"})
    if not 1 <= limite <= 100:
        detalhes.append({"campo": "limite", "problema": "deve estar entre 1 e 100"})
    if detalhes:
        raise ErroApi(400, "PARAMETRO_INVALIDO", "Os parâmetros de paginação são inválidos. Use pagina a partir de 1 e limite entre 1 e 100.", detalhes)
    return ParametrosPaginacao(pagina=pagina, limite=limite)


def paginar(itens: Sequence[T], parametros: ParametrosPaginacao) -> Tuple[List[T], int]:
    inicio = (parametros.pagina - 1) * parametros.limite
    return list(itens[inicio:inicio + parametros.limite]), len(itens)
