import re
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

from app.core import relogio, senhas
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.adesao import CLASSES_CONSUMO, ETAPAS_ADESAO, Aceite, Adesao, Anexo, DadosNegocio, Interessado
from app.models.cliente import Cliente
from app.models.pedido import CATALOGO_ETAPAS, Etapa, Pedido
from app.repositories.adesao_repository import AdesaoRepository
from app.repositories.autenticacao_repository import AutenticacaoRepository
from app.repositories.indicacao_repository import IndicacaoRepository
from app.repositories.notificacao_repository import NotificacaoRepository
from app.repositories.pedido_repository import PedidoRepository
from app.services import indicacao_service, interessado_service, notificacao_service
from app.services.simulacao_service import DISTRIBUIDORA_ATENDIDA

VERSAO_DOCUMENTOS_VIGENTE = "2026-07-01"
TAMANHO_MAXIMO_ANEXO_BYTES = 10 * 1024 * 1024
TAMANHO_MINIMO_SENHA = 8
TIPO_ANEXO = "fatura_energia"
CAMPOS_NEGOCIO = ("numero_instalacao", "distribuidora", "titular_nome", "titular_documento", "cep", "classe_consumo")
ASSINATURAS_ARQUIVO = (b"%PDF", b"\x89PNG\r\n\x1a\n", b"\xff\xd8\xff")


@dataclass
class ProgressoAdesao:
    etapa_atual: str
    concluidas: List[str]
    pendentes: List[str]


@dataclass
class Submissao:
    adesao: Adesao
    cliente: Cliente
    pedido: Pedido


def progresso(adesao: Adesao) -> ProgressoAdesao:
    feitas = {
        "contato": True,
        "negocio": adesao.negocio is not None,
        "termos": adesao.aceite is not None,
        "confirmacao": adesao.situacao == "submetida",
    }
    concluidas = [e for e in ETAPAS_ADESAO if feitas[e]]
    pendentes = [e for e in ETAPAS_ADESAO if not feitas[e]]
    return ProgressoAdesao(concluidas[-1], concluidas, pendentes)


def _corpo_invalido(detalhes: List[Dict[str, str]]) -> ErroApi:
    return ErroApi(400, "CORPO_INVALIDO", "O corpo da requisição é inválido. Corrija os campos indicados e tente de novo.", detalhes)


def _obter_editavel(adesao_id: str, interessado: Interessado, repositorio: AdesaoRepository) -> Adesao:
    adesao = repositorio.obter_adesao(adesao_id)
    # Adesão de outro interessado recebe a mesma resposta de adesão inexistente.
    if adesao is None or adesao.interessado_id != interessado.id:
        raise ErroApi(404, "ADESAO_NAO_ENCONTRADA", "Não encontramos essa adesão. Confira o código ou comece o cadastro de novo.")
    if adesao.situacao == "submetida":
        raise ErroApi(409, "ADESAO_JA_SUBMETIDA", "Essa adesão já foi enviada e não pode mais ser alterada.")
    return adesao


def _somente_digitos(valor: str) -> str:
    return re.sub(r"[.\-/\s]", "", valor)


def _campos_ausentes(dados: Dict[str, Any], campos: Tuple[str, ...]) -> List[Dict[str, str]]:
    return [
        {"campo": f"dados.{c}", "problema": "campo obrigatório"}
        for c in campos
        if not isinstance(dados.get(c), str) or not dados[c].strip()
    ]


