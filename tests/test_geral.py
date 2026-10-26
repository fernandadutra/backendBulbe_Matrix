def test_healthcheck(cliente_http):
    assert cliente_http.get("/").status_code == 200


def test_rota_inexistente_404_no_envelope(cliente_http):
    r = cliente_http.get("/api/v1/nada")
    assert r.status_code == 404
    assert r.json()["erro"]["codigo"] == "ROTA_NAO_ENCONTRADA"
    assert r.json()["erro"]["detalhes"] is None


def test_metodo_nao_permitido_405_no_envelope(cliente_http):
    r = cliente_http.delete("/api/v1/simulacoes")
    assert r.status_code == 405
    assert r.json()["erro"]["codigo"] == "METODO_NAO_PERMITIDO"


def test_erro_interno_500_sem_vazar_detalhes():
    from fastapi.testclient import TestClient
    from app.main import app

    @app.get("/_explode_teste")
    def explode():
        raise RuntimeError("segredo interno")

    try:
        r = TestClient(app, raise_server_exceptions=False).get("/_explode_teste")
    finally:
        app.router.routes.pop()
    assert r.status_code == 500
    assert r.json()["erro"]["codigo"] == "ERRO_INTERNO"
    assert "segredo" not in r.text


def test_openapi_sem_validacao_automatica_do_fastapi(cliente_http):
    r = cliente_http.get("/openapi.json")
    assert r.status_code == 200
    assert "HTTPValidationError" not in r.text
    esquemas = r.json()["components"]["schemas"]
    for nome in ("Erro", "EtapaPedido", "MemoriaCalculo"):
        assert nome in esquemas
    assert any(n.startswith("Paginacao") for n in esquemas)
    assert "/api/v1/simulacoes" in r.json()["paths"]
    for caminho in ("/api/v1/sessoes", "/api/v1/sessoes/renovacao", "/api/v1/perfil"):
        assert caminho in r.json()["paths"]
    for caminho in ("/api/v1/interessados", "/api/v1/adesoes/{id}/submissao"):
        assert caminho in r.json()["paths"]
    assert "/v1/usinas" not in r.json()["paths"]
