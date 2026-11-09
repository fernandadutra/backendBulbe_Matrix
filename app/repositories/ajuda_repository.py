"""
Camada de Persistência, repositórios dos textos de ajuda (dicas).
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.

Os blocos de cada dica (parágrafos e listas) ficam numa coluna JSON.
"""

from typing import Any, Dict, Iterable, List, Optional, Protocol

from sqlalchemy import select

from app.db.models import DicaModel
from app.db.repositorio_sql import RepositorioSql
from app.models.dica import Bloco, BlocoLista, BlocoParagrafo, Dica, ItemLista


class AjudaRepository(Protocol):
    def listar(self, tela: str, elemento: Optional[str] = None) -> List[Dica]: ...


class InMemoryAjudaRepository:
    def __init__(self, dicas: Iterable[Dica] = ()):
        self._dicas = list(dicas)

    def listar(self, tela: str, elemento: Optional[str] = None) -> List[Dica]:
        return [d for d in self._dicas if d.tela == tela and (elemento is None or d.elemento == elemento)]

    def salvar(self, dica: Dica) -> None:
        self._dicas.append(dica)


def _bloco_para_json(bloco: Bloco) -> Dict[str, Any]:
    if isinstance(bloco, BlocoLista):
        itens = [{"texto": i.texto, "titulo": i.titulo} for i in bloco.itens]
        return {"tipo": "lista", "ordenada": bloco.ordenada, "itens": itens}
    return {"tipo": "paragrafo", "texto": bloco.texto, "titulo": bloco.titulo}


def _bloco_do_json(dados: Dict[str, Any]) -> Bloco:
    if dados["tipo"] == "lista":
        return BlocoLista([ItemLista(i["texto"], i["titulo"]) for i in dados["itens"]], dados["ordenada"])
    return BlocoParagrafo(dados["texto"], dados["titulo"])


def _para_dominio(m: DicaModel) -> Dica:
    return Dica(
        tela=m.tela, elemento=m.elemento, titulo=m.titulo, rotulo_acessivel=m.rotulo_acessivel,
        atualizado_em=m.atualizado_em, blocos=[_bloco_do_json(b) for b in m.blocos],
    )


class SqlAjudaRepository(RepositorioSql):
    # Dicas são conteúdo somente leitura para os services: não precisam ser rastreadas.

    def listar(self, tela: str, elemento: Optional[str] = None) -> List[Dica]:
        with self._unidade() as u:
            consulta = select(DicaModel).where(DicaModel.tela == tela).order_by(DicaModel.id)
            if elemento is not None:
                consulta = consulta.where(DicaModel.elemento == elemento)
            return [_para_dominio(m) for m in u.sessao.scalars(consulta)]

    def salvar(self, dica: Dica) -> None:
        """Usado pelo seed."""
        with self._unidade() as u:
            consulta = select(DicaModel).where(DicaModel.tela == dica.tela, DicaModel.elemento == dica.elemento)
            modelo = u.sessao.scalars(consulta).first()
            if modelo is None:
                modelo = DicaModel(tela=dica.tela, elemento=dica.elemento)
                u.sessao.add(modelo)
            modelo.titulo = dica.titulo
            modelo.rotulo_acessivel = dica.rotulo_acessivel
            modelo.atualizado_em = dica.atualizado_em
            modelo.blocos = [_bloco_para_json(b) for b in dica.blocos]
            u.sessao.flush()
