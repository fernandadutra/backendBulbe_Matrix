from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, StrictBool, StrictStr

from app.schemas.pedido import PrazoEstimado


class InteressadoRequisicao(BaseModel):
    # Tipos estritos. Formato de e-mail e existência da simulação são validados no service.
    nome: StrictStr = Field(examples=["Maria Souza"])
    email: StrictStr = Field(examples=["cliente@exemplo.com.br"])
    whatsapp: StrictStr = Field(examples=["+5531999998888"])
    simulacao_id: Optional[StrictStr] = Field(default=None, examples=["sim_2c81b40e"])
    aceite_comunicacoes: StrictBool = Field(examples=[True], description="Consentimento de marketing, distinto do aceite dos termos.")


class InteressadoResposta(BaseModel):
    id: str = Field(examples=["int_18c4a70b"])
    situacao: str = Field(examples=["novo"], description="novo ou convertido")
    token_fluxo: str = Field(examples=["tfl_c93b21ee..."], description="Enviar em `Authorization: Bearer` nas rotas de adesão.")
    expira_em: datetime = Field(examples=["2026-08-24T14:30:00-03:00"])


class AdesaoRequisicao(BaseModel):
    interessado_id: StrictStr = Field(examples=["int_18c4a70b"])


class EtapaRequisicao(BaseModel):
    etapa: StrictStr = Field(examples=["negocio"], description="contato ou negocio")
    dados: Dict[str, Any] = Field(
        examples=[
            {
                "numero_instalacao": "3013588579",
                "distribuidora": "CEMIG",
                "titular_nome": "Maria Souza",
                "titular_documento": "00000000000",
                "cep": "30140071",
                "classe_consumo": "residencial",
            }
        ]
    )


class AdesaoResposta(BaseModel):
    id: str = Field(examples=["ade_6b2f9013"])
    situacao: str = Field(examples=["em_preenchimento"], description="em_preenchimento ou submetida")
    etapa_atual: str = Field(examples=["contato"])
    etapas_concluidas: List[str] = Field(examples=[["contato"]])
    etapas_pendentes: List[str] = Field(examples=[["negocio", "termos", "confirmacao"]])


class DadosExtraidos(BaseModel):
    numero_instalacao: str = Field(examples=["3013588579"])
    valor_centavos: int = Field(examples=[35000])
    consumo_kwh: int = Field(examples=[249])
    confianca: float = Field(examples=[0.92])


class AnexoResposta(BaseModel):
    id: str = Field(examples=["anx_4a71cc80"])
    tipo: str = Field(examples=["fatura_energia"])
    nome_arquivo: str = Field(examples=["fatura-junho.pdf"])
    tamanho_bytes: int = Field(examples=[284193])
    situacao: str = Field(examples=["recebido"])
    recebido_em: datetime = Field(examples=["2026-08-23T14:35:00-03:00"])
    dados_extraidos: Optional[DadosExtraidos] = Field(default=None, description="Sempre nulo: ainda não há leitura automática da fatura.")


class AceiteRequisicao(BaseModel):
    aceite_termo_adesao: StrictBool = Field(examples=[True])
    aceite_politica_privacidade: StrictBool = Field(examples=[True])
    versao_documentos: StrictStr = Field(examples=["2026-07-01"])
    aceito_em: datetime = Field(examples=["2026-08-23T14:36:00-03:00"])


class SubmissaoRequisicao(BaseModel):
    # Tamanho mínimo da senha é regra de negócio, validada no service.
    senha: StrictStr = Field(examples=["********"])
    aceite_compartilhamento_dados: StrictBool = Field(examples=[True])


class SubmissaoResposta(BaseModel):
    adesao_id: str = Field(examples=["ade_6b2f9013"])
    cliente_id: str = Field(examples=["cli_3f81aa02"])
    pedido_id: str = Field(examples=["ped_7f3a9c21"])
    situacao: str = Field(examples=["submetida"])
    prazo_estimado_dias: PrazoEstimado
    mensagem: str = Field(examples=["Recebemos sua adesão. A homologação junto à Cemig leva de 90 a 120 dias e você pode acompanhar cada etapa pelo app."])
