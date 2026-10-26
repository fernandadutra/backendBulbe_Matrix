import re
import secrets
import string
import unicodedata
from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional, Tuple

from app.core import relogio
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.cliente import Cliente
from app.models.indicacao import CATALOGO_FAIXAS, Indicacao
from app.repositories.autenticacao_repository import AutenticacaoRepository
from app.repositories.indicacao_repository import IndicacaoRepository
from app.repositories.notificacao_repository import NotificacaoRepository
from app.services import notificacao_service
from app.services.interessado_service import normalizar_whatsapp

RECOMPENSA_POR_INDICACAO_CENTAVOS = 5000
LIMITE_INDICACOES_PENDENTES = 10
URL_COMPARTILHAMENTO = "https://bulbe.com.br/indique/{codigo}"

_ALFABETO_CODIGO = string.ascii_uppercase + string.digits


@dataclass
class PainelDeIndicacoes:
    codigo: str
    indicacoes: List[Indicacao]
    total: int
    convertidas: int
    credito_centavos: int
    faixa: Tuple[str, str, int]
    proxima_faixa: Optional[str]
    para_proxima: int


def ofuscar_nome(nome: str) -> str:
    """LGPD: o indicador nunca vê o nome completo. Primeira palavra com 2 letras, última com 1; as do meio somem."""
    palavras = nome.split()
    if len(palavras) == 1:
        return palavras[0][:2] + "*" * (len(palavras[0]) - 2)
    return " ".join(p[:visiveis] + "*" * (len(p) - visiveis) for p, visiveis in ((palavras[0], 2), (palavras[-1], 1)))


def _codigo_base(nome: str) -> str:
    primeiro = unicodedata.normalize("NFKD", nome.split()[0]).encode("ascii", "ignore").decode()
    return re.sub(r"[^A-Za-z0-9]", "", primeiro).upper() + "50"


def _obter_codigo(cliente: Cliente, repositorio: IndicacaoRepository) -> str:
    codigo = repositorio.codigo_do_cliente(cliente.id)
    if codigo is not None:
        return codigo
    codigo = _codigo_base(cliente.nome)
    while repositorio.cliente_do_codigo(codigo) is not None:
        codigo = _codigo_base(cliente.nome) + "".join(secrets.choice(_ALFABETO_CODIGO) for _ in range(2))
    repositorio.salvar_codigo(cliente.id, codigo)
    return codigo


def painel(cliente: Cliente, repositorio: IndicacaoRepository) -> PainelDeIndicacoes:
    indicacoes = repositorio.listar_por_cliente(cliente.id)
    total = len(indicacoes)
    convertidas = sum(1 for i in indicacoes if i.situacao == "convertida")
    posicao = max(n for n, faixa in enumerate(CATALOGO_FAIXAS) if total >= faixa[2])
    proxima = CATALOGO_FAIXAS[posicao + 1] if posicao + 1 < len(CATALOGO_FAIXAS) else None
    return PainelDeIndicacoes(
        codigo=_obter_codigo(cliente, repositorio),
        indicacoes=indicacoes,
        total=total,
        convertidas=convertidas,
        credito_centavos=convertidas * RECOMPENSA_POR_INDICACAO_CENTAVOS,
        faixa=CATALOGO_FAIXAS[posicao],
        proxima_faixa=proxima[0] if proxima else None,
        para_proxima=proxima[2] - total if proxima else 0,
    )


def indicar(
    cliente: Cliente, nome: str, whatsapp: str, repositorio: IndicacaoRepository, clientes: AutenticacaoRepository
) -> Indicacao:
    contato = normalizar_whatsapp(whatsapp)
    detalhes = []
    if not nome.strip():
        detalhes.append({"campo": "nome", "problema": "não pode ficar vazio"})
    if contato is None:
        detalhes.append({"campo": "whatsapp", "problema": "deve ter de 12 a 13 dígitos, com DDI e DDD"})
    if detalhes:
        raise ErroApi(400, "CORPO_INVALIDO", "O corpo da requisição é inválido. Corrija os campos indicados e tente de novo.", detalhes)

    if any(normalizar_whatsapp(c.telefone or "") == contato for c in clientes.listar()):
        raise ErroApi(409, "CONTATO_JA_CLIENTE", "Esta pessoa já é cliente Bulbe. Indique outro contato.")
    if repositorio.por_whatsapp(contato) is not None:
        raise ErroApi(409, "CONTATO_JA_INDICADO", "Este contato já foi indicado. Indique outra pessoa.")
    pendentes = sum(1 for i in repositorio.listar_por_cliente(cliente.id) if i.situacao == "pendente")
    if pendentes >= LIMITE_INDICACOES_PENDENTES:
        raise ErroApi(
            422,
            "LIMITE_DE_INDICACOES",
            f"Você já tem {LIMITE_INDICACOES_PENDENTES} indicações aguardando adesão. Espere alguma ser concluída para indicar mais.",
        )
    return repositorio.salvar(
        Indicacao(
            id=gerar_id("ind"), cliente_id=cliente.id, nome=nome.strip(), whatsapp=contato,
            situacao="pendente", indicada_em=relogio.hoje(),
        )
    )


def converter_indicacao(
    whatsapp: str, quando: datetime, repositorio: IndicacaoRepository, notificacoes: NotificacaoRepository
) -> None:
    # Só os dígitos contam: o interessado pode ter digitado o número com outra máscara.
    contato = normalizar_whatsapp(whatsapp)
    indicacao = repositorio.por_whatsapp(contato) if contato else None
    if indicacao is not None and indicacao.situacao == "pendente":
        indicacao.situacao, indicacao.convertida_em = "convertida", quando
        notificacao_service.notificar(indicacao.cliente_id, "indicacao_convertida", "indicacao", indicacao.id, notificacoes)
