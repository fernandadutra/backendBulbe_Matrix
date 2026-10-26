import logging
import os

_SEGREDO_PADRAO = "segredo-de-desenvolvimento-troque-em-producao"

USANDO_SEGREDO_PADRAO = not os.getenv("BULBE_JWT_SEGREDO")
JWT_SEGREDO = os.getenv("BULBE_JWT_SEGREDO") or _SEGREDO_PADRAO
JWT_ALGORITMO = "HS256"
LIMITE_SIMULACOES_POR_MINUTO = int(os.getenv("BULBE_LIMITE_SIMULACOES_POR_MINUTO", "30"))
MINUTOS_TOKEN_ACESSO = int(os.getenv("BULBE_MINUTOS_TOKEN_ACESSO", "15"))
DIAS_TOKEN_RENOVACAO = int(os.getenv("BULBE_DIAS_TOKEN_RENOVACAO", "30"))
LIMITE_FALHAS_LOGIN = int(os.getenv("BULBE_LIMITE_FALHAS_LOGIN", "5"))
JANELA_FALHAS_LOGIN_SEGUNDOS = int(os.getenv("BULBE_JANELA_FALHAS_LOGIN_SEGUNDOS", "900"))
LIMITE_LOGIN_POR_IP_POR_MINUTO = int(os.getenv("BULBE_LIMITE_LOGIN_POR_IP_POR_MINUTO", "20"))

if USANDO_SEGREDO_PADRAO:
    logging.getLogger("bulbe").warning(
        "BULBE_JWT_SEGREDO não está definida: usando o segredo padrão, que serve só para desenvolvimento. "
        "Em produção a variável é obrigatória."
    )
