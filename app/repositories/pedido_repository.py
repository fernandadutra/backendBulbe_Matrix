"""
Camada de Persistência, repositórios de Pedido (e das faturas ligadas a ele).
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.

As etapas da homologação ficam na tabela filha etapas_pedido.
"""

from datetime import datetime
from typing import Iterable, List, Optional, Protocol

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import EtapaPedidoModel, FaturaModel, PedidoModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.fatura import Fatura
from app.models.pedido import Etapa, Pedido

_CAMPOS_PEDIDO = (
    "cliente_id", "numero_instalacao", "distribuidora", "situacao", "criado_em", "previsao_proxima_atualizacao",
    "consultado_em",
)
_CAMPOS_ETAPA = ("chave", "nome", "descricao", "situacao", "iniciada_em", "concluida_em")
_CAMPOS_FATURA = (
    "cliente_id", "pedido_id", "competencia", "vencimento", "valor_centavos", "economia_centavos", "consumo_kwh",
    "situacao", "linha_digitavel", "url_pdf",
)


class PedidoRepository(Protocol):
    def listar_por_cliente(self, cliente_id: str) -> List[Pedido]: ...
    def obter(self, pedido_id: str) -> Optional[Pedido]: ...
    def cliente_tem_pedido_aprovado(self, cliente_id: str) -> bool: ...
    def salvar_consulta(self, pedido: Pedido, etapas: List[Etapa], consultado_em: datetime) -> None: ...
    def salvar(self, pedido: Pedido) -> None: ...
    def listar_faturas_por_cliente(self, cliente_id: str) -> List[Fatura]: ...
    def obter_fatura(self, fatura_id: str) -> Optional[Fatura]: ...


class InMemoryPedidoRepository:
    def __init__(self, pedidos: Iterable[Pedido] = (), faturas: Iterable[Fatura] = ()):
        self._pedidos = list(pedidos)
        self._faturas = list(faturas)

    def listar_por_cliente(self, cliente_id: str) -> List[Pedido]:
        do_cliente = [p for p in self._pedidos if p.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda p: p.criado_em, reverse=True)

    def obter(self, pedido_id: str) -> Optional[Pedido]:
        return next((p for p in self._pedidos if p.id == pedido_id), None)

    def cliente_tem_pedido_aprovado(self, cliente_id: str) -> bool:
        return any(p.cliente_id == cliente_id and p.situacao == "aprovado" for p in self._pedidos)

    def salvar_consulta(self, pedido: Pedido, etapas: List[Etapa], consultado_em: datetime) -> None:
        pedido.etapas = etapas
        pedido.consultado_em = consultado_em

    def salvar(self, pedido: Pedido) -> None:
        self._pedidos.append(pedido)

    def listar_faturas_por_cliente(self, cliente_id: str) -> List[Fatura]:
        do_cliente = [f for f in self._faturas if f.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda f: f.competencia, reverse=True)

    def obter_fatura(self, fatura_id: str) -> Optional[Fatura]:
        return next((f for f in self._faturas if f.id == fatura_id), None)

    def salvar_fatura(self, fatura: Fatura) -> None:
        self._faturas.append(fatura)


# Conversões


def _pedido_para_dominio(m: PedidoModel) -> Pedido:
    etapas = [Etapa(ordem=e.ordem, **{c: getattr(e, c) for c in _CAMPOS_ETAPA}) for e in m.etapas]
    return Pedido(id=m.id, etapas=etapas, **{c: getattr(m, c) for c in _CAMPOS_PEDIDO})


def _gravar_pedido(sessao: Session, p: Pedido) -> None:
    modelo = sessao.get(PedidoModel, p.id)
    if modelo is None:
        modelo = PedidoModel(id=p.id, ordem_gravacao=proxima_ordem(sessao, PedidoModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(p, c) for c in _CAMPOS_PEDIDO})

    # Etapas identificadas pela ordem (1 a 4): atualiza as que existem, cria as novas, apaga as que saíram.
    guardadas = {e.ordem: e for e in modelo.etapas}
    for etapa in p.etapas:
        linha = guardadas.pop(etapa.ordem, None)
        if linha is None:
            linha = EtapaPedidoModel(ordem=etapa.ordem)
            modelo.etapas.append(linha)
        copiar_campos(linha, **{c: getattr(etapa, c) for c in _CAMPOS_ETAPA})
    for sobrando in guardadas.values():
        modelo.etapas.remove(sobrando)


def _fatura_para_dominio(m: FaturaModel) -> Fatura:
    return Fatura(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_FATURA})


def _gravar_fatura(sessao: Session, f: Fatura) -> None:
    modelo = sessao.get(FaturaModel, f.id)
    if modelo is None:
        modelo = FaturaModel(id=f.id, ordem_gravacao=proxima_ordem(sessao, FaturaModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(f, c) for c in _CAMPOS_FATURA})


class SqlPedidoRepository(RepositorioSql):
    def _entregar(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Pedido, modelo.id) or u.rastrear(_pedido_para_dominio(modelo), modelo.id, _gravar_pedido)

    def _entregar_fatura(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Fatura, modelo.id) or u.rastrear(_fatura_para_dominio(modelo), modelo.id, _gravar_fatura)

    def listar_por_cliente(self, cliente_id: str) -> List[Pedido]:
        with self._unidade() as u:
            consulta = (
                select(PedidoModel)
                .where(PedidoModel.cliente_id == cliente_id)
                .order_by(PedidoModel.criado_em.desc(), PedidoModel.ordem_gravacao)
            )
            return [self._entregar(u, m) for m in u.sessao.scalars(consulta)]

    def obter(self, pedido_id: str) -> Optional[Pedido]:
        with self._unidade() as u:
            return self._entregar(u, u.sessao.get(PedidoModel, pedido_id))

    def cliente_tem_pedido_aprovado(self, cliente_id: str) -> bool:
        with self._unidade() as u:
            consulta = select(PedidoModel.id).where(
                PedidoModel.cliente_id == cliente_id, PedidoModel.situacao == "aprovado"
            )
            return u.sessao.scalars(consulta).first() is not None

    def salvar_consulta(self, pedido: Pedido, etapas: List[Etapa], consultado_em: datetime) -> None:
        with self._unidade() as u:
            pedido.etapas = etapas
            pedido.consultado_em = consultado_em
            _gravar_pedido(u.sessao, pedido)
            u.sessao.flush()
            u.rastrear(pedido, pedido.id, _gravar_pedido)

    def salvar(self, pedido: Pedido) -> None:
        with self._unidade() as u:
            _gravar_pedido(u.sessao, pedido)
            u.sessao.flush()
            u.rastrear(pedido, pedido.id, _gravar_pedido)

    def listar_faturas_por_cliente(self, cliente_id: str) -> List[Fatura]:
        with self._unidade() as u:
            consulta = (
                select(FaturaModel)
                .where(FaturaModel.cliente_id == cliente_id)
                .order_by(FaturaModel.competencia.desc(), FaturaModel.ordem_gravacao)
            )
            return [self._entregar_fatura(u, m) for m in u.sessao.scalars(consulta)]

    def obter_fatura(self, fatura_id: str) -> Optional[Fatura]:
        with self._unidade() as u:
            return self._entregar_fatura(u, u.sessao.get(FaturaModel, fatura_id))

    def salvar_fatura(self, fatura: Fatura) -> None:
        """Usado pelo seed e pelos testes: nenhum evento da API emite fatura ainda."""
        with self._unidade() as u:
            _gravar_fatura(u.sessao, fatura)
            u.sessao.flush()
            u.rastrear(fatura, fatura.id, _gravar_fatura)
