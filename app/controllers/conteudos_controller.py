from fastapi import APIRouter, Response

from app.core.estado import repositorios
from app.schemas.conteudo import BoasVindasResposta, PassoBoasVindas
from app.services import conteudo_service

router = APIRouter(prefix="/conteudos", tags=["Boas-vindas"])


def _passo(p):
    return PassoBoasVindas(
        ordem=p.ordem,
        titulo=p.titulo,
        texto=p.texto,
        url_ilustracao=p.url_ilustracao,
        texto_alternativo=p.texto_alternativo,
    )


@router.get(
    "/boas-vindas",
    response_model=BoasVindasResposta,
    summary="Obter o conteúdo da tela de boas-vindas",
    description="Público. O texto é atualizável sem nova versão do app; use versao para revalidar o conteúdo.",
)
def obter_boas_vindas(response: Response):
    conteudo = conteudo_service.obter_boas_vindas(repositorios.conteudos)
    response.headers["Cache-Control"] = "public, max-age=300"
    return BoasVindasResposta(
        versao=conteudo.versao,
        titulo=conteudo.titulo,
        passos=[_passo(p) for p in conteudo.passos],
    )
