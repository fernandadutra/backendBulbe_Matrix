from app.core import limite_requisicoes, relogio
from app.repositories import dados_iniciais
from app.repositories.adesao_repository import AdesaoRepository
from app.repositories.ajuda_repository import AjudaRepository
from app.repositories.autenticacao_repository import AutenticacaoRepository
from app.repositories.beneficio_repository import BeneficioRepository
from app.repositories.pedido_repository import PedidoRepository
from app.repositories.sessao_repository import SessaoRepository
from app.repositories.simulacao_repository import SimulacaoRepository


class Repositorios:
    """Repositórios em memória do processo. Quem precisa de dados lê daqui.

    Para acrescentar um repositório: declare o atributo em __init__ e
    monte-o a partir da semente em reiniciar_estado().
    """

    def __init__(self):
        self.clientes: AutenticacaoRepository
        self.pedidos: PedidoRepository
        self.simulacoes: SimulacaoRepository
        self.beneficios: BeneficioRepository
        self.ajuda: AjudaRepository
        self.sessoes: SessaoRepository
        self.adesoes: AdesaoRepository


repositorios = Repositorios()


def reiniciar_estado() -> None:
    repositorios.clientes = AutenticacaoRepository(dados_iniciais.clientes())
    repositorios.pedidos = PedidoRepository(dados_iniciais.pedidos())
    repositorios.simulacoes = SimulacaoRepository()
    repositorios.beneficios = BeneficioRepository(
        dados_iniciais.parceiros(), dados_iniciais.trilhas(), dados_iniciais.beneficios()
    )
    repositorios.ajuda = AjudaRepository(dados_iniciais.dicas())
    repositorios.sessoes = SessaoRepository()
    repositorios.adesoes = AdesaoRepository()
    limite_requisicoes.reiniciar()
    relogio.restaurar_relogio()


reiniciar_estado()
