from datetime import date, datetime
from typing import List, Optional

from pydantic import BaseModel, Field, StrictStr

from app.schemas.comum import Paginacao


class ParceiroBeneficio(BaseModel):
    id: str = Field(examples=["par_inter"])
    nome: str = Field(examples=["Inter"])
    url_logo: str = Field(examples=["https://cdn.bulbe.com.br/parceiros/inter.png"])
    cor_marca: str = Field(examples=["#ff7200"])


class CondicoesResgate(BaseModel):
    tipo: str = Field(examples=["uso_unico"], description="uso_unico ou recorrente")
    exige_pedido_aprovado: bool
    elegivel: bool
    motivo_inelegibilidade: Optional[str] = Field(examples=["Disponível após a aprovação do seu pedido pela Cemig."])


class ValidadeBeneficio(BaseModel):
    inicio: date = Field(examples=["2026-08-01"])
    fim: Optional[date] = Field(examples=["2026-12-31"])
    rotulo: str = Field(examples=["Válido até 31/12/2026"])


class AcaoBeneficio(BaseModel):
    rotulo: str = Field(examples=["Acessar"])
    exige_resgate: bool


class Beneficio(BaseModel):
    id: str = Field(examples=["ben_inter_cashback"])
    trilha: str = Field(examples=["connect"], description="connect, movement ou experience")
    parceiro: ParceiroBeneficio
    titulo: str = Field(examples=["Até 77% de cashback!"])
    descricao: str
    regras_de_uso: str
    condicoes_resgate: CondicoesResgate
    validade: ValidadeBeneficio
    acao: AcaoBeneficio


class EstadoVazio(BaseModel):
    titulo: str = Field(examples=["Nenhum benefício disponível agora"])
    mensagem: str = Field(examples=["Novos benefícios dos parceiros Bulbe aparecem aqui assim que forem liberados."])


class PaginaBeneficios(Paginacao[Beneficio]):
    estado_vazio: Optional[EstadoVazio] = Field(
        default=None, description="Só vem preenchido quando dados está vazio."
    )


class ParceiroDestaque(BaseModel):
    id: str = Field(examples=["par_araujo"])
    nome: str = Field(examples=["Araújo"])
    url_logo: str = Field(examples=["https://cdn.bulbe.com.br/parceiros/araujo.png"])


class Trilha(BaseModel):
    chave: str = Field(examples=["connect"])
    nome: str = Field(examples=["Bulbe Connect"])
    descricao: str
    desbloqueada: bool
    motivo_bloqueio: Optional[str] = Field(examples=["Disponível após a aprovação do seu pedido pela Cemig."])
    cor_tema: str = Field(examples=["verde"])
    url_icone: str = Field(examples=["https://cdn.bulbe.com.br/trilhas/connect.svg"])
    quantidade_beneficios_ativos: int = Field(examples=[4])
    parceiros_destaque: List[ParceiroDestaque]


class ListaTrilhas(BaseModel):
    dados: List[Trilha]


class ResgateRequisicao(BaseModel):
    pedido_id: Optional[StrictStr] = Field(default=None, examples=["ped_7f3a9c21"])


class ResgateCriado(BaseModel):
    id: str = Field(examples=["rsg_5e02a7cc"])
    beneficio_id: str = Field(examples=["ben_inter_cashback"])
    resgatado_em: datetime = Field(examples=["2026-08-23T14:31:12-03:00"])
    situacao: str = Field(examples=["confirmado"])
    instrucoes: str
    codigo: str = Field(examples=["BULBE-INTER-8F2K"])
    url_acesso: str
    expira_em: datetime = Field(examples=["2026-08-30T23:59:59-03:00"])


class ResgateResumo(BaseModel):
    id: str = Field(examples=["rsg_5e02a7cc"])
    beneficio_id: str = Field(examples=["ben_inter_cashback"])
    beneficio_titulo: str = Field(examples=["Até 77% de cashback!"])
    parceiro_nome: str = Field(examples=["Inter"])
    resgatado_em: datetime
    situacao: str
    codigo: str
    expira_em: datetime
