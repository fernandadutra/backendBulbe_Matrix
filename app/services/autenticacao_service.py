from typing import Optional

import jwt

from app.core import config, relogio
from app.models.cliente import Cliente
from app.repositories.autenticacao_repository import AutenticacaoRepository


def cliente_do_token(token: str, repositorio: AutenticacaoRepository) -> Optional[Cliente]:
    """Devolve o cliente dono do token, ou None se o token for inválido, expirado ou de cliente inexistente."""
    try:
        claims = jwt.decode(
            token,
            config.JWT_SEGREDO,
            algorithms=[config.JWT_ALGORITMO],
            # A expiração é conferida abaixo com o relógio da aplicação, não o do sistema.
            options={"require": ["sub", "exp"], "verify_exp": False, "verify_iat": False},
        )
    except jwt.PyJWTError:
        return None
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or exp <= relogio.agora().timestamp():
        return None
    sub = claims.get("sub")
    if not isinstance(sub, str):
        return None
    return repositorio.obter(sub)
