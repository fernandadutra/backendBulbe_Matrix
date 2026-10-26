import logging
from typing import Any, Dict, List, Optional

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

logger = logging.getLogger("bulbe")


class ErroApi(Exception):
    def __init__(
        self,
        status_code: int,
        codigo: str,
        mensagem: str,
        detalhes: Optional[List[Dict[str, str]]] = None,
        cabecalhos: Optional[Dict[str, str]] = None,
    ):
        super().__init__(mensagem)
        self.status_code = status_code
        self.codigo = codigo
        self.mensagem = mensagem
        self.detalhes = detalhes
        self.cabecalhos = cabecalhos


def _resposta(
    status_code: int,
    codigo: str,
    mensagem: str,
    detalhes: Optional[List[Dict[str, str]]] = None,
    cabecalhos: Optional[Dict[str, str]] = None,
) -> JSONResponse:
    # O envelope sempre traz a chave detalhes, nula fora de erro de validação.
    corpo: Dict[str, Any] = {"erro": {"codigo": codigo, "mensagem": mensagem, "detalhes": detalhes}}
    return JSONResponse(status_code=status_code, content=corpo, headers=cabecalhos)


_PROBLEMAS = {
    "missing": "campo obrigatório",
    "int_parsing": "deve ser um número inteiro",
    "int_from_float": "deve ser um número inteiro, sem casas decimais",
    "int_type": "deve ser um número inteiro",
    "string_type": "deve ser um texto",
    "bool_type": "deve ser true ou false",
    "bool_parsing": "deve ser true ou false",
    "json_invalid": "JSON malformado",
    "model_attributes_type": "o corpo deve ser um objeto JSON",
    "dict_type": "o corpo deve ser um objeto JSON",
}


def _problema(erro: Dict[str, Any]) -> str:
    return _PROBLEMAS.get(erro.get("type", ""), "valor inválido")


def _tratar_erro_api(_: Request, exc: ErroApi) -> JSONResponse:
    return _resposta(exc.status_code, exc.codigo, exc.mensagem, exc.detalhes, exc.cabecalhos)


def _tratar_validacao(_: Request, exc: RequestValidationError) -> JSONResponse:
    erros = exc.errors()
    detalhes = []
    for erro in erros:
        caminho = [str(p) for p in erro["loc"][1:]]
        detalhes.append({"campo": ".".join(caminho) or erro["loc"][0], "problema": _problema(erro)})
    veio_do_corpo = any(erro["loc"] and erro["loc"][0] == "body" for erro in erros)
    if veio_do_corpo:
        return _resposta(400, "CORPO_INVALIDO", "O corpo da requisição é inválido. Corrija os campos indicados e tente de novo.", detalhes)
    return _resposta(400, "PARAMETRO_INVALIDO", "Um parâmetro da requisição é inválido. Corrija os campos indicados e tente de novo.", detalhes)


def _tratar_http(_: Request, exc: StarletteHTTPException) -> JSONResponse:
    if exc.status_code == 404:
        return _resposta(404, "ROTA_NAO_ENCONTRADA", "Esse endereço não existe. Confira a URL e tente de novo.")
    if exc.status_code == 405:
        return _resposta(405, "METODO_NAO_PERMITIDO", "Esse método não é permitido neste endereço. Confira a documentação da API.", cabecalhos=dict(exc.headers or {}))
    return _resposta(exc.status_code, "ERRO_HTTP", str(exc.detail), cabecalhos=dict(exc.headers or {}))


def _tratar_excecao(_: Request, exc: Exception) -> JSONResponse:
    logger.exception("Erro inesperado", exc_info=exc)
    return _resposta(500, "ERRO_INTERNO", "Algo deu errado do nosso lado. Tente de novo em instantes.")


def registrar_tratadores(app: FastAPI) -> None:
    app.add_exception_handler(ErroApi, _tratar_erro_api)
    app.add_exception_handler(RequestValidationError, _tratar_validacao)
    app.add_exception_handler(StarletteHTTPException, _tratar_http)
    app.add_exception_handler(Exception, _tratar_excecao)
