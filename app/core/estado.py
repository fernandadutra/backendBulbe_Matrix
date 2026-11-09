from app.core import limite_requisicoes, relogio
from app.db.database import SessionLocal
from app.repositories.adesao_repository import AdesaoRepository, SqlAdesaoRepository
from app.repositories.ajuda_repository import AjudaRepository, SqlAjudaRepository
from app.repositories.autenticacao_repository import AutenticacaoRepository, SqlAutenticacaoRepository
from app.repositories.beneficio_repository import BeneficioRepository, SqlBeneficioRepository
from app.repositories.conteudo_repository import ConteudoRepository, SqlConteudoRepository
from app.repositories.indicacao_repository import IndicacaoRepository, SqlIndicacaoRepository
from app.repositories.notificacao_repository import NotificacaoRepository, SqlNotificacaoRepository
from app.repositories.pedido_repository import PedidoRepository, SqlPedidoRepository
from app.repositories.sessao_repository import SessaoRepository, SqlSessaoRepository
from app.repositories.simulacao_repository import SimulacaoRepository, SqlSimulacaoRepository


class Repositorios:
    """Repositórios usados pela aplicação. Quem precisa de dados lê daqui.

    Os atributos são tipados pelo CONTRATO (Protocol); as instâncias são as
    versões SQL, que leem e gravam no banco. Para acrescentar um repositório:
    declare o atributo em __init__ e monte-o em reiniciar_estado().
    """

    def __init__(self):
        self.clientes: AutenticacaoRepository
        self.pedidos: PedidoRepository
        self.simulacoes: SimulacaoRepository
        self.beneficios: BeneficioRepository
        self.ajuda: AjudaRepository
        self.sessoes: SessaoRepository
        self.adesoes: AdesaoRepository
        self.indicacoes: IndicacaoRepository
        self.notificacoes: NotificacaoRepository
        self.conteudos: ConteudoRepository


repositorios = Repositorios()


def reiniciar_estado() -> None:
    """Monta os repositórios SQL e zera o estado que vive só na memória do processo
    (limites de requisição e relógio). Os dados ficam no banco: para popular, rode o seed."""
    repositorios.clientes = SqlAutenticacaoRepository(SessionLocal)
    repositorios.pedidos = SqlPedidoRepository(SessionLocal)
    repositorios.simulacoes = SqlSimulacaoRepository(SessionLocal)
    repositorios.beneficios = SqlBeneficioRepository(SessionLocal)
    repositorios.ajuda = SqlAjudaRepository(SessionLocal)
    repositorios.sessoes = SqlSessaoRepository(SessionLocal)
    repositorios.adesoes = SqlAdesaoRepository(SessionLocal)
    repositorios.indicacoes = SqlIndicacaoRepository(SessionLocal)
    repositorios.notificacoes = SqlNotificacaoRepository(SessionLocal)
    repositorios.conteudos = SqlConteudoRepository(SessionLocal)
    limite_requisicoes.reiniciar()
    relogio.restaurar_relogio()


reiniciar_estado()
