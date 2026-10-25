import secrets
import string
from dataclasses import dataclass
from datetime import datetime, time, timedelta
from typing import List, Optional, Tuple
from uuid import UUID

from app.core import relogio
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.beneficio import CHAVES_TRILHA, Beneficio, Parceiro, Trilha
from app.models.cliente import Cliente
from app.models.resgate import Resgate
from app.repositories.beneficio_repository import BeneficioRepository
from app.repositories.pedido_repository import PedidoRepository

MOTIVO_PEDIDO_APROVADO = "Disponível após a aprovação do seu pedido pela Cemig."
MOTIVO_FATURA_ATIVA = "Disponível para clientes com fatura Bulbe ativa."

_ALFABETO_CODIGO = string.ascii_uppercase + string.digits


@dataclass
class BeneficioAvaliado:
    beneficio: Beneficio
    parceiro: Parceiro
    elegivel: bool
    motivo_inelegibilidade: Optional[str]


@dataclass
class TrilhaAvaliada:
    trilha: Trilha
    desbloqueada: bool
    motivo_bloqueio: Optional[str]
    quantidade_beneficios_ativos: int
    parceiros_destaque: List[Parceiro]


@dataclass
class ResgateListado:
    resgate: Resgate
    beneficio_titulo: str
    parceiro_nome: str


def cliente_atende_regra(
    regra: str, cliente: Cliente, pedidos: PedidoRepository, pedido_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    """Única decisão de acesso: vale para desbloquear trilha e para elegibilidade de benefício."""
    if regra == "livre":
        return True, None
    if regra == "pedido_aprovado":
        if pedido_id is not None:
            pedido = pedidos.obter(pedido_id)
            atende = pedido is not None and pedido.cliente_id == cliente.id and pedido.situacao == "aprovado"
        else:
            atende = pedidos.cliente_tem_pedido_aprovado(cliente.id)
        return (True, None) if atende else (False, MOTIVO_PEDIDO_APROVADO)
    if regra == "fatura_ativa":
        # Faturas só existem no Bloco 2: até lá, nenhum cliente atende esta regra.
        return False, MOTIVO_FATURA_ATIVA
    raise ValueError(f"Regra de acesso desconhecida: {regra}")


def _elegibilidade(
    beneficio: Beneficio, trilha: Trilha, cliente: Cliente, pedidos: PedidoRepository, pedido_id: Optional[str] = None
) -> Tuple[bool, Optional[str]]:
    for regra in (trilha.regra_acesso, beneficio.regra_acesso):
        atende, motivo = cliente_atende_regra(regra, cliente, pedidos, pedido_id)
        if not atende:
            return False, motivo
    return True, None


def _avaliar(beneficio: Beneficio, cliente: Cliente, repositorio: BeneficioRepository, pedidos: PedidoRepository) -> BeneficioAvaliado:
    trilha = next(t for t in repositorio.listar_trilhas() if t.chave == beneficio.trilha)
    elegivel, motivo = _elegibilidade(beneficio, trilha, cliente, pedidos)
    return BeneficioAvaliado(beneficio, repositorio.obter_parceiro(beneficio.parceiro_id), elegivel, motivo)


def listar_beneficios(
    cliente: Cliente, trilha: Optional[str], repositorio: BeneficioRepository, pedidos: PedidoRepository
) -> List[BeneficioAvaliado]:
    if trilha is not None and trilha not in CHAVES_TRILHA:
        raise ErroApi(
            400,
            "PARAMETRO_INVALIDO",
            "A trilha informada não existe. Use connect, movement ou experience.",
            [{"campo": "trilha", "problema": "valor fora de connect, movement, experience"}],
        )
    hoje = relogio.hoje()
    vigentes = [b for b in repositorio.listar_beneficios() if b.vigente_em(hoje) and (trilha is None or b.trilha == trilha)]
    return [_avaliar(b, cliente, repositorio, pedidos) for b in vigentes]


def obter_beneficio(
    beneficio_id: str, cliente: Cliente, repositorio: BeneficioRepository, pedidos: PedidoRepository
) -> BeneficioAvaliado:
    beneficio = repositorio.obter_beneficio(beneficio_id)
    if beneficio is None or not beneficio.vigente_em(relogio.hoje()):
        raise _beneficio_nao_encontrado()
    return _avaliar(beneficio, cliente, repositorio, pedidos)


def listar_trilhas(cliente: Cliente, repositorio: BeneficioRepository, pedidos: PedidoRepository) -> List[TrilhaAvaliada]:
    hoje = relogio.hoje()
    vigentes = [b for b in repositorio.listar_beneficios() if b.vigente_em(hoje)]
    avaliadas = []
    for trilha in repositorio.listar_trilhas():
        da_trilha = [b for b in vigentes if b.trilha == trilha.chave]
        desbloqueada, motivo = cliente_atende_regra(trilha.regra_acesso, cliente, pedidos)
        destaques = {b.parceiro_id: repositorio.obter_parceiro(b.parceiro_id) for b in da_trilha}
        avaliadas.append(
            TrilhaAvaliada(
                trilha=trilha,
                desbloqueada=desbloqueada,
                motivo_bloqueio=motivo,
                quantidade_beneficios_ativos=len(da_trilha),
                parceiros_destaque=sorted((p for p in destaques.values() if p.destaque), key=lambda p: p.nome),
            )
        )
    return avaliadas


def _beneficio_nao_encontrado() -> ErroApi:
    return ErroApi(404, "BENEFICIO_NAO_ENCONTRADO", "Não encontramos esse benefício. Volte à lista para ver as ofertas atuais.")


def _validar_chave(chave: Optional[str]) -> str:
    try:
        if chave is None:
            raise ValueError
        return str(UUID(chave))
    except ValueError:
        raise ErroApi(
            400,
            "IDEMPOTENCY_KEY_INVALIDA",
            "Não foi possível confirmar o resgate. Atualize a tela e tente de novo.",
            [{"campo": "Idempotency-Key", "problema": "obrigatório, no formato UUID"}],
        )


def _gerar_codigo(prefixo: str) -> str:
    sufixo = "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(4))
    return f"BULBE-{prefixo}-{sufixo}"


def resgatar(
    beneficio_id: str,
    cliente: Cliente,
    chave: Optional[str],
    pedido_id: Optional[str],
    repositorio: BeneficioRepository,
    pedidos: PedidoRepository,
) -> Resgate:
    chave = _validar_chave(chave)
    with repositorio.trava:
        anterior = repositorio.resgate_por_chave(cliente.id, chave)
        if anterior is not None:
            if anterior.beneficio_id != beneficio_id:
                raise ErroApi(
                    422,
                    "CHAVE_DE_IDEMPOTENCIA_REUTILIZADA",
                    "Não foi possível confirmar o resgate. Atualize a tela e tente de novo.",
                )
            return anterior

        beneficio = repositorio.obter_beneficio(beneficio_id)
        if beneficio is None:
            raise _beneficio_nao_encontrado()
        if pedido_id is not None:
            pedido = pedidos.obter(pedido_id)
            # Pedido de outro cliente recebe a mesma resposta de pedido inexistente.
            if pedido is None or pedido.cliente_id != cliente.id:
                raise ErroApi(404, "PEDIDO_NAO_ENCONTRADO", "Não encontramos esse pedido. Confira o número ou volte à lista de pedidos.")

        hoje = relogio.hoje()
        if beneficio.ativo and hoje < beneficio.validade_inicio:
            raise _beneficio_nao_encontrado()
        if not beneficio.vigente_em(hoje):
            raise ErroApi(
                410,
                "BENEFICIO_EXPIRADO",
                "Este benefício não está mais disponível. Atualize a lista para ver as ofertas atuais.",
            )
        if beneficio.tipo == "uso_unico" and repositorio.cliente_ja_resgatou(cliente.id, beneficio.id):
            raise ErroApi(
                409,
                "BENEFICIO_JA_RESGATADO",
                "Você já resgatou este benefício. Consulte o código na sua lista de resgates.",
            )
        trilha = next(t for t in repositorio.listar_trilhas() if t.chave == beneficio.trilha)
        elegivel, motivo = _elegibilidade(beneficio, trilha, cliente, pedidos, pedido_id)
        if not elegivel:
            raise ErroApi(422, "CLIENTE_NAO_ELEGIVEL", motivo)

        agora = relogio.agora()
        limite = agora.date() + timedelta(days=beneficio.dias_validade_resgate)
        resgate_id = gerar_id("rsg")
        resgate = Resgate(
            id=resgate_id,
            cliente_id=cliente.id,
            beneficio_id=beneficio.id,
            resgatado_em=agora,
            situacao="confirmado",
            instrucoes=beneficio.instrucoes,
            codigo=_gerar_codigo(beneficio.prefixo_codigo),
            url_acesso=f"{beneficio.url_acesso}?rsg={resgate_id}",
            expira_em=datetime.combine(limite, time(23, 59, 59), tzinfo=relogio.FUSO),
            chave_idempotencia=chave,
            pedido_id=pedido_id,
        )
        repositorio.salvar_resgate(resgate)
        return resgate


def listar_resgates(cliente: Cliente, repositorio: BeneficioRepository) -> List[ResgateListado]:
    listados = []
    for resgate in repositorio.listar_resgates_por_cliente(cliente.id):
        beneficio = repositorio.obter_beneficio(resgate.beneficio_id)
        parceiro = repositorio.obter_parceiro(beneficio.parceiro_id)
        listados.append(ResgateListado(resgate, beneficio.titulo, parceiro.nome))
    return listados
