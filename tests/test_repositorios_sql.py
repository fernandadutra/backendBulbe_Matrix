"""
Testes de integração dos repositórios SQL.

Falam com o banco de teste de verdade (bulbe_test.db), preparado pela fixture
estado_limpo do conftest: tabelas vazias + dados de demonstração do seed.
Verificam que o SQLAlchemy, o SQLite e o nosso código funcionam juntos.

O coração deles: duas instâncias DIFERENTES de repositório enxergam o mesmo
dado, então o dado está no banco, e não na memória de um objeto.
"""

import hashlib
from datetime import timedelta

import pytest
from sqlalchemy.exc import IntegrityError

from app.core import relogio
from app.db.database import SessionLocal, engine
from app.db.unidade_de_trabalho import unidade_atual, unidade_de_trabalho
from app.models.adesao import Aceite, Adesao, Anexo, DadosNegocio, Interessado
from app.models.cliente import Cliente
from app.models.notificacao import Notificacao
from app.models.pedido import Etapa
from app.models.resgate import Resgate
from app.models.sessao import Sessao
from app.models.simulacao import Simulacao
from app.repositories.adesao_repository import SqlAdesaoRepository
from app.repositories.ajuda_repository import SqlAjudaRepository
from app.repositories.autenticacao_repository import SqlAutenticacaoRepository
from app.repositories.beneficio_repository import SqlBeneficioRepository
from app.repositories.conteudo_repository import SqlConteudoRepository
from app.repositories.indicacao_repository import SqlIndicacaoRepository
from app.repositories.notificacao_repository import SqlNotificacaoRepository
from app.repositories.pedido_repository import SqlPedidoRepository
from app.repositories.sessao_repository import SqlSessaoRepository
from app.repositories.simulacao_repository import SqlSimulacaoRepository
from tests.conftest import AGORA_CONGELADA, CLIENTE_A, CLIENTE_B, PEDIDO_A

AGORA = AGORA_CONGELADA


def _simulacao(simulacao_id: str, cliente_id=CLIENTE_A, calculado_em=AGORA) -> Simulacao:
    return Simulacao(
        id=simulacao_id, cliente_id=cliente_id, calculado_em=calculado_em, distribuidora="CEMIG", consumo_kwh=250,
        percentual_desconto=15.0, valor_sem_desconto_centavos=30000, valor_com_bulbe_centavos=25500,
        economia_mensal_centavos=4500, economia_anual_centavos=54000,
    )


def _interessado(interessado_id="int_teste01", email="maria@exemplo.com.br") -> Interessado:
    return Interessado(
        id=interessado_id, nome="Maria Souza", email=email, whatsapp="+5531999998888", simulacao_id=None,
        aceite_comunicacoes=True, criado_em=AGORA, hash_token_fluxo="h" * 64,
        token_expira_em=AGORA + timedelta(hours=24),
    )


# Banco de teste


def test_os_testes_usam_um_banco_separado():
    assert engine.url.database.endswith("bulbe_test.db")


# Clientes


def test_seed_gravou_os_clientes_de_demonstracao():
    nomes = [c.nome for c in SqlAutenticacaoRepository(SessionLocal).listar()]
    assert nomes == ["Ana Souza", "Bruno Lima"]


def test_cliente_persiste_entre_instancias_do_repositorio():
    SqlAutenticacaoRepository(SessionLocal).salvar(Cliente(id="cli_novo0001", nome="Carla", email="carla@x.com"))
    outra_instancia = SqlAutenticacaoRepository(SessionLocal)
    assert outra_instancia.obter("cli_novo0001").nome == "Carla"


def test_cliente_e_buscado_pelo_email_sem_diferenciar_maiusculas():
    repo = SqlAutenticacaoRepository(SessionLocal)
    assert repo.obter_por_email("ANA@Exemplo.com.br").id == CLIENTE_A
    assert repo.obter_por_cpf("11144477735").id == CLIENTE_B
    assert repo.obter_por_email("ninguem@exemplo.com.br") is None


def test_email_repetido_e_barrado_pelo_proprio_banco():
    repo = SqlAutenticacaoRepository(SessionLocal)
    with pytest.raises(IntegrityError):
        repo.salvar(Cliente(id="cli_copia001", nome="Outra Ana", email="ana@exemplo.com.br"))


