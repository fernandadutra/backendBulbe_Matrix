from fastapi import APIRouter, Depends, File, Form, Request, UploadFile, status

from app.core.estado import repositorios
from app.core.seguranca import obter_interessado_do_fluxo
from app.models.adesao import Adesao, Interessado
from app.schemas.adesao import (
    AceiteRequisicao,
    AdesaoRequisicao,
    AdesaoResposta,
    AnexoResposta,
    EtapaRequisicao,
    InteressadoRequisicao,
    InteressadoResposta,
    SubmissaoRequisicao,
    SubmissaoResposta,
)
from app.schemas.comum import respostas_de_erro
from app.schemas.pedido import PrazoEstimado
from app.services import adesao_service, interessado_service, pedido_service

router = APIRouter(tags=["Adesão"])


def _adesao(adesao: Adesao) -> AdesaoResposta:
    andamento = adesao_service.progresso(adesao)
    return AdesaoResposta(
        id=adesao.id,
        situacao=adesao.situacao,
        etapa_atual=andamento.etapa_atual,
        etapas_concluidas=andamento.concluidas,
        etapas_pendentes=andamento.pendentes,
    )


@router.post(
    "/interessados",
    response_model=InteressadoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar o interessado",
    description="Público. Devolve o `token_fluxo` que autoriza as rotas de adesão.",
    responses=respostas_de_erro(400, 409),
)
def registrar_interessado(dados: InteressadoRequisicao):
    registrado = interessado_service.registrar_interessado(
        dados.nome,
        dados.email,
        dados.whatsapp,
        dados.simulacao_id,
        dados.aceite_comunicacoes,
        repositorios.adesoes,
        repositorios.clientes,
        repositorios.simulacoes,
    )
    interessado = registrado.interessado
    return InteressadoResposta(
        id=interessado.id,
        situacao=interessado.situacao,
        token_fluxo=registrado.token_fluxo,
        expira_em=interessado.token_expira_em,
    )


@router.post(
    "/adesoes",
    response_model=AdesaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Abrir a adesão",
    description="Autorizado pelo token de fluxo. Se o interessado já tem adesão, devolve a existente.",
    responses=respostas_de_erro(400, 401, 404),
)
def abrir_adesao(dados: AdesaoRequisicao, interessado: Interessado = Depends(obter_interessado_do_fluxo)):
    return _adesao(adesao_service.abrir_adesao(dados.interessado_id, interessado, repositorios.adesoes))


@router.patch(
    "/adesoes/{id}",
    response_model=AdesaoResposta,
    summary="Salvar o progresso de uma etapa",
    description="Aceita as etapas `contato` e `negocio`. Termos e confirmação têm rotas próprias.",
    responses=respostas_de_erro(400, 401, 404, 409, 422),
)
def salvar_etapa(id: str, dados: EtapaRequisicao, interessado: Interessado = Depends(obter_interessado_do_fluxo)):
    adesao = adesao_service.salvar_etapa(id, interessado, dados.etapa, dados.dados, repositorios.adesoes)
    return _adesao(adesao)


@router.post(
    "/adesoes/{id}/anexos",
    response_model=AnexoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Enviar a fatura de energia",
    description="`multipart/form-data`. Aceita PDF, JPG e PNG de até 10 MB, conferidos pelo conteúdo.",
    responses=respostas_de_erro(400, 401, 404, 409, 413, 415, 422),
)
def enviar_anexo(
    id: str,
    arquivo: UploadFile = File(...),
    tipo: str = Form(..., examples=["fatura_energia"]),
    interessado: Interessado = Depends(obter_interessado_do_fluxo),
):
    # Lê um byte além do limite: basta para o service recusar sem carregar o arquivo inteiro.
    conteudo = arquivo.file.read(adesao_service.TAMANHO_MAXIMO_ANEXO_BYTES + 1)
    anexo = adesao_service.receber_anexo(id, interessado, tipo, arquivo.filename, conteudo, repositorios.adesoes)
    return AnexoResposta(
        id=anexo.id,
        tipo=anexo.tipo,
        nome_arquivo=anexo.nome_arquivo,
        tamanho_bytes=anexo.tamanho_bytes,
        situacao="recebido",
        recebido_em=anexo.recebido_em,
    )


@router.post(
    "/adesoes/{id}/aceites",
    response_model=AdesaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Registrar o aceite dos termos",
    description="Guarda também o IP e o user agent da requisição, para auditoria do consentimento.",
    responses=respostas_de_erro(400, 401, 404, 409, 422),
)
def registrar_aceite(
    id: str,
    dados: AceiteRequisicao,
    request: Request,
    interessado: Interessado = Depends(obter_interessado_do_fluxo),
):
    ip = request.client.host if request.client else "desconhecido"
    adesao = adesao_service.registrar_aceite(
        id,
        interessado,
        dados.aceite_termo_adesao,
        dados.aceite_politica_privacidade,
        dados.versao_documentos,
        dados.aceito_em,
        ip,
        request.headers.get("user-agent"),
        repositorios.adesoes,
    )
    return _adesao(adesao)


@router.post(
    "/adesoes/{id}/submissao",
    response_model=SubmissaoResposta,
    status_code=status.HTTP_201_CREATED,
    summary="Submeter a adesão",
    description="Cria o cliente com a senha informada e o pedido de homologação.",
    responses=respostas_de_erro(400, 401, 404, 409, 422),
)
def submeter_adesao(id: str, dados: SubmissaoRequisicao, interessado: Interessado = Depends(obter_interessado_do_fluxo)):
    submissao = adesao_service.submeter(
        id,
        interessado,
        dados.senha,
        dados.aceite_compartilhamento_dados,
        repositorios.adesoes,
        repositorios.clientes,
        repositorios.pedidos,
    )
    prazo = pedido_service.PRAZO_ESTIMADO_DIAS
    return SubmissaoResposta(
        adesao_id=submissao.adesao.id,
        cliente_id=submissao.cliente.id,
        pedido_id=submissao.pedido.id,
        situacao=submissao.adesao.situacao,
        prazo_estimado_dias=PrazoEstimado(**prazo),
        mensagem=(
            f"Recebemos sua adesão. A homologação junto à Cemig leva de {prazo['minimo']} a {prazo['maximo']} dias "
            "e você pode acompanhar cada etapa pelo app."
        ),
    )
