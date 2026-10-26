import threading
from collections import defaultdict, deque
from typing import Deque, Dict, Optional

from fastapi import Request

from app.core import config, relogio
from app.core.erros import ErroApi

JANELA_SEGUNDOS = 60

_acessos: Dict[str, Deque[float]] = defaultdict(deque)
# O FastAPI roda dependências síncronas em várias threads: a varredura do dicionário precisa de exclusão.
_trava = threading.Lock()

_acessos_login: Dict[str, Deque[float]] = defaultdict(deque)
_falhas_login: Dict[str, Deque[float]] = defaultdict(deque)


def reiniciar() -> None:
    with _trava:
        _acessos.clear()
        _acessos_login.clear()
        _falhas_login.clear()


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


def limitar_login_por_ip(request: Request) -> None:
    ip = request.client.host if request.client else "desconhecido"
    with _trava:
        agora = relogio.agora().timestamp()
        fila = _acessos_login[ip]
        while fila and agora - fila[0] >= JANELA_SEGUNDOS:
            fila.popleft()
        if len(fila) >= config.LIMITE_LOGIN_POR_IP_POR_MINUTO:
            espera = max(1, int(JANELA_SEGUNDOS - (agora - fila[0])) + 1)
            raise ErroApi(
                429,
                "LIMITE_DE_TENTATIVAS",
                f"Você fez muitas tentativas de entrada em pouco tempo. Aguarde {espera} segundos e tente de novo.",
                cabecalhos={"Retry-After": str(espera)},
            )
        fila.append(agora)


def falhas_de_login_excedidas(identificador: str) -> Optional[int]:
    """Segundos até a falha mais antiga sair da janela, ou None se o identificador ainda pode tentar."""
    with _trava:
        agora = relogio.agora().timestamp()
        fila = _falhas_login[identificador]
        while fila and agora - fila[0] >= config.JANELA_FALHAS_LOGIN_SEGUNDOS:
            fila.popleft()
        if len(fila) < config.LIMITE_FALHAS_LOGIN:
            return None
        return max(1, int(config.JANELA_FALHAS_LOGIN_SEGUNDOS - (agora - fila[0])) + 1)


def registrar_falha_de_login(identificador: str) -> None:
    with _trava:
        _falhas_login[identificador].append(relogio.agora().timestamp())


def limpar_falhas_de_login(identificador: str) -> None:
    with _trava:
        _falhas_login.pop(identificador, None)