# Simulações: data com fuso e ordem de gravação


def test_data_e_hora_voltam_do_banco_com_fuso():
    repo = SqlSimulacaoRepository(SessionLocal)
    repo.salvar(_simulacao("sim_fuso0001"))
    lida = SqlSimulacaoRepository(SessionLocal).obter("sim_fuso0001")
    assert lida.calculado_em == AGORA
    assert lida.calculado_em.utcoffset() == timedelta(hours=-3)


def test_simulacoes_mais_recentes_primeiro_e_empate_pela_ordem_de_gravacao():
    repo = SqlSimulacaoRepository(SessionLocal)
    repo.salvar(_simulacao("sim_antiga01", calculado_em=AGORA - timedelta(days=1)))
    repo.salvar(_simulacao("sim_empate01"))
    repo.salvar(_simulacao("sim_empate02"))
    repo.salvar(_simulacao("sim_doBruno1", cliente_id=CLIENTE_B))
    ids = [s.id for s in SqlSimulacaoRepository(SessionLocal).listar_por_cliente(CLIENTE_A)]
    assert ids == ["sim_empate02", "sim_empate01", "sim_antiga01"]


# Sessões: hashes já usados ficam numa tabela filha


def test_sessao_e_achada_pelo_hash_atual_e_pelos_ja_usados():
    repo = SqlSessaoRepository(SessionLocal)
    repo.salvar(Sessao("ses_teste001", CLIENTE_A, AGORA, AGORA + timedelta(days=30), "a" * 64))
    with unidade_de_trabalho():
        sessao = repo.obter_por_hash("a" * 64)
        sessao.hashes_usados.add(sessao.hash_token)
        sessao.hash_token = "b" * 64
    outra = SqlSessaoRepository(SessionLocal)
    assert outra.obter_por_hash("b" * 64).hashes_usados == {"a" * 64}
    assert outra.obter_por_hash("a" * 64).id == "ses_teste001"
    assert outra.obter_por_hash("c" * 64) is None


# Adesão: dados de negócio, aceite e anexos


def test_adesao_completa_vai_e_volta_do_banco():
    repo = SqlAdesaoRepository(SessionLocal)
    repo.salvar_interessado(_interessado())
    repo.salvar_adesao(Adesao(id="ade_teste001", interessado_id="int_teste01", criada_em=AGORA))
    with unidade_de_trabalho():
        adesao = repo.obter_adesao("ade_teste001")
        adesao.negocio = DadosNegocio("3013588579", "CEMIG", "Maria Souza", "52998224725", "30130000", "residencial")
        adesao.anexos.append(Anexo("anx_teste001", "fatura_energia", "conta.pdf", 8, b"%PDF-1.4", AGORA))
        adesao.aceite = Aceite("2026-07-01", AGORA, AGORA, "127.0.0.1", "pytest")

    lida = SqlAdesaoRepository(SessionLocal).adesao_do_interessado("int_teste01")
    assert lida.negocio.classe_consumo == "residencial"
    assert lida.aceite.ip == "127.0.0.1"
    assert [(a.nome_arquivo, a.conteudo) for a in lida.anexos] == [("conta.pdf", b"%PDF-1.4")]
    assert SqlAdesaoRepository(SessionLocal).interessado_por_email("MARIA@exemplo.com.br").id == "int_teste01"


# Pedidos: etapas na tabela filha


def test_salvar_consulta_troca_as_etapas_do_pedido():
    repo = SqlPedidoRepository(SessionLocal)
    pedido = repo.obter(PEDIDO_A)
    etapas = [Etapa(1, "analise_bulbe", "Em análise pela Bulbe", "d1", "concluida", AGORA, AGORA),
              Etapa(2, "enviado_cemig", "Enviado para Cemig", "d2", "em_andamento", AGORA)]
    repo.salvar_consulta(pedido, etapas, AGORA)

    lido = SqlPedidoRepository(SessionLocal).obter(PEDIDO_A)
    assert [(e.chave, e.situacao) for e in lido.etapas] == [("analise_bulbe", "concluida"),
                                                           ("enviado_cemig", "em_andamento")]
    assert lido.consultado_em == AGORA
    assert lido.etapa_atual.chave == "enviado_cemig"