def _validar_negocio(dados: Dict[str, Any]) -> DadosNegocio:
    detalhes = _campos_ausentes(dados, CAMPOS_NEGOCIO)
    if detalhes:
        raise _corpo_invalido(detalhes)
    documento = _somente_digitos(dados["titular_documento"])
    cep = _somente_digitos(dados["cep"])
    classe = dados["classe_consumo"].strip().lower()
    if not (documento.isdigit() and len(documento) in (11, 14)):
        detalhes.append({"campo": "dados.titular_documento", "problema": "deve ter 11 dígitos (CPF) ou 14 (CNPJ)"})
    if not (cep.isdigit() and len(cep) == 8):
        detalhes.append({"campo": "dados.cep", "problema": "deve ter 8 dígitos"})
    if classe not in CLASSES_CONSUMO:
        detalhes.append({"campo": "dados.classe_consumo", "problema": "valor fora de " + ", ".join(CLASSES_CONSUMO)})
    if detalhes:
        raise _corpo_invalido(detalhes)
    if dados["distribuidora"].strip().upper() != DISTRIBUIDORA_ATENDIDA:
        raise ErroApi(
            422,
            "DISTRIBUIDORA_NAO_ATENDIDA",
            "Por enquanto a Bulbe atende apenas clientes da CEMIG.",
            [{"campo": "dados.distribuidora", "problema": "distribuidora não atendida"}],
        )
    instalacao = dados["numero_instalacao"].strip()
    if not (instalacao.isdigit() and len(instalacao) == 10):
        raise ErroApi(
            422,
            "INSTALACAO_INVALIDA",
            "O número da instalação deve ter 10 dígitos. Confira na sua conta de luz.",
            [{"campo": "dados.numero_instalacao", "problema": "deve ter 10 dígitos"}],
        )
    return DadosNegocio(instalacao, DISTRIBUIDORA_ATENDIDA, dados["titular_nome"].strip(), documento, cep, classe)


def abrir_adesao(interessado_id: str, interessado: Interessado, repositorio: AdesaoRepository) -> Adesao:
    if interessado_id != interessado.id:
        raise ErroApi(404, "INTERESSADO_NAO_ENCONTRADO", "Não encontramos esse cadastro. Comece o cadastro de novo.")
    adesao = repositorio.adesao_do_interessado(interessado.id)
    if adesao is None:
        adesao = Adesao(id=gerar_id("ade"), interessado_id=interessado.id, criada_em=relogio.agora())
        repositorio.salvar_adesao(adesao)
    return adesao


def salvar_etapa(
    adesao_id: str, interessado: Interessado, etapa: str, dados: Dict[str, Any], repositorio: AdesaoRepository
) -> Adesao:
    adesao = _obter_editavel(adesao_id, interessado, repositorio)
    if etapa in ("termos", "confirmacao"):
        destino = "/aceites" if etapa == "termos" else "/submissao"
        raise _corpo_invalido([{"campo": "etapa", "problema": f"esta etapa não é salva aqui, use POST /adesoes/{{id}}{destino}"}])
    if etapa not in ETAPAS_ADESAO:
        raise _corpo_invalido([{"campo": "etapa", "problema": "valor fora de " + ", ".join(ETAPAS_ADESAO)}])
    if etapa == "negocio":
        adesao.negocio = _validar_negocio(dados)
        return adesao
    detalhes = _campos_ausentes(dados, ("nome", "whatsapp"))
    whatsapp = None if detalhes else interessado_service.normalizar_whatsapp(dados["whatsapp"])
    if not detalhes and whatsapp is None:
        detalhes.append({"campo": "dados.whatsapp", "problema": "deve ter de 12 a 13 dígitos, com DDI e DDD"})
    if detalhes:
        raise _corpo_invalido(detalhes)
    interessado.nome, interessado.whatsapp = dados["nome"].strip(), whatsapp
    return adesao


def receber_anexo(
    adesao_id: str, interessado: Interessado, tipo: str, nome_arquivo: Optional[str], conteudo: bytes,
    repositorio: AdesaoRepository,
) -> Anexo:
    adesao = _obter_editavel(adesao_id, interessado, repositorio)
    if tipo != TIPO_ANEXO:
        raise _corpo_invalido([{"campo": "tipo", "problema": f"valor fora de {TIPO_ANEXO}"}])
    if len(conteudo) > TAMANHO_MAXIMO_ANEXO_BYTES:
        raise ErroApi(413, "ARQUIVO_MUITO_GRANDE", "O arquivo passa de 10 MB. Envie uma versão menor da fatura.")
    if not conteudo:
        raise ErroApi(422, "ARQUIVO_ILEGIVEL", "Não conseguimos ler o arquivo. Envie a fatura de novo.")
    if not conteudo.startswith(ASSINATURAS_ARQUIVO):
        raise ErroApi(415, "FORMATO_NAO_SUPORTADO", "Envie a fatura em PDF, JPG ou PNG.")
    nome = (nome_arquivo or "fatura").replace("\\", "/").split("/")[-1]
    anexo = Anexo(gerar_id("anx"), tipo, nome, len(conteudo), conteudo, relogio.agora())
    adesao.anexos.append(anexo)
    return anexo


