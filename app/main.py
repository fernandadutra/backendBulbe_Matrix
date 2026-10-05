from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field
from typing import List, Optional

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
        {"name": "Usinas", "description": "Gestão e consulta do parque de geração solar"}
    ]
)

class SimulacaoRequest(BaseModel):
    valor_conta_luz: float = Field(..., gt=0, example=350.00, description="Valor médio da fatura em R$")
    distribuidora: str = Field(default="CEMIG", example="CEMIG")

class SimulacaoResponse(BaseModel):
    valor_original: float = Field(..., example=350.00)
    percentual_desconto: float = Field(..., example=0.15)
    valor_com_desconto: float = Field(..., example=297.50)
    economia_anual_estimada: float = Field(..., example=630.00)

class PedidoStatusResponse(BaseModel):
    pedido_id: int = Field(..., example=101)
    cliente_id: int = Field(..., example=42)
    etapa_atual: str = Field(..., example="Em análise técnica pela CEMIG")
    dias_restantes_estimados: int = Field(..., example=45)
    concluido: bool = Field(..., example=False)

class UsinaResponse(BaseModel):
    id: int = Field(..., example=1)
    nome: str = Field(..., example="Usina Solar Montes Claros")
    capacidade_kwh: float = Field(..., example=15000.0)
    status: str = Field(..., example="ativa")

@app.get("/", tags=["Healthcheck"])
def inicio():
    return {"mensagem": "API Bulbe funcionando com sucesso!"}

@app.post(
    "/v1/simulacoes", 
    response_model=SimulacaoResponse, 
    status_code=status.HTTP_201_CREATED, 
    tags=["Simulações"],
    summary="Calcular economia estimada"
)
def criar_simulacao(dados: SimulacaoRequest):
    desconto = dados.valor_conta_luz * 0.15
    valor_final = dados.valor_conta_luz - desconto
    return {
        "valor_original": dados.valor_conta_luz,
        "percentual_desconto": 0.15,
        "valor_com_desconto": round(valor_final, 2),
        "economia_anual_estimada": round(desconto * 12, 2)
    }

@app.get(
    "/v1/pedidos/{pedido_id}/status", 
    response_model=PedidoStatusResponse, 
    tags=["Jornada do Cliente"],
    summary="Acompanhar status da homologação"
)
def obter_status_pedido(pedido_id: int):
    return {
        "pedido_id": pedido_id,
        "cliente_id": 42,
        "etapa_atual": "Em análise técnica pela CEMIG",
        "dias_restantes_estimados": 45,
        "concluido": False
    }

@app.get(
    "/v1/usinas", 
    response_model=List[UsinaResponse], 
    tags=["Usinas"],
    summary="Listar usinas solares"
)
def listar_usinas():
    return [
        {"id": 1, "nome": "Usina Montes Claros I", "capacidade_kwh": 25000.0, "status": "ativa"},
        {"id": 2, "nome": "Usina Pirapora II", "capacidade_kwh": 40000.0, "status": "ativa"}
    ]