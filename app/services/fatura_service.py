import re
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from app.core import relogio
from app.core.erros import ErroApi
from app.models.cliente import Cliente
from app.models.fatura import GRANULARIDADES, SITUACOES_FATURA, Fatura
from app.repositories.pedido_repository import PedidoRepository
from app.services import autenticacao_service

_COMPETENCIA = re.compile(r"\d{4}-(0[1-9]|1[0-2])")


@dataclass
class FaturasDoCliente:
    faturas: List[Fatura]
    situacoes: Dict[str, str]  # id da fatura -> situação na data de hoje
    estado_vazio: Optional[str]


@dataclass
class PontoDaSerie:
    competencia: str
    consumo_kwh: int
    valor_pago_centavos: int
    economia_centavos: int


@dataclass
class ConsumoDoCliente:
    instalacao: Optional[str]
    granularidade: str
    serie: List[PontoDaSerie]
    economia_acumulada: int
    consumo_medio: int
    estado_vazio: Optional[str]


def _parametro_invalido(mensagem: str, campo: str, problema: str) -> ErroApi:
    return ErroApi(400, "PARAMETRO_INVALIDO", mensagem, [{"campo": campo, "problema": problema}])


def cliente_tem_fatura_ativa(cliente_id: str, pedidos: PedidoRepository) -> bool:
    """Fatura ativa: ao menos uma fatura emitida e nenhuma vencida em aberto."""
    faturas = pedidos.listar_faturas_por_cliente(cliente_id)
    hoje = relogio.hoje()
    return bool(faturas) and all(f.situacao_em(hoje) != "vencida" for f in faturas)


def estado_vazio_do_cliente(cliente: Cliente, pedidos: PedidoRepository) -> Optional[str]:
    """Chave do estado vazio, ou None quando o cliente já tem alguma fatura."""
    if pedidos.listar_faturas_por_cliente(cliente.id):
        return None
    situacoes = {p.situacao for p in pedidos.listar_por_cliente(cliente.id)}
    if "aprovado" in situacoes:
        return "homologado_sem_fatura"
    if "em_andamento" in situacoes:
        return "aguardando_homologacao"
    return "sem_instalacao"


def listar_faturas(cliente: Cliente, situacao: Optional[str], pedidos: PedidoRepository) -> FaturasDoCliente:
    if situacao is not None and situacao not in SITUACOES_FATURA:
        raise _parametro_invalido(
            "A situação informada não existe. Use aberta, paga ou vencida.",
            "situacao",
            "valor fora de aberta, paga, vencida",
        )
    hoje = relogio.hoje()
    faturas = pedidos.listar_faturas_por_cliente(cliente.id)
    situacoes = {f.id: f.situacao_em(hoje) for f in faturas}
    if situacao:
        faturas = [f for f in faturas if situacoes[f.id] == situacao]
    return FaturasDoCliente(faturas, situacoes, estado_vazio_do_cliente(cliente, pedidos))


def obter_fatura(fatura_id: str, cliente: Cliente, pedidos: PedidoRepository) -> Tuple[Fatura, str]:
    fatura = pedidos.obter_fatura(fatura_id)
    # Fatura de outro cliente recebe a mesma resposta de fatura inexistente.
    if fatura is None or fatura.cliente_id != cliente.id:
        raise ErroApi(404, "FATURA_NAO_ENCONTRADA", "Não encontramos essa fatura. Volte à lista para ver as suas faturas.")
    return fatura, fatura.situacao_em(relogio.hoje())


def _validar_competencia(valor: Optional[str], campo: str) -> None:
    if valor is not None and not _COMPETENCIA.fullmatch(valor):
        raise _parametro_invalido(f"O campo {campo} deve estar no formato AAAA-MM.", campo, "formato esperado AAAA-MM")


def _agregar(faturas: List[Fatura], granularidade: str) -> List[PontoDaSerie]:
    por_periodo: Dict[str, List[Fatura]] = {}
    for f in sorted(faturas, key=lambda f: f.competencia):
        chave = f.competencia[:4] if granularidade == "anual" else f.competencia
        por_periodo.setdefault(chave, []).append(f)
    return [
        PontoDaSerie(
            chave,
            sum(f.consumo_kwh for f in grupo),
            sum(f.valor_centavos for f in grupo),
            sum(f.economia_centavos for f in grupo),
        )
        for chave, grupo in por_periodo.items()
    ]


def consultar_consumo(
    cliente: Cliente,
    instalacao: Optional[str],
    de: Optional[str],
    ate: Optional[str],
    granularidade: str,
    pedidos: PedidoRepository,
) -> ConsumoDoCliente:
    if granularidade not in GRANULARIDADES:
        raise _parametro_invalido(
            "A granularidade informada não existe. Use mensal ou anual.", "granularidade", "valor fora de mensal, anual"
        )
    _validar_competencia(de, "de")
    _validar_competencia(ate, "ate")
    if de is not None and ate is not None and de > ate:
        raise _parametro_invalido("O período é inválido: o mês inicial vem depois do final.", "de", "posterior a ate")

    instalacoes = autenticacao_service.montar_perfil(cliente, pedidos)
    if instalacao is None:
        escolhida = next((i for i in instalacoes if i.principal), None)
        numero = escolhida.pedido.numero_instalacao if escolhida else None
    elif any(i.pedido.numero_instalacao == instalacao for i in instalacoes):
        numero = instalacao
    else:
        raise _parametro_invalido(
            "Essa instalação não está vinculada à sua conta.", "instalacao", "instalação não pertence ao cliente"
        )

    pedidos_da_instalacao = {i.pedido.id for i in instalacoes if i.pedido.numero_instalacao == numero}
    faturas = [
        f
        for f in pedidos.listar_faturas_por_cliente(cliente.id)
        if f.pedido_id in pedidos_da_instalacao
        and (de is None or f.competencia >= de)
        and (ate is None or f.competencia <= ate)
    ]
    # Média arredondada para o inteiro mais próximo, sem float.
    consumo_total = sum(f.consumo_kwh for f in faturas)
    consumo_medio = (2 * consumo_total + len(faturas)) // (2 * len(faturas)) if faturas else 0
    return ConsumoDoCliente(
        instalacao=numero,
        granularidade=granularidade,
        serie=_agregar(faturas, granularidade),
        economia_acumulada=sum(f.economia_centavos for f in faturas),
        consumo_medio=consumo_medio,
        estado_vazio=estado_vazio_do_cliente(cliente, pedidos),
    )