def test_pedidos_e_faturas_do_seed():
    repo = SqlPedidoRepository(SessionLocal)
    assert repo.cliente_tem_pedido_aprovado(CLIENTE_B) is True
    assert repo.cliente_tem_pedido_aprovado(CLIENTE_A) is False
    assert [f.competencia for f in repo.listar_faturas_por_cliente(CLIENTE_B)] == ["2026-10", "2026-09", "2026-08"]


# Benefícios e resgates


def _resgate(resgate_id: str, chave: str, beneficio_id="ben_livelo_pontos") -> Resgate:
    return Resgate(
        id=resgate_id, cliente_id=CLIENTE_B, beneficio_id=beneficio_id, resgatado_em=AGORA, situacao="confirmado",
        instrucoes="i", codigo="LIVELO-1", url_acesso="https://x", expira_em=AGORA + timedelta(days=7),
        chave_idempotencia=chave,
    )


def test_salvar_resgate_grava_e_soma_o_contador_no_banco():
    repo = SqlBeneficioRepository(SessionLocal)
    repo.salvar_resgate(_resgate("rsg_teste001", "chave-1"))
    repo.salvar_resgate(_resgate("rsg_teste002", "chave-2"))
    outra = SqlBeneficioRepository(SessionLocal)
    assert outra.obter_beneficio("ben_livelo_pontos").total_resgates == 2
    assert outra.resgate_por_chave(CLIENTE_B, "chave-1").id == "rsg_teste001"
    assert outra.cliente_ja_resgatou(CLIENTE_B, "ben_livelo_pontos") is True
    assert [r.id for r in outra.listar_resgates_por_cliente(CLIENTE_B)] == ["rsg_teste002", "rsg_teste001"]


def test_mesma_chave_de_idempotencia_e_barrada_pelo_banco_sem_somar_o_contador():
    repo = SqlBeneficioRepository(SessionLocal)
    repo.salvar_resgate(_resgate("rsg_teste001", "chave-1"))
    with pytest.raises(IntegrityError):
        repo.salvar_resgate(_resgate("rsg_teste002", "chave-1"))
    assert SqlBeneficioRepository(SessionLocal).obter_beneficio("ben_livelo_pontos").total_resgates == 1


def test_catalogo_de_beneficios_na_ordem_do_seed():
    repo = SqlBeneficioRepository(SessionLocal)
    assert [t.chave for t in repo.listar_trilhas()] == ["connect", "movement", "experience"]
    assert repo.listar_beneficios()[0].id == "ben_inter_cashback"
    assert repo.obter_parceiro("par_inter").nome == "Inter"
    with pytest.raises(KeyError):
        repo.obter_parceiro("par_inexistente")


# Indicações, notificações e conteúdo


def test_codigo_de_indicacao_nos_dois_sentidos():
    repo = SqlIndicacaoRepository(SessionLocal)
    repo.salvar_codigo(CLIENTE_B, "BRUNO50")
    outra = SqlIndicacaoRepository(SessionLocal)
    assert outra.codigo_do_cliente(CLIENTE_B) == "BRUNO50"
    assert outra.cliente_do_codigo("ANA50") == CLIENTE_A
    assert outra.cliente_do_codigo("NAOEXISTE") is None


def test_notificacao_lida_fica_gravada():
    repo = SqlNotificacaoRepository(SessionLocal)
    repo.salvar(Notificacao("not_teste001", CLIENTE_A, "pedido_criado", "t", "m", False, AGORA, "pedido", PEDIDO_A))
    with unidade_de_trabalho():
        repo.obter("not_teste001").lida = True
    assert SqlNotificacaoRepository(SessionLocal).obter("not_teste001").lida is True
    assert SqlNotificacaoRepository(SessionLocal).listar_por_cliente(CLIENTE_A)[0].id == "not_teste001"


