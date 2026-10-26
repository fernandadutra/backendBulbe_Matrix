from typing import Dict, Generic, List, Optional, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class DetalheErro(BaseModel):
    campo: str = Field(examples=["valor_fatura_centavos"])
    problema: str = Field(examples=["abaixo do mínimo aceito"])


class CorpoErro(BaseModel):
    codigo: str = Field(examples=["CONSUMO_FORA_DA_FAIXA"])
    mensagem: str = Field(examples=["O valor da fatura deve estar entre R$ 50,00 e R$ 5.000,00."])
    detalhes: Optional[List[DetalheErro]] = Field(default=None, description="Só vem preenchido em erro de validação.")


class Erro(BaseModel):
    erro: CorpoErro


class Paginacao(BaseModel, Generic[T]):
    dados: List[T]
    pagina: int = Field(examples=[1])
    limite: int = Field(examples=[20])
    total: int = Field(examples=[1])


_DESCRICOES = {
    400: "Corpo malformado ou parâmetro inválido.",
    401: "Token ausente, expirado ou inválido.",
    404: "Recurso inexistente ou não pertencente ao cliente autenticado.",
    409: "Conflito com o estado atual do recurso.",
    410: "Recurso que deixou de estar disponível.",
    413: "Arquivo acima do tamanho máximo permitido.",
    415: "Formato de arquivo não suportado.",
    422: "Regra de negócio violada.",
    429: "Limite de requisições excedido.",
    503: "Dependência externa indisponível sem dado em cache.",
}


def respostas_de_erro(*codigos: int) -> Dict[int, dict]:
    return {c: {"model": Erro, "description": _DESCRICOES[c]} for c in codigos}
