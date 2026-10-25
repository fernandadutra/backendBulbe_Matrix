from typing import Optional

from fastapi import APIRouter, Body, Depends, Header, Query, status

from app.core.estado import repositorios
from app.core.paginacao import ParametrosPaginacao, paginar, parametros_paginacao
from app.core.seguranca import obter_cliente_atual
from app.models.cliente import Cliente
from app.schemas.beneficio import (
    AcaoBeneficio,
    Beneficio,
    CondicoesResgate,
    EstadoVazio,
    ListaTrilhas,
    PaginaBeneficios,
    ParceiroBeneficio,
    ParceiroDestaque,
    ResgateCriado,
    ResgateRequisicao,
    ResgateResumo,
    Trilha,
    ValidadeBeneficio,
)
from app.schemas.comum import Paginacao, respostas_de_erro
from app.services import beneficio_service
from app.services.beneficio_service import BeneficioAvaliado

router = APIRouter(tags=["Clube de Benefícios"])

ESTADO_VAZIO = EstadoVazio(
    titulo="Nenhum benefício disponível agora",
    mensagem="Novos benefícios dos parceiros Bulbe aparecem aqui assim que forem liberados.",
)


def _beneficio(av: BeneficioAvaliado) -> Beneficio:
    b, p = av.beneficio, av.parceiro
    rotulo = f"Válido até {b.validade_fim:%d/%m/%Y}" if b.validade_fim else "Sem prazo definido"
    return Beneficio(
        id=b.id,
        trilha=b.trilha,
        parceiro=ParceiroBeneficio(id=p.id, nome=p.nome, url_logo=p.url_logo, cor_marca=p.cor_marca),
        titulo=b.titulo,
        descricao=b.descricao,
        regras_de_uso=b.regras_de_uso,
        condicoes_resgate=CondicoesResgate(
            tipo=b.tipo,
            exige_pedido_aprovado=b.regra_acesso == "pedido_aprovado",
            elegivel=av.elegivel,
            motivo_inelegibilidade=av.motivo_inelegibilidade,
        ),
        validade=ValidadeBeneficio(inicio=b.validade_inicio, fim=b.validade_fim, rotulo=rotulo),
        acao=AcaoBeneficio(rotulo="Acessar", exige_resgate=True),
    )


@router.get(
    "/beneficios",
    response_model=PaginaBeneficios,
    summary="Listar benefícios ativos",
    responses=respostas_de_erro(400, 401),
)
def listar_beneficios(
    trilha: Optional[str] = Query(
        default=None,
        description="Filtra por trilha do clube.",
        json_schema_extra={"enum": ["connect", "movement", "experience"]},
    ),
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    avaliados = beneficio_service.listar_beneficios(cliente, trilha, repositorios.beneficios, repositorios.pedidos)
    fatia, total = paginar(avaliados, paginacao)
    dados = [_beneficio(av) for av in fatia]
    return PaginaBeneficios(
        dados=dados,
        pagina=paginacao.pagina,
        limite=paginacao.limite,
        total=total,
        estado_vazio=None if dados else ESTADO_VAZIO,
    )


@router.get(
    "/beneficios/{id}",
    response_model=Beneficio,
    summary="Obter um benefício",
    responses=respostas_de_erro(401, 404),
)
def obter_beneficio(id: str, cliente: Cliente = Depends(obter_cliente_atual)):
    avaliado = beneficio_service.obter_beneficio(id, cliente, repositorios.beneficios, repositorios.pedidos)
    return _beneficio(avaliado)


@router.get(
    "/trilhas",
    response_model=ListaTrilhas,
    summary="Listar trilhas do clube",
    responses=respostas_de_erro(401),
)
def listar_trilhas(cliente: Cliente = Depends(obter_cliente_atual)):
    avaliadas = beneficio_service.listar_trilhas(cliente, repositorios.beneficios, repositorios.pedidos)
    return ListaTrilhas(
        dados=[
            Trilha(
                chave=a.trilha.chave,
                nome=a.trilha.nome,
                descricao=a.trilha.descricao,
                desbloqueada=a.desbloqueada,
                motivo_bloqueio=a.motivo_bloqueio,
                cor_tema=a.trilha.cor_tema,
                url_icone=a.trilha.url_icone,
                quantidade_beneficios_ativos=a.quantidade_beneficios_ativos,
                parceiros_destaque=[
                    ParceiroDestaque(id=p.id, nome=p.nome, url_logo=p.url_logo) for p in a.parceiros_destaque
                ],
            )
            for a in avaliadas
        ]
    )


@router.post(
    "/beneficios/{id}/resgates",
    response_model=ResgateCriado,
    status_code=status.HTTP_201_CREATED,
    summary="Resgatar um benefício",
    responses=respostas_de_erro(400, 401, 404, 409, 410, 422),
)
def resgatar_beneficio(
    id: str,
    corpo: Optional[ResgateRequisicao] = Body(default=None),
    idempotency_key: Optional[str] = Header(
        default=None,
        alias="Idempotency-Key",
        description="Obrigatório. UUID gerado pelo cliente a cada tentativa de resgate.",
    ),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    resgate = beneficio_service.resgatar(
        id,
        cliente,
        idempotency_key,
        corpo.pedido_id if corpo else None,
        repositorios.beneficios,
        repositorios.pedidos,
    )
    return ResgateCriado(
        id=resgate.id,
        beneficio_id=resgate.beneficio_id,
        resgatado_em=resgate.resgatado_em,
        situacao=resgate.situacao,
        instrucoes=resgate.instrucoes,
        codigo=resgate.codigo,
        url_acesso=resgate.url_acesso,
        expira_em=resgate.expira_em,
    )


@router.get(
    "/resgates",
    response_model=Paginacao[ResgateResumo],
    summary="Listar resgates do cliente",
    responses=respostas_de_erro(400, 401),
)
def listar_resgates(
    paginacao: ParametrosPaginacao = Depends(parametros_paginacao),
    cliente: Cliente = Depends(obter_cliente_atual),
):
    listados = beneficio_service.listar_resgates(cliente, repositorios.beneficios)
    fatia, total = paginar(listados, paginacao)
    dados = [
        ResgateResumo(
            id=item.resgate.id,
            beneficio_id=item.resgate.beneficio_id,
            beneficio_titulo=item.beneficio_titulo,
            parceiro_nome=item.parceiro_nome,
            resgatado_em=item.resgate.resgatado_em,
            situacao=item.resgate.situacao,
            codigo=item.resgate.codigo,
            expira_em=item.resgate.expira_em,
        )
        for item in fatia
    ]
    return Paginacao[ResgateResumo](dados=dados, pagina=paginacao.pagina, limite=paginacao.limite, total=total)
