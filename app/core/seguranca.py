from datetime import timedelta
from typing import Optional

import jwt
from fastapi import Depends, Request
from fastapi.security import HTTPBearer

from app.core import config, relogio
from app.core.erros import ErroApi
from app.core.estado import repositorios
from app.models.cliente import Cliente
from app.services import autenticacao_service

# Só alimenta o cadeado do Swagger. A leitura do cabeçalho é feita à mão abaixo.
_esquema_bearer = HTTPBearer(auto_error=False, description="Token JWT no formato `Bearer <token>`.")

_CABECALHO_401 = {"WWW-Authenticate": "Bearer"}


def emitir_token(cliente_id: str, minutos: int = config.MINUTOS_TOKEN_ACESSO) -> str:
    agora = relogio.agora()
    claims = {
        "sub": cliente_id,
        "iat": int(agora.timestamp()),
        "exp": int((agora + timedelta(minutes=minutos)).timestamp()),
    }
    return jwt.encode(claims, config.JWT_SEGREDO, algorithm=config.JWT_ALGORITMO)


def _token_invalido() -> ErroApi:
    return ErroApi(401, "TOKEN_INVALIDO", "Sua sessão expirou ou é inválida. Entre de novo para continuar.", cabecalhos=_CABECALHO_401)


def _extrair_token(request: Request) -> Optional[str]:
    cabecalho = request.headers.get("authorization")
    if cabecalho is None:
        return None
    esquema, _, token = cabecalho.partition(" ")
    if esquema.lower() != "bearer" or not token.strip():
        raise _token_invalido()
    return token.strip()


def _cliente_do_token(token: str) -> Cliente:
    cliente = autenticacao_service.cliente_do_token(token, repositorios.clientes)
    if cliente is None:
        raise _token_invalido()
    return cliente


def obter_cliente_atual(request: Request, _credenciais=Depends(_esquema_bearer)) -> Cliente:
    token = _extrair_token(request)
    if token is None:
        raise ErroApi(401, "TOKEN_AUSENTE", "Você precisa entrar para acessar este recurso.", cabecalhos=_CABECALHO_401)
    return _cliente_do_token(token)


def obter_cliente_opcional(request: Request, _credenciais=Depends(_esquema_bearer)) -> Optional[Cliente]:
    token = _extrair_token(request)
    if token is None:
        return None
    return _cliente_do_token(token)
