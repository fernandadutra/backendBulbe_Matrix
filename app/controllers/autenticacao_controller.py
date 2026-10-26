from fastapi import APIRouter, Depends, Response, status

from app.core import config
from app.core.estado import repositorios
from app.core.limite_requisicoes import limitar_login_por_ip
from app.core.seguranca import emitir_token, obter_cliente_atual
from app.models.cliente import Cliente
from app.schemas.autenticacao import (
    ClienteSessao,
    InstalacaoPerfil,
    Perfil,
    SessaoRequisicao,
    SessaoResposta,
    TokenRenovacaoRequisicao,
)
from app.schemas.comum import respostas_de_erro
from app.services import autenticacao_service
from app.services.autenticacao_service import SessaoEmitida

router = APIRouter(tags=["Autenticação"])


def _para_resposta(sessao: SessaoEmitida) -> SessaoResposta:
    cliente = sessao.cliente
    return SessaoResposta(
        token_acesso=emitir_token(cliente.id),
        tipo_token="Bearer",
        expira_em_segundos=config.MINUTOS_TOKEN_ACESSO * 60,
        token_renovacao=sessao.token_renovacao,
        cliente=ClienteSessao(
            id=cliente.id,
            nome=cliente.nome,
            possui_pedido_em_andamento=sessao.possui_pedido_em_andamento,
            # Faturas só existem no Bloco 2: até lá, nenhum cliente tem fatura emitida.
            possui_fatura_emitida=False,
        ),
    )


@router.post(
    "/sessoes",
    response_model=SessaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Autenticar o cliente",
    description="Público. Aceita e-mail ou CPF como identificador.",
    responses=respostas_de_erro(400, 401, 429),
    dependencies=[Depends(limitar_login_por_ip)],
)
def criar_sessao(dados: SessaoRequisicao):
    sessao = autenticacao_service.autenticar(
        dados.identificador, dados.senha, repositorios.clientes, repositorios.sessoes, repositorios.pedidos
    )
    return _para_resposta(sessao)


@router.post(
    "/sessoes/renovacao",
    response_model=SessaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Renovar o token de acesso",
    description="Público, autorizado pelo token de renovação. O token de renovação devolvido substitui o enviado.",
    responses=respostas_de_erro(400, 401),
)
def renovar_sessao(dados: TokenRenovacaoRequisicao):
    sessao = autenticacao_service.renovar_sessao(
        dados.token_renovacao, repositorios.clientes, repositorios.sessoes, repositorios.pedidos
    )
    return _para_resposta(sessao)


@router.delete(
    "/sessoes",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Encerrar a sessão",
    description="Invalida o token de renovação. O token de acesso segue válido até expirar.",
    responses=respostas_de_erro(400, 401),
)
def encerrar_sessao(dados: TokenRenovacaoRequisicao, cliente: Cliente = Depends(obter_cliente_atual)):
    autenticacao_service.encerrar_sessao(dados.token_renovacao, cliente, repositorios.sessoes)
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get(
    "/perfil",
    response_model=Perfil,
    summary="Obter perfil e instalações do cliente",
    responses=respostas_de_erro(401),
)
def obter_perfil(cliente: Cliente = Depends(obter_cliente_atual)):
    instalacoes = autenticacao_service.montar_perfil(cliente, repositorios.pedidos)
    return Perfil(
        id=cliente.id,
        nome=cliente.nome,
        email=cliente.email,
        telefone=cliente.telefone,
        instalacoes=[
            InstalacaoPerfil(
                numero=i.pedido.numero_instalacao,
                distribuidora=i.pedido.distribuidora,
                pedido_id=i.pedido.id,
                principal=i.principal,
            )
            for i in instalacoes
        ],
    )
