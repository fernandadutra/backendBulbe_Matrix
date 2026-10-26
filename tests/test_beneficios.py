import re
import threading
from datetime import datetime
from uuid import uuid4

from fastapi.testclient import TestClient

from app.core import relogio
from app.core.estado import repositorios
from app.main import app
from tests.conftest import CLIENTE_A, CLIENTE_B, PEDIDO_A, PEDIDO_B, cabecalho_de

INTER = "ben_inter_cashback"
LIVELO = "ben_livelo_pontos"
FROSSARD = "ben_frossard_economia"
MOTIVO_PEDIDO = "Disponível após a aprovação do seu pedido pela Cemig."


def resgatar(cliente_http, cliente_id, beneficio_id, chave=None, corpo=None):
    cabecalhos = cabecalho_de(cliente_id)
    cabecalhos["Idempotency-Key"] = chave or str(uuid4())
    return cliente_http.post(f"/api/v1/beneficios/{beneficio_id}/resgates", headers=cabecalhos, json=corpo)


def viajar_para_2027():
    futuro = datetime(2027, 1, 1, 10, 0, tzinfo=relogio.FUSO)
    relogio.definir_relogio(lambda: futuro)


# Listagem

def test_beneficios_sem_token_401(cliente_http):
    r = cliente_http.get("/api/v1/beneficios")
    assert r.status_code == 401
    assert r.json()["erro"]["codigo"] == "TOKEN_AUSENTE"


def test_lista_traz_os_quatro_beneficios_ativos(cliente_http):
    r = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(CLIENTE_A))
    corpo = r.json()
    assert r.status_code == 200
    assert corpo["total"] == 4 and corpo["pagina"] == 1 and corpo["limite"] == 20
    assert corpo["estado_vazio"] is None
    assert [b["id"] for b in corpo["dados"]] == [INTER, LIVELO, FROSSARD, "ben_araujo_descontos"]


def test_item_inter_formato_da_spec(cliente_http):
    r = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(CLIENTE_A))
    assert r.json()["dados"][0] == {
        "id": INTER,
        "trilha": "connect",
        "parceiro": {
            "id": "par_inter", "nome": "Inter",
            "url_logo": "https://cdn.bulbe.com.br/parceiros/inter.png", "cor_marca": "#ff7200",
        },
        "titulo": "Até 77% de cashback!",
        "descricao": "Cashback em compras realizadas pelo app do Inter.",
        "regras_de_uso": "Válido para novas contas abertas pelo link Bulbe. Cashback creditado em até 60 dias.",
        "condicoes_resgate": {
            "tipo": "uso_unico", "exige_pedido_aprovado": False,
            "elegivel": True, "motivo_inelegibilidade": None,
        },
        "validade": {"inicio": "2026-08-01", "fim": "2026-12-31", "rotulo": "Válido até 31/12/2026"},
        "acao": {"rotulo": "Acessar", "exige_resgate": True},
    }


def test_livelo_inelegivel_para_a_e_elegivel_para_b(cliente_http):
    def livelo(cliente_id):
        r = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(cliente_id))
        return next(b for b in r.json()["dados"] if b["id"] == LIVELO)

    a = livelo(CLIENTE_A)
    assert a["condicoes_resgate"] == {
        "tipo": "recorrente", "exige_pedido_aprovado": True,
        "elegivel": False, "motivo_inelegibilidade": MOTIVO_PEDIDO,
    }
    assert a["validade"] == {"inicio": "2026-08-01", "fim": None, "rotulo": "Sem prazo definido"}
    b = livelo(CLIENTE_B)
    assert b["condicoes_resgate"]["elegivel"] is True
    assert b["condicoes_resgate"]["motivo_inelegibilidade"] is None


def test_filtro_por_trilha_valida(cliente_http):
    r = cliente_http.get("/api/v1/beneficios?trilha=connect", headers=cabecalho_de(CLIENTE_A))
    assert r.json()["total"] == 4


