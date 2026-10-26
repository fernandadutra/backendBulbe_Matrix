URL = "/api/v1/conteudos/boas-vindas"


def test_boas_vindas_conteudo_exato_do_contrato(cliente_http):
    r = cliente_http.get(URL)
    assert r.status_code == 200
    assert r.json() == {
        "versao": "2026-08-01",
        "titulo": "Como funciona",
        "passos": [
            {
                "ordem": 1,
                "titulo": "Energia solar que gera economia",
                "texto": "Nossas fazendas solares produzem energia limpa e renovável.",
                "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-1.svg",
                "texto_alternativo": "Painéis solares em uma fazenda solar",
            },
            {
                "ordem": 2,
                "titulo": "Energia que chega até você",
                "texto": "Essa energia solar é enviada para a rede de distribuição da CEMIG.",
                "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-2.svg",
                "texto_alternativo": "Linhas de transmissão levando energia à rede da distribuidora",
            },
            {
                "ordem": 3,
                "titulo": "Créditos que viram desconto na sua conta de luz",
                "texto": "A energia chega em forma de créditos que se transformam em desconto.",
                "url_ilustracao": "https://cdn.bulbe.com.br/boas-vindas/passo-3.svg",
                "texto_alternativo": "Fatura de energia com valor reduzido pelo desconto",
            },
        ],
    }


def test_passos_em_ordem(cliente_http):
    passos = cliente_http.get(URL).json()["passos"]
    assert [p["ordem"] for p in passos] == [1, 2, 3]


def test_cache_control_presente(cliente_http):
    assert cliente_http.get(URL).headers["cache-control"] == "public, max-age=300"


def test_funciona_sem_token(cliente_http):
    assert "authorization" not in cliente_http.headers
    assert cliente_http.get(URL).status_code == 200


def test_token_enviado_e_ignorado(cliente_http):
    r = cliente_http.get(URL, headers={"Authorization": "Bearer qualquer-coisa"})
    assert r.status_code == 200
    assert r.json()["versao"] == "2026-08-01"
