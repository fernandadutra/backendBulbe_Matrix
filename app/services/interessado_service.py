import hashlib
import re
import secrets
from dataclasses import dataclass
from datetime import timedelta
from typing import Optional

from app.core import config, relogio
from app.core.erros import ErroApi
from app.core.ids import gerar_id
from app.models.adesao import Interessado
from app.repositories.adesao_repository import AdesaoRepository
from app.repositories.autenticacao_repository import AutenticacaoRepository
from app.repositories.simulacao_repository import SimulacaoRepository

_FORMATO_EMAIL = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")


@dataclass
class InteressadoRegistrado:
    interessado: Interessado
    token_fluxo: str


def _hash_do_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def interessado_do_token(token: str, repositorio: AdesaoRepository) -> Optional[Interessado]:
    """Devolve o interessado dono do token de fluxo, ou None se o token for inválido ou expirado."""
    interessado = repositorio.interessado_por_hash_token(_hash_do_token(token))
    if interessado is None or interessado.token_expira_em <= relogio.agora():
        return None
    return interessado


def registrar_interessado(
    nome: str,
    email: str,
    whatsapp: str,
    simulacao_id: Optional[str],
    aceite_comunicacoes: bool,
    adesoes: AdesaoRepository,
    clientes: AutenticacaoRepository,
    simulacoes: SimulacaoRepository,
) -> InteressadoRegistrado:
    email = email.strip().lower()
    detalhes = []
    if not nome.strip():
        detalhes.append({"campo": "nome", "problema": "não pode ficar vazio"})
    if not _FORMATO_EMAIL.match(email):
        detalhes.append({"campo": "email", "problema": "formato de e-mail inválido"})
    if not whatsapp.strip():
        detalhes.append({"campo": "whatsapp", "problema": "não pode ficar vazio"})
    if simulacao_id is not None and simulacoes.obter(simulacao_id) is None:
        detalhes.append({"campo": "simulacao_id", "problema": "simulação não encontrada"})
    if detalhes:
        raise ErroApi(400, "CORPO_INVALIDO", "O corpo da requisição é inválido. Corrija os campos indicados e tente de novo.", detalhes)
    if adesoes.interessado_por_email(email) or clientes.obter_por_email(email):
        raise ErroApi(409, "EMAIL_JA_CADASTRADO", "Já existe um cadastro com este e-mail. Entre na sua conta ou use outro e-mail.")

    token = "tfl_" + secrets.token_urlsafe(32)
    agora = relogio.agora()
    interessado = Interessado(
        id=gerar_id("int"),
        nome=nome.strip(),
        email=email,
        whatsapp=whatsapp.strip(),
        simulacao_id=simulacao_id,
        aceite_comunicacoes=aceite_comunicacoes,
        criado_em=agora,
        hash_token_fluxo=_hash_do_token(token),
        token_expira_em=agora + timedelta(hours=config.HORAS_TOKEN_FLUXO),
    )
    adesoes.salvar_interessado(interessado)
    return InteressadoRegistrado(interessado, token)
