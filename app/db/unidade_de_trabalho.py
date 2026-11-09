"""
Unidade de trabalho (Unit of Work): uma sessão do banco por requisição.

Por que existe
--------------
Os services foram escritos contra repositórios em memória. Neles, quem recebe
um objeto do repositório pode alterá-lo direto (``sessao.revogada = True``,
``notificacao.lida = True``, ``adesao.anexos.append(...)``) e a mudança "fica
gravada", porque o objeto É o dado guardado.

Com banco isso deixa de ser verdade: o objeto do domínio é uma cópia da linha.
Para não mexer em nenhum service, os repositórios SQL registram aqui cada objeto
que entregam (``rastrear``). No fim da requisição, a unidade copia de volta para o
banco o estado de todos eles e faz um único commit. Se a requisição quebrar com
erro inesperado, nada é gravado (rollback).

Bônus: dentro da mesma requisição, buscar duas vezes o mesmo registro devolve o
mesmo objeto (mapa de identidade), exatamente como na versão em memória.

Fora de uma requisição (seed, testes, terminal Python), cada chamada de
repositório abre e confirma a sua própria unidade. Para alterar objetos fora de
uma requisição e gravar as alterações, use ``with unidade_de_trabalho(): ...``.
"""

from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Callable, Dict, Iterator, Optional, Tuple

from sqlalchemy import event
from sqlalchemy.orm import Session, sessionmaker

Gravar = Callable[[Session, Any], None]

_atual: ContextVar[Optional["UnidadeDeTrabalho"]] = ContextVar("unidade_de_trabalho", default=None)


class UnidadeDeTrabalho:
    def __init__(self, fabrica: sessionmaker) -> None:
        self.sessao: Session = fabrica()
        self._rastreados: Dict[Tuple[type, Any], Tuple[Any, Gravar]] = {}
        # O mapa de identidade do SQLAlchemy guarda referências fracas: uma linha
        # carregada e não alterada pode ser descartada e, aí, cada session.get()
        # volta ao banco. A unidade vive uma requisição só, então seguramos as linhas.
        self._linhas: set = set()
        event.listen(self.sessao, "loaded_as_persistent", self._segurar)
        event.listen(self.sessao, "pending_to_persistent", self._segurar)

    def _segurar(self, _sessao: Session, linha: Any) -> None:
        self._linhas.add(linha)

    def obter(self, tipo: type, chave: Any) -> Any:
        """Devolve o objeto do domínio já entregue nesta unidade, se houver."""
        par = self._rastreados.get((tipo, chave))
        return par[0] if par else None

    def rastrear(self, objeto: Any, chave: Any, gravar: Gravar) -> Any:
        """Passa a acompanhar o objeto; no fim, ``gravar(sessao, objeto)`` leva o estado dele ao banco."""
        par = self._rastreados.setdefault((type(objeto), chave), (objeto, gravar))
        return par[0]

    def sincronizar(self) -> None:
        """Copia para a sessão o estado atual dos objetos rastreados e envia ao banco (sem commit).

        Os repositórios chamam antes de toda consulta, para que um filtro no banco
        enxergue o que o service já alterou na memória.
        """
        for objeto, gravar in list(self._rastreados.values()):
            gravar(self.sessao, objeto)
        self.sessao.flush()

    def confirmar(self) -> None:
        self.sincronizar()
        self.sessao.commit()

    def descartar(self) -> None:
        self.sessao.rollback()
        self._rastreados.clear()
        self._linhas.clear()

    def fechar(self) -> None:
        self.sessao.close()
        self._linhas.clear()


def unidade_atual() -> Optional[UnidadeDeTrabalho]:
    return _atual.get()


@contextmanager
def unidade_de_trabalho(fabrica: Optional[sessionmaker] = None) -> Iterator[UnidadeDeTrabalho]:
    """Entra na unidade em andamento ou abre uma nova, confirmada ao sair do bloco."""
    existente = _atual.get()
    if existente is not None:
        yield existente
        return
    if fabrica is None:
        from app.db.database import SessionLocal

        fabrica = SessionLocal
    unidade = UnidadeDeTrabalho(fabrica)
    marcador = _atual.set(unidade)
    try:
        yield unidade
        unidade.confirmar()
    except BaseException:
        unidade.descartar()
        raise
    finally:
        unidade.fechar()
        _atual.reset(marcador)


class UnidadeDeTrabalhoMiddleware:
    """Abre uma unidade de trabalho por requisição HTTP.

    O commit acontece logo antes de a resposta começar a ser enviada. Assim:
    - respostas de erro de negócio (401, 404, 409...) também gravam o que o
      service alterou, como na versão em memória (ex.: revogar a sessão quando
      um token de renovação é reutilizado);
    - o cliente nunca recebe "201 Created" de algo que ainda não está no banco;
    - se o commit falhar, a exceção vira 500 e nada fica gravado.
    """

    def __init__(self, app, fabrica: Optional[sessionmaker] = None) -> None:
        self.app = app
        self.fabrica = fabrica

    async def __call__(self, scope, receive, send) -> None:
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        with unidade_de_trabalho(self.fabrica) as unidade:
            confirmada = False

            async def enviar(mensagem) -> None:
                nonlocal confirmada
                if mensagem["type"] == "http.response.start" and not confirmada:
                    confirmada = True
                    unidade.confirmar()
                await send(mensagem)

            await self.app(scope, receive, enviar)
