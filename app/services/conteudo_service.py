from app.models.conteudo import ConteudoBoasVindas
from app.repositories.conteudo_repository import ConteudoRepository


def obter_boas_vindas(repositorio: ConteudoRepository) -> ConteudoBoasVindas:
    return repositorio.obter_boas_vindas()
