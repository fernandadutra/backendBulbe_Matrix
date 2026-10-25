import threading
from collections import defaultdict, deque
from typing import Deque, Dict

from fastapi import Request

from app.core import config, relogio
from app.core.erros import ErroApi

JANELA_SEGUNDOS = 60

_acessos: Dict[str, Deque[float]] = defaultdict(deque)
# O FastAPI roda dependências síncronas em várias threads: a varredura do dicionário precisa de exclusão.
_trava = threading.Lock()


def reiniciar() -> None:
    with _trava:
        _acessos.clear()


def limitar_simulacoes(request: Request) -> None:
    ip = request.client.host if request.client else "desconhecido"
    with _trava:
        agora = relogio.agora().timestamp()
        # Descarta todo IP cuja última requisição já saiu da janela, para o dicionário não crescer sem limite.
        for outro in [chave for chave, f in _acessos.items() if not f or agora - f[-1] >= JANELA_SEGUNDOS]:
            del _acessos[outro]
        fila = _acessos[ip]
        while fila and agora - fila[0] >= JANELA_SEGUNDOS:
            fila.popleft()
        if len(fila) >= config.LIMITE_SIMULACOES_POR_MINUTO:
            espera = max(1, int(JANELA_SEGUNDOS - (agora - fila[0])) + 1)
            raise ErroApi(
                429,
                "LIMITE_DE_REQUISICOES",
                f"Você fez muitas simulações em pouco tempo. Aguarde {espera} segundos e tente de novo.",
                cabecalhos={"Retry-After": str(espera)},
            )
        fila.append(agora)