def test_filtro_por_trilha_sem_beneficio_traz_estado_vazio(cliente_http):
    r = cliente_http.get("/api/v1/beneficios?trilha=movement", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json()["dados"] == [] and r.json()["total"] == 0
    assert r.json()["estado_vazio"] == {
        "titulo": "Nenhum benefício disponível agora",
        "mensagem": "Novos benefícios dos parceiros Bulbe aparecem aqui assim que forem liberados.",
    }


def test_filtro_por_trilha_invalida_400(cliente_http):
    r = cliente_http.get("/api/v1/beneficios?trilha=ouro", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 400
    erro = r.json()["erro"]
    assert erro["codigo"] == "PARAMETRO_INVALIDO"
    assert erro["detalhes"][0]["campo"] == "trilha"


def test_paginacao_dos_beneficios(cliente_http):
    r = cliente_http.get("/api/v1/beneficios?pagina=2&limite=3", headers=cabecalho_de(CLIENTE_A))
    assert [b["id"] for b in r.json()["dados"]] == ["ben_araujo_descontos"]
    assert r.json()["total"] == 4


def test_beneficio_expirado_some_da_lista_e_do_detalhe(cliente_http):
    viajar_para_2027()
    r = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(CLIENTE_A))
    ids = [b["id"] for b in r.json()["dados"]]
    assert INTER not in ids and len(ids) == 3
    d = cliente_http.get(f"/api/v1/beneficios/{INTER}", headers=cabecalho_de(CLIENTE_A))
    assert d.status_code == 404
    assert d.json()["erro"]["codigo"] == "BENEFICIO_NAO_ENCONTRADO"


def test_beneficio_desativado_some(cliente_http):
    repositorios.beneficios.obter_beneficio(FROSSARD).ativo = False
    r = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(CLIENTE_A))
    assert FROSSARD not in [b["id"] for b in r.json()["dados"]]
    assert cliente_http.get(f"/api/v1/beneficios/{FROSSARD}", headers=cabecalho_de(CLIENTE_A)).status_code == 404


# Detalhe

