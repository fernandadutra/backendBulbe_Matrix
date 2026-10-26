import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import List, Optional

import jwt

from app.core import config, limite_requisicoes, relogio, senhas
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.cliente import Cliente
from app.models.pedido import Pedido
from app.models.sessao import Sessao
from app.repositories.autenticacao_repository import AutenticacaoRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.sessao_repository import SessaoRepository

# Hash de formato válido que nunca confere: gasta o mesmo tempo quando o identificador não existe.
_HASH_INEXISTENTE = "00" * 16 + "$" + "00" * 32


def cliente_do_token(token: str, repositorio: AutenticacaoRepository) -> Optional[Cliente]:
    """Devolve o cliente dono do token, ou None se o token for inválido, expirado ou de cliente inexistente."""
    try:
        claims = jwt.decode(
            token,
            config.JWT_SEGREDO,
            algorithms=[config.JWT_ALGORITMO],
            # A expiração é conferida abaixo com o relógio da aplicação, não o do sistema.
            options={"require": ["sub", "exp"], "verify_exp": False, "verify_iat": False},
        )
    except jwt.PyJWTError:
        return None
    exp = claims.get("exp")
    if not isinstance(exp, (int, float)) or exp <= relogio.agora().timestamp():
        return None
    sub = claims.get("sub")
    if not isinstance(sub, str):
        return None
    return repositorio.obter(sub)


@dataclass
class SessaoEmitida:
    cliente: Cliente
    token_renovacao: str
    possui_pedido_em_andamento: bool
    possui_fatura_emitida: bool


@dataclass
class InstalacaoDoCliente:
    pedido: Pedido
    principal: bool


def _hash_do_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _novo_token_renovacao() -> str:
    return "trn_" + secrets.token_urlsafe(32)


def _token_renovacao_invalido() -> ErroApi:
    return ErroApi(401, "TOKEN_RENOVACAO_INVALIDO", "Sua sessão expirou. Entre de novo para continuar.")


def _credenciais_invalidas() -> ErroApi:
    return ErroApi(401, "CREDENCIAIS_INVALIDAS", "E-mail, CPF ou senha incorretos. Confira os dados e tente de novo.")


def _normalizar(identificador: str) -> str:
    identificador = identificador.strip()
    if "@" in identificador:
        return identificador.lower()
    digitos = re.sub(r"[.\-\s]", "", identificador)
    return digitos if digitos.isdigit() and len(digitos) == 11 else identificador


def _buscar_cliente(identificador: str, repositorio: AutenticacaoRepository) -> Optional[Cliente]:
    if "@" in identificador:
        return repositorio.obter_por_email(identificador)
    if identificador.isdigit() and len(identificador) == 11:
        return repositorio.obter_por_cpf(identificador)
    return None


def _emitir(cliente: Cliente, token_renovacao: str, pedidos: PedidoRepository) -> SessaoEmitida:
    em_andamento = any(p.situacao == "em_andamento" for p in pedidos.listar_por_cliente(cliente.id))
    com_fatura = bool(pedidos.listar_faturas_por_cliente(cliente.id))
    return SessaoEmitida(cliente, token_renovacao, em_andamento, com_fatura)


def autenticar(
    identificador: str,
    senha: str,
    clientes: AutenticacaoRepository,
    sessoes: SessaoRepository,
    pedidos: PedidoRepository,
) -> SessaoEmitida:
    identificador = _normalizar(identificador)
    espera = limite_requisicoes.falhas_de_login_excedidas(identificador)
    if espera is not None:
        raise ErroApi(
            429,
            "LIMITE_DE_TENTATIVAS",
            f"Muitas tentativas de entrada com estes dados. Aguarde {espera} segundos e tente de novo.",
            cabecalhos={"Retry-After": str(espera)},
        )
    cliente = _buscar_cliente(identificador, clientes)
    senha_hash = cliente.senha_hash if cliente and cliente.senha_hash else _HASH_INEXISTENTE
    if not senhas.conferir(senha, senha_hash) or cliente is None:
        limite_requisicoes.registrar_falha_de_login(identificador)
        raise _credenciais_invalidas()
    limite_requisicoes.limpar_falhas_de_login(identificador)
    token = _novo_token_renovacao()
    agora = relogio.agora()
    sessoes.salvar(
        Sessao(
            id=gerar_id("ses"),
            cliente_id=cliente.id,
            criada_em=agora,
            expira_em=agora + timedelta(days=config.DIAS_TOKEN_RENOVACAO),
            hash_token=_hash_do_token(token),
        )
    )
    return _emitir(cliente, token, pedidos)


def renovar_sessao(
    token_renovacao: str, clientes: AutenticacaoRepository, sessoes: SessaoRepository, pedidos: PedidoRepository
) -> SessaoEmitida:
    hash_recebido = _hash_do_token(token_renovacao)
    sessao = sessoes.obter_por_hash(hash_recebido)
    if sessao is None:
        raise _token_renovacao_invalido()
    if hash_recebido in sessao.hashes_usados:
        # Token já rotacionado reaparecendo indica cópia: a sessão inteira deixa de valer.
        sessao.revogada = True
        raise _token_renovacao_invalido()
    agora = relogio.agora()
    cliente = clientes.obter(sessao.cliente_id)
    if sessao.revogada or sessao.expira_em <= agora or cliente is None:
        raise _token_renovacao_invalido()
    novo = _novo_token_renovacao()
    sessao.hashes_usados.add(sessao.hash_token)
    sessao.hash_token = _hash_do_token(novo)
    sessao.expira_em = agora + timedelta(days=config.DIAS_TOKEN_RENOVACAO)
    return _emitir(cliente, novo, pedidos)


def encerrar_sessao(token_renovacao: str, cliente: Cliente, sessoes: SessaoRepository) -> None:
    sessao = sessoes.obter_por_hash(_hash_do_token(token_renovacao))
    if sessao is not None and sessao.cliente_id == cliente.id:
        sessao.revogada = True


def montar_perfil(cliente: Cliente, pedidos: PedidoRepository) -> List[InstalacaoDoCliente]:
    do_cliente = sorted(pedidos.listar_por_cliente(cliente.id), key=lambda p: p.criado_em)
    return [InstalacaoDoCliente(p, principal=i == 0) for i, p in enumerate(do_cliente)]
