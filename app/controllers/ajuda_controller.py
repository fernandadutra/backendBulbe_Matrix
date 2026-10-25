from typing import Optional

from fastapi import APIRouter, Query, Response

from app.core.estado import repositorios
from app.models import dica as modelo
from app.schemas.comum import respostas_de_erro
from app.schemas.dica import BlocoLista, BlocoParagrafo, Dica, ItemLista, RespostaDicas
from app.services import ajuda_service

router = APIRouter(prefix="/ajuda", tags=["Ajuda"])


def _bloco(b):
    if isinstance(b, modelo.BlocoLista):
        return BlocoLista(ordenada=b.ordenada, itens=[ItemLista(titulo=i.titulo, texto=i.texto) for i in b.itens])
    return BlocoParagrafo(titulo=b.titulo, texto=b.texto)


@router.get(
    "/dicas",
    response_model=RespostaDicas,
    summary="Obter dicas de ajuda de uma tela",
    description="Público. Lista vazia significa que a tela não tem ajuda e o botão deve ficar escondido.",
    responses=respostas_de_erro(400),
)
def listar_dicas(
    response: Response,
    tela: Optional[str] = Query(
        default=None,
        description="Obrigatório. Chave da tela.",
        json_schema_extra={"enum": list(modelo.TELAS_COM_AJUDA)},
    ),
    elemento: Optional[str] = Query(default=None, description="Filtra pelo campo ou componente da tela."),
):
    dicas, atualizado_em = ajuda_service.listar_dicas(tela, elemento, repositorios.ajuda)
    response.headers["Cache-Control"] = "public, max-age=300"
    return RespostaDicas(
        tela=tela,
        atualizado_em=atualizado_em,
        dicas=[
            Dica(
                elemento=d.elemento,
                titulo=d.titulo,
                rotulo_acessivel=d.rotulo_acessivel,
                blocos=[_bloco(b) for b in d.blocos],
            )
            for d in dicas
        ],
    )
