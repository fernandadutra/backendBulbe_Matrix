"""
Camada de Persistência, repositórios do conteúdo de boas-vindas.
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

from typing import Optional, Protocol

from sqlalchemy import select

from app.db.models import ConteudoBoasVindasModel, PassoBoasVindasModel
from app.db.repositorio_sql import RepositorioSql
from app.models.conteudo import ConteudoBoasVindas, Passo


class ConteudoRepository(Protocol):
    def obter_boas_vindas(self) -> ConteudoBoasVindas: ...


class InMemoryConteudoRepository:
    def __init__(self, boas_vindas: Optional[ConteudoBoasVindas] = None):
        self._boas_vindas = None
        if boas_vindas is not None:
            self.salvar_boas_vindas(boas_vindas)

    def obter_boas_vindas(self) -> ConteudoBoasVindas:
        return self._boas_vindas

    def salvar_boas_vindas(self, boas_vindas: ConteudoBoasVindas) -> None:
        boas_vindas.passos = sorted(boas_vindas.passos, key=lambda p: p.ordem)
        self._boas_vindas = boas_vindas


class SqlConteudoRepository(RepositorioSql):
    # Conteúdo somente leitura para os services: não precisa ser rastreado.

    def obter_boas_vindas(self) -> ConteudoBoasVindas:
        with self._unidade() as u:
            # Vale a versão mais recente (as versões são datas AAAA-MM-DD).
            consulta = select(ConteudoBoasVindasModel).order_by(ConteudoBoasVindasModel.versao.desc())
            modelo = u.sessao.scalars(consulta).first()
            if modelo is None:
                return None
            passos = [
                Passo(p.ordem, p.titulo, p.texto, p.url_ilustracao, p.texto_alternativo) for p in modelo.passos
            ]
            return ConteudoBoasVindas(versao=modelo.versao, titulo=modelo.titulo, passos=passos)

    def salvar_boas_vindas(self, boas_vindas: ConteudoBoasVindas) -> None:
        """Usado pelo seed."""
        with self._unidade() as u:
            modelo = u.sessao.get(ConteudoBoasVindasModel, boas_vindas.versao)
            if modelo is None:
                modelo = ConteudoBoasVindasModel(versao=boas_vindas.versao)
                u.sessao.add(modelo)
            modelo.titulo = boas_vindas.titulo
            modelo.passos = [
                PassoBoasVindasModel(
                    ordem=p.ordem, titulo=p.titulo, texto=p.texto, url_ilustracao=p.url_ilustracao,
                    texto_alternativo=p.texto_alternativo,
                )
                for p in boas_vindas.passos
            ]
            u.sessao.flush()