def test_detalhe_mesmo_schema_do_item(cliente_http):
    lista = cliente_http.get("/api/v1/beneficios", headers=cabecalho_de(CLIENTE_A)).json()["dados"]
    r = cliente_http.get(f"/api/v1/beneficios/{LIVELO}", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    assert r.json() == lista[1]


def test_detalhe_inexistente_404(cliente_http):
    r = cliente_http.get("/api/v1/beneficios/ben_nada", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "BENEFICIO_NAO_ENCONTRADO"


def test_detalhe_sem_token_401(cliente_http):
    assert cliente_http.get(f"/api/v1/beneficios/{INTER}").status_code == 401


# Trilhas

def trilhas_de(cliente_http, cliente_id):
    r = cliente_http.get("/api/v1/trilhas", headers=cabecalho_de(cliente_id))
    assert r.status_code == 200
    return {t["chave"]: t for t in r.json()["dados"]}


def test_trilhas_sem_token_401(cliente_http):
    assert cliente_http.get("/api/v1/trilhas").status_code == 401


def test_trilhas_formato_e_ordem(cliente_http):
    r = cliente_http.get("/api/v1/trilhas", headers=cabecalho_de(CLIENTE_A))
    assert list(r.json()) == ["dados"]
    assert [t["chave"] for t in r.json()["dados"]] == ["connect", "movement", "experience"]
    connect = r.json()["dados"][0]
    assert connect == {
        "chave": "connect",
        "nome": "Bulbe Connect",
        "descricao": "Cliente possui acesso imediato a benefícios e parceiros.",
        "desbloqueada": True,
        "motivo_bloqueio": None,
        "cor_tema": "verde",
        "url_icone": "https://cdn.bulbe.com.br/trilhas/connect.svg",
        "quantidade_beneficios_ativos": 4,
        "parceiros_destaque": [
            {"id": "par_araujo", "nome": "Araújo", "url_logo": "https://cdn.bulbe.com.br/parceiros/araujo.png"},
            {"id": "par_inter", "nome": "Inter", "url_logo": "https://cdn.bulbe.com.br/parceiros/inter.png"},
        ],
    }


def test_trilhas_desbloqueio_do_cliente_a(cliente_http):
    t = trilhas_de(cliente_http, CLIENTE_A)
    assert t["connect"]["desbloqueada"] is True
    assert t["movement"]["desbloqueada"] is False
    assert t["movement"]["motivo_bloqueio"] == MOTIVO_PEDIDO
    assert t["movement"]["cor_tema"] == "azul"
    assert t["movement"]["quantidade_beneficios_ativos"] == 0
    assert t["movement"]["parceiros_destaque"] == []
    assert t["experience"]["desbloqueada"] is False
    assert t["experience"]["motivo_bloqueio"] == "Disponível para clientes com fatura Bulbe ativa."
    assert t["experience"]["cor_tema"] == "laranja"


def test_trilhas_desbloqueio_do_cliente_b(cliente_http):
    t = trilhas_de(cliente_http, CLIENTE_B)
    assert t["movement"]["desbloqueada"] is True
    assert t["movement"]["motivo_bloqueio"] is None
    assert t["experience"]["desbloqueada"] is True


def test_trilha_nao_conta_beneficio_expirado(cliente_http):
    viajar_para_2027()
    t = trilhas_de(cliente_http, CLIENTE_A)
    assert t["connect"]["quantidade_beneficios_ativos"] == 3
    assert [p["nome"] for p in t["connect"]["parceiros_destaque"]] == ["Araújo"]


# Resgate

def test_resgate_sem_token_401(cliente_http):
    r = cliente_http.post(f"/api/v1/beneficios/{INTER}/resgates", headers={"Idempotency-Key": str(uuid4())})
    assert r.status_code == 401


def test_resgate_201_formato_da_spec(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, INTER)
    assert r.status_code == 201
    corpo = r.json()
    assert list(corpo) == ["id", "beneficio_id", "resgatado_em", "situacao", "instrucoes", "codigo", "url_acesso", "expira_em"]
    assert re.fullmatch(r"rsg_[0-9a-f]{8}", corpo["id"])
    assert corpo["beneficio_id"] == INTER
    assert corpo["resgatado_em"] == "2026-10-21T10:00:00-03:00"
    assert corpo["situacao"] == "confirmado"
    assert corpo["instrucoes"] == "Abra o app do Inter e finalize a abertura da conta em até 7 dias para garantir o cashback."
    assert re.fullmatch(r"BULBE-INTER-[A-Z0-9]{4}", corpo["codigo"])
    assert corpo["url_acesso"] == f"https://parceiros.bulbe.com.br/inter/redirecionamento?rsg={corpo['id']}"
    assert corpo["expira_em"] == "2026-10-28T23:59:59-03:00"


def test_resgate_sem_corpo_e_com_corpo_vazio(cliente_http):
    assert resgatar(cliente_http, CLIENTE_A, INTER).status_code == 201
    assert resgatar(cliente_http, CLIENTE_A, "ben_araujo_descontos", corpo={}).status_code == 201


def test_mesma_chave_devolve_o_mesmo_resgate(cliente_http):
    chave = str(uuid4())
    primeiro = resgatar(cliente_http, CLIENTE_A, INTER, chave)
    segundo = resgatar(cliente_http, CLIENTE_A, INTER, chave)
    assert primeiro.status_code == segundo.status_code == 201
    assert primeiro.json() == segundo.json()
    assert repositorios.beneficios.obter_beneficio(INTER).total_resgates == 1


def test_chave_reutilizada_em_outro_beneficio_422(cliente_http):
    chave = str(uuid4())
    assert resgatar(cliente_http, CLIENTE_A, INTER, chave).status_code == 201
    r = resgatar(cliente_http, CLIENTE_A, FROSSARD, chave)
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "CHAVE_DE_IDEMPOTENCIA_REUTILIZADA"
    assert repositorios.beneficios.obter_beneficio(FROSSARD).total_resgates == 0


def test_chave_de_outro_cliente_nao_colide(cliente_http):
    chave = str(uuid4())
    a = resgatar(cliente_http, CLIENTE_A, INTER, chave)
    b = resgatar(cliente_http, CLIENTE_B, INTER, chave)
    assert a.status_code == b.status_code == 201
    assert a.json()["id"] != b.json()["id"]


def test_resgate_sem_chave_400(cliente_http):
    r = cliente_http.post(f"/api/v1/beneficios/{INTER}/resgates", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "IDEMPOTENCY_KEY_INVALIDA"


def test_resgate_chave_que_nao_e_uuid_400(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, INTER, chave="abc-123")
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "IDEMPOTENCY_KEY_INVALIDA"


def test_uso_unico_segunda_vez_com_outra_chave_409(cliente_http):
    assert resgatar(cliente_http, CLIENTE_A, INTER).status_code == 201
    r = resgatar(cliente_http, CLIENTE_A, INTER)
    assert r.status_code == 409
    assert r.json()["erro"]["codigo"] == "BENEFICIO_JA_RESGATADO"
    assert repositorios.beneficios.obter_beneficio(INTER).total_resgates == 1


def test_uso_unico_de_um_cliente_nao_bloqueia_outro(cliente_http):
    assert resgatar(cliente_http, CLIENTE_A, INTER).status_code == 201
    assert resgatar(cliente_http, CLIENTE_B, INTER).status_code == 201


def test_recorrente_pode_ser_resgatado_duas_vezes(cliente_http):
    primeiro = resgatar(cliente_http, CLIENTE_B, LIVELO)
    segundo = resgatar(cliente_http, CLIENTE_B, LIVELO)
    assert primeiro.status_code == segundo.status_code == 201
    assert primeiro.json()["id"] != segundo.json()["id"]
    assert re.fullmatch(r"BULBE-LIVELO-[A-Z0-9]{4}", primeiro.json()["codigo"])
    assert repositorios.beneficios.obter_beneficio(LIVELO).total_resgates == 2


def test_inelegivel_422_com_o_motivo(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, LIVELO)
    assert r.status_code == 422
    assert r.json()["erro"]["codigo"] == "CLIENTE_NAO_ELEGIVEL"
    assert r.json()["erro"]["mensagem"] == MOTIVO_PEDIDO
    assert repositorios.beneficios.obter_beneficio(LIVELO).total_resgates == 0
    assert cliente_http.get("/api/v1/resgates", headers=cabecalho_de(CLIENTE_A)).json()["total"] == 0


def test_resgate_expirado_410(cliente_http):
    viajar_para_2027()
    r = resgatar(cliente_http, CLIENTE_A, INTER)
    assert r.status_code == 410
    assert r.json()["erro"]["codigo"] == "BENEFICIO_EXPIRADO"
    assert r.json()["erro"]["mensagem"] == "Este benefício não está mais disponível. Atualize a lista para ver as ofertas atuais."


def test_resgate_desativado_410(cliente_http):
    repositorios.beneficios.obter_beneficio(FROSSARD).ativo = False
    assert resgatar(cliente_http, CLIENTE_A, FROSSARD).status_code == 410


def test_resgate_de_beneficio_que_ainda_nao_comecou_404(cliente_http):
    from datetime import date
    repositorios.beneficios.obter_beneficio(INTER).validade_inicio = date(2026, 11, 1)
    r = resgatar(cliente_http, CLIENTE_A, INTER)
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "BENEFICIO_NAO_ENCONTRADO"
    assert cliente_http.get(f"/api/v1/beneficios/{INTER}", headers=cabecalho_de(CLIENTE_A)).status_code == 404


def test_resgate_inexistente_404(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, "ben_nada")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "BENEFICIO_NAO_ENCONTRADO"


def test_pedido_id_de_outro_cliente_404(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, INTER, corpo={"pedido_id": PEDIDO_B})
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "PEDIDO_NAO_ENCONTRADO"


def test_pedido_id_inexistente_404(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, INTER, corpo={"pedido_id": "ped_nada"})
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "PEDIDO_NAO_ENCONTRADO"


def test_pedido_id_proprio_e_aprovado_libera_o_resgate(cliente_http):
    assert resgatar(cliente_http, CLIENTE_B, LIVELO, corpo={"pedido_id": PEDIDO_B}).status_code == 201


def test_pedido_id_proprio_mas_nao_aprovado_422(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, LIVELO, corpo={"pedido_id": PEDIDO_A})
    assert r.status_code == 422
    assert r.json()["erro"]["mensagem"] == MOTIVO_PEDIDO


def test_pedido_id_com_tipo_errado_400(cliente_http):
    r = resgatar(cliente_http, CLIENTE_A, INTER, corpo={"pedido_id": 10})
    assert r.status_code == 400
    assert r.json()["erro"]["codigo"] == "CORPO_INVALIDO"


def test_idempotencia_devolve_o_resgate_mesmo_com_beneficio_expirado(cliente_http):
    chave = str(uuid4())
    primeiro = resgatar(cliente_http, CLIENTE_A, INTER, chave)
    viajar_para_2027()
    segundo = resgatar(cliente_http, CLIENTE_A, INTER, chave)
    assert segundo.status_code == 201
    assert segundo.json() == primeiro.json()


def test_dois_resgates_simultaneos_de_uso_unico_geram_um_so(cliente_http):
    resultados = []
    largada = threading.Barrier(8)

    def disparar():
        largada.wait()
        resultados.append(resgatar(cliente_http, CLIENTE_A, INTER).status_code)

    threads = [threading.Thread(target=disparar) for _ in range(8)]
    for t in threads:
        t.start()
    for t in threads:
        t.join()
    assert sorted(resultados) == [201] + [409] * 7
    assert repositorios.beneficios.obter_beneficio(INTER).total_resgates == 1


def test_falha_ao_gravar_nao_deixa_resgate_nem_contador():
    class ChavesQuebradas(dict):
        def __setitem__(self, *_):
            raise RuntimeError("falha simulada")

    repositorios.beneficios._chaves = ChavesQuebradas()
    erro = TestClient(app, raise_server_exceptions=False)
    cabecalhos = {**cabecalho_de(CLIENTE_A), "Idempotency-Key": str(uuid4())}
    r = erro.post(f"/api/v1/beneficios/{INTER}/resgates", headers=cabecalhos)
    assert r.status_code == 500
    assert repositorios.beneficios.obter_beneficio(INTER).total_resgates == 0
    assert repositorios.beneficios.listar_resgates_por_cliente(CLIENTE_A) == []
    assert not repositorios.beneficios.trava.locked()


# Meus resgates

def test_resgates_sem_token_401(cliente_http):
    assert cliente_http.get("/api/v1/resgates").status_code == 401


def test_resgates_so_do_cliente_e_mais_recentes_primeiro(cliente_http):
    primeiro = resgatar(cliente_http, CLIENTE_A, INTER).json()
    segundo = resgatar(cliente_http, CLIENTE_A, FROSSARD).json()
    resgatar(cliente_http, CLIENTE_B, LIVELO)
    r = cliente_http.get("/api/v1/resgates", headers=cabecalho_de(CLIENTE_A))
    assert r.status_code == 200
    corpo = r.json()
    assert (corpo["pagina"], corpo["limite"], corpo["total"]) == (1, 20, 2)
    assert [d["id"] for d in corpo["dados"]] == [segundo["id"], primeiro["id"]]
    assert corpo["dados"][1] == {
        "id": primeiro["id"],
        "beneficio_id": INTER,
        "beneficio_titulo": "Até 77% de cashback!",
        "parceiro_nome": "Inter",
        "resgatado_em": primeiro["resgatado_em"],
        "situacao": "confirmado",
        "codigo": primeiro["codigo"],
        "expira_em": primeiro["expira_em"],
    }


def test_resgates_vazio_para_quem_nao_resgatou(cliente_http):
    resgatar(cliente_http, CLIENTE_A, INTER)
    r = cliente_http.get("/api/v1/resgates", headers=cabecalho_de(CLIENTE_B))
    assert r.json()["dados"] == [] and r.json()["total"] == 0


def test_contador_incrementa_uma_vez_por_resgate(cliente_http):
    chave = str(uuid4())
    resgatar(cliente_http, CLIENTE_B, LIVELO, chave)
    resgatar(cliente_http, CLIENTE_B, LIVELO, chave)
    resgatar(cliente_http, CLIENTE_B, LIVELO)
    assert repositorios.beneficios.obter_beneficio(LIVELO).total_resgates == 2