def test_dicas_com_blocos_em_json_e_boas_vindas_ordenadas():
    dica = SqlAjudaRepository(SessionLocal).listar("simular-desconto")[0]
    assert dica.blocos[3].ordenada is True
    assert dica.blocos[3].itens[1].texto == "Depois disso, aplicamos até 15% de desconto."
    assert SqlAjudaRepository(SessionLocal).listar("status-pedido", "outro-elemento") == []
    conteudo = SqlConteudoRepository(SessionLocal).obter_boas_vindas()
    assert [p.ordem for p in conteudo.passos] == [1, 2, 3]


# Unidade de trabalho


def test_alteracao_fora_de_unidade_de_trabalho_nao_e_gravada():
    repo = SqlNotificacaoRepository(SessionLocal)
    # Sem unidade de trabalho, cada chamada abre e fecha a sua: o objeto devolvido é só uma cópia.
    repo.obter("not_c410aa7b").lida = True
    assert repo.obter("not_c410aa7b").lida is False


def test_dentro_da_unidade_o_mesmo_registro_e_o_mesmo_objeto():
    repo = SqlPedidoRepository(SessionLocal)
    with unidade_de_trabalho():
        assert repo.obter(PEDIDO_A) is repo.obter(PEDIDO_A)
        assert repo.listar_por_cliente(CLIENTE_A)[0] is repo.obter(PEDIDO_A)


def test_consulta_enxerga_alteracao_ainda_nao_confirmada():
    repo = SqlNotificacaoRepository(SessionLocal)
    with unidade_de_trabalho():
        repo.obter("not_c410aa7b").cliente_id = CLIENTE_B
        assert "not_c410aa7b" in [n.id for n in repo.listar_por_cliente(CLIENTE_B)]


def test_erro_dentro_da_unidade_desfaz_tudo():
    repo = SqlAutenticacaoRepository(SessionLocal)
    with pytest.raises(RuntimeError):
        with unidade_de_trabalho():
            repo.salvar(Cliente(id="cli_desfeito", nome="Não grava"))
            repo.obter(CLIENTE_A).nome = "Nome alterado"
            raise RuntimeError("falha no meio da operação")
    assert repo.obter("cli_desfeito") is None
    assert repo.obter(CLIENTE_A).nome == "Ana Souza"
    assert unidade_atual() is None


# Persistência de ponta a ponta: a API grava no banco


def test_dado_criado_pela_api_sobrevive_a_reinicio_da_aplicacao(cliente_http):
    from app.core.estado import reiniciar_estado
    from tests.conftest import cabecalho_de

    corpo = {"valor_fatura_centavos": 30000, "distribuidora": "CEMIG"}
    criada = cliente_http.post("/api/v1/simulacoes", json=corpo, headers=cabecalho_de(CLIENTE_A))
    assert criada.status_code == 201

    # Reiniciar monta repositórios novos, como um uvicorn que acabou de subir: o dado vem do banco.
    reiniciar_estado()
    relogio.definir_relogio(lambda: AGORA)
    lida = cliente_http.get(f"/api/v1/simulacoes/{criada.json()['id']}", headers=cabecalho_de(CLIENTE_A))
    assert lida.status_code == 200
    assert lida.json() == criada.json()


def test_erro_de_negocio_ainda_grava_o_que_o_service_alterou(cliente_http):
    # Reusar um token de renovação revoga a sessão E responde 401: a revogação precisa ir ao banco.
    from tests.conftest import EMAIL_A, SENHA_DEV

    antigo = cliente_http.post("/api/v1/sessoes", json={"identificador": EMAIL_A, "senha": SENHA_DEV}).json()
    novo = cliente_http.post("/api/v1/sessoes/renovacao", json={"token_renovacao": antigo["token_renovacao"]}).json()
    assert cliente_http.post("/api/v1/sessoes/renovacao", json={"token_renovacao": antigo["token_renovacao"]}).status_code == 401
    hash_novo = hashlib.sha256(novo["token_renovacao"].encode()).hexdigest()
    assert SqlSessaoRepository(SessionLocal).obter_por_hash(hash_novo).revogada is True


def test_seed_nao_duplica_quando_o_banco_ja_tem_dados(capsys):
    from app.db import seed

    seed.main()
    assert "Nada a fazer" in capsys.readouterr().out
    assert len(SqlAutenticacaoRepository(SessionLocal).listar()) == 2