def registrar_aceite(
    adesao_id: str, interessado: Interessado, aceite_termo: bool, aceite_politica: bool, versao: str,
    aceito_em: datetime, ip: str, user_agent: Optional[str], repositorio: AdesaoRepository,
) -> Adesao:
    adesao = _obter_editavel(adesao_id, interessado, repositorio)
    if adesao.aceite is not None:
        raise ErroApi(409, "ACEITE_JA_REGISTRADO", "Você já aceitou os termos desta adesão.")
    detalhes = [
        {"campo": campo, "problema": "o aceite é obrigatório"}
        for campo, valor in (("aceite_termo_adesao", aceite_termo), ("aceite_politica_privacidade", aceite_politica))
        if not valor
    ]
    if detalhes:
        raise _corpo_invalido(detalhes)
    if versao != VERSAO_DOCUMENTOS_VIGENTE:
        raise ErroApi(
            422,
            "VERSAO_DOCUMENTOS_DESATUALIZADA",
            "Os termos foram atualizados. Leia a versão atual e aceite de novo.",
            [{"campo": "versao_documentos", "problema": f"a versão vigente é {VERSAO_DOCUMENTOS_VIGENTE}"}],
        )
    adesao.aceite = Aceite(versao, aceito_em, relogio.agora(), ip, user_agent)
    return adesao


def submeter(
    adesao_id: str, interessado: Interessado, senha: str, aceite_compartilhamento: bool,
    adesoes: AdesaoRepository, clientes: AutenticacaoRepository, pedidos: PedidoRepository,
    indicacoes: IndicacaoRepository, notificacoes: NotificacaoRepository,
) -> Submissao:
    adesao = _obter_editavel(adesao_id, interessado, adesoes)
    detalhes = [
        {"campo": campo, "problema": "etapa pendente"}
        for campo, pendente in (
            ("negocio", adesao.negocio is None),
            ("anexo", not adesao.anexos),
            ("termos", adesao.aceite is None),
        )
        if pendente
    ]
    if len(senha) < TAMANHO_MINIMO_SENHA:
        detalhes.append({"campo": "senha", "problema": f"deve ter pelo menos {TAMANHO_MINIMO_SENHA} caracteres"})
    if not aceite_compartilhamento:
        detalhes.append({"campo": "aceite_compartilhamento_dados", "problema": "o aceite é obrigatório"})
    if detalhes:
        raise ErroApi(422, "SUBMISSAO_INVALIDA", "Faltam informações para concluir a adesão. Revise os itens indicados.", detalhes)

    negocio = adesao.negocio
    cpf = negocio.titular_documento if len(negocio.titular_documento) == 11 else None
    if clientes.obter_por_email(interessado.email):
        raise ErroApi(409, "EMAIL_JA_CADASTRADO", "Já existe um cliente com este e-mail. Entre na sua conta.")
    if cpf and clientes.obter_por_cpf(cpf):
        raise ErroApi(409, "CPF_JA_CADASTRADO", "Já existe um cliente com este CPF. Entre na sua conta.")

    agora = relogio.agora()
    cliente = Cliente(
        id=gerar_id("cli"), nome=interessado.nome, email=interessado.email, cpf=cpf,
        telefone=interessado.whatsapp, senha_hash=senhas.gerar_hash(senha),
    )
    etapas = [
        Etapa(ordem, chave, nome, descricao, "em_andamento" if ordem == 1 else "pendente", agora if ordem == 1 else None)
        for ordem, chave, nome, descricao in CATALOGO_ETAPAS
    ]
    pedido = Pedido(
        id=gerar_id("ped"), cliente_id=cliente.id, numero_instalacao=negocio.numero_instalacao,
        distribuidora=negocio.distribuidora, situacao="em_andamento", criado_em=agora,
        previsao_proxima_atualizacao=None, etapas=etapas, consultado_em=agora,
    )
    clientes.salvar(cliente)
    pedidos.salvar(pedido)
    notificacao_service.notificar(cliente.id, "pedido_criado", "pedido", pedido.id, notificacoes)
    indicacao_service.converter_indicacao(interessado.whatsapp, agora, indicacoes, notificacoes)
    adesao.situacao, adesao.cliente_id, adesao.pedido_id = "submetida", cliente.id, pedido.id
    interessado.situacao = "convertido"
    return Submissao(adesao, cliente, pedido)
