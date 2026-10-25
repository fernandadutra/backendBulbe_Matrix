from fastapi import FastAPI

from app.controllers import ajuda_controller, beneficios_controller, pedidos_controller, simulacoes_controller
from app.core.erros import registrar_tratadores

app = FastAPI(
    title="Bulbe Energia - API da Jornada do Cliente",
    description="""
    Backend RESTful para gestão da retenção de clientes, simulação de economia 
    e acompanhamento da jornada de homologação CEMIG (90 a 120 dias).
    """,
    version="1.0.0",
    openapi_tags=[
        {"name": "Simulações", "description": "Cálculo de estimativa de desconto na conta de luz"},
        {"name": "Jornada do Cliente", "description": "Status do pedido e timeline da homologação CEMIG"},
        {"name": "Clube de Benefícios", "description": "Trilhas, benefícios dos parceiros e resgates"},
        {"name": "Ajuda", "description": "Textos de ajuda contextual por tela"},
    ],
)

registrar_tratadores(app)
app.include_router(pedidos_controller.router, prefix="/api/v1")
app.include_router(simulacoes_controller.router, prefix="/api/v1")
app.include_router(beneficios_controller.router, prefix="/api/v1")
app.include_router(ajuda_controller.router, prefix="/api/v1")


@app.get("/", tags=["Healthcheck"])
def inicio():
    return {"mensagem": "API Bulbe funcionando com sucesso!"}


def _openapi_sem_422_automatico():
    if app.openapi_schema is None:
        esquema = FastAPI.openapi(app)
        # O handler devolve 400 no envelope Erro, então o 422 automático do FastAPI não vale.
        # O 422 de regra de negócio (schema Erro) é mantido.
        for caminho in esquema["paths"].values():
            for operacao in caminho.values():
                resposta = operacao.get("responses", {}).get("422")
                if resposta and "HTTPValidationError" in str(resposta):
                    del operacao["responses"]["422"]
        componentes = esquema.get("components", {}).get("schemas", {})
        componentes.pop("HTTPValidationError", None)
        componentes.pop("ValidationError", None)
    return app.openapi_schema


app.openapi = _openapi_sem_422_automatico
