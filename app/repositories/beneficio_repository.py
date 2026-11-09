"""
Camada de Persistência, repositórios do Clube de Benefícios
(parceiros, trilhas, benefícios e resgates).
Mesmo padrão dos demais: contrato, versão em memória e versão SQL.
"""

import threading
from typing import Dict, Iterable, List, Optional, Protocol, Tuple

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models import BeneficioModel, ParceiroModel, ResgateModel, TrilhaModel
from app.db.repositorio_sql import RepositorioSql, copiar_campos, proxima_ordem
from app.models.beneficio import Beneficio, Parceiro, Trilha
from app.models.resgate import Resgate

_CAMPOS_PARCEIRO = ("nome", "url_logo", "cor_marca", "destaque")
_CAMPOS_TRILHA = ("nome", "descricao", "regra_acesso", "cor_tema", "url_icone")
_CAMPOS_BENEFICIO = (
    "trilha", "parceiro_id", "titulo", "descricao", "regras_de_uso", "tipo", "regra_acesso", "validade_inicio",
    "validade_fim", "ativo", "dias_validade_resgate", "instrucoes", "prefixo_codigo", "url_acesso", "total_resgates",
)
_CAMPOS_RESGATE = (
    "cliente_id", "beneficio_id", "resgatado_em", "situacao", "instrucoes", "codigo", "url_acesso", "expira_em",
    "chave_idempotencia", "pedido_id",
)


class BeneficioRepository(Protocol):
    # Quem decide um resgate segura a trava do começo das checagens até salvar_resgate.
    trava: threading.Lock

    def listar_trilhas(self) -> List[Trilha]: ...
    def obter_parceiro(self, parceiro_id: str) -> Parceiro: ...
    def listar_beneficios(self) -> List[Beneficio]: ...
    def obter_beneficio(self, beneficio_id: str) -> Optional[Beneficio]: ...
    def resgate_por_chave(self, cliente_id: str, chave: str) -> Optional[Resgate]: ...
    def cliente_ja_resgatou(self, cliente_id: str, beneficio_id: str) -> bool: ...
    def salvar_resgate(self, resgate: Resgate) -> None: ...
    def listar_resgates_por_cliente(self, cliente_id: str) -> List[Resgate]: ...


class InMemoryBeneficioRepository:
    def __init__(
        self,
        parceiros: Iterable[Parceiro] = (),
        trilhas: Iterable[Trilha] = (),
        beneficios: Iterable[Beneficio] = (),
    ):
        self._parceiros: Dict[str, Parceiro] = {p.id: p for p in parceiros}
        self._trilhas: List[Trilha] = list(trilhas)
        self._beneficios: Dict[str, Beneficio] = {b.id: b for b in beneficios}
        self._resgates: List[Resgate] = []
        self._chaves: Dict[Tuple[str, str], str] = {}
        self.trava = threading.Lock()

    def listar_trilhas(self) -> List[Trilha]:
        return list(self._trilhas)

    def obter_parceiro(self, parceiro_id: str) -> Parceiro:
        return self._parceiros[parceiro_id]

    def listar_beneficios(self) -> List[Beneficio]:
        return list(self._beneficios.values())

    def obter_beneficio(self, beneficio_id: str) -> Optional[Beneficio]:
        return self._beneficios.get(beneficio_id)

    def resgate_por_chave(self, cliente_id: str, chave: str) -> Optional[Resgate]:
        resgate_id = self._chaves.get((cliente_id, chave))
        return next((r for r in self._resgates if r.id == resgate_id), None) if resgate_id else None

    def cliente_ja_resgatou(self, cliente_id: str, beneficio_id: str) -> bool:
        return any(r.cliente_id == cliente_id and r.beneficio_id == beneficio_id for r in self._resgates)

    def salvar_resgate(self, resgate: Resgate) -> None:
        """Grava resgate, contador e chave juntos. Chamar com a trava já tomada."""
        beneficio = self._beneficios[resgate.beneficio_id]
        chave = (resgate.cliente_id, resgate.chave_idempotencia)
        self._resgates.append(resgate)
        try:
            beneficio.total_resgates += 1
            self._chaves[chave] = resgate.id
        except Exception:
            self._resgates.remove(resgate)
            beneficio.total_resgates = max(0, beneficio.total_resgates - 1)
            self._chaves.pop(chave, None)
            raise

    def listar_resgates_por_cliente(self, cliente_id: str) -> List[Resgate]:
        # Mais recentes primeiro. Em empate de horário, vale a ordem de gravação.
        do_cliente = [r for r in reversed(self._resgates) if r.cliente_id == cliente_id]
        return sorted(do_cliente, key=lambda r: r.resgatado_em, reverse=True)

    def salvar_parceiro(self, parceiro: Parceiro) -> None:
        self._parceiros[parceiro.id] = parceiro

    def salvar_trilha(self, trilha: Trilha) -> None:
        self._trilhas.append(trilha)

    def salvar_beneficio(self, beneficio: Beneficio) -> None:
        self._beneficios[beneficio.id] = beneficio


# Conversões


def _parceiro_para_dominio(m: ParceiroModel) -> Parceiro:
    return Parceiro(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_PARCEIRO})


def _trilha_para_dominio(m: TrilhaModel) -> Trilha:
    return Trilha(chave=m.chave, **{c: getattr(m, c) for c in _CAMPOS_TRILHA})


def _beneficio_para_dominio(m: BeneficioModel) -> Beneficio:
    return Beneficio(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_BENEFICIO})


def _resgate_para_dominio(m: ResgateModel) -> Resgate:
    return Resgate(id=m.id, **{c: getattr(m, c) for c in _CAMPOS_RESGATE})


def _gravar_parceiro(sessao: Session, p: Parceiro) -> None:
    modelo = sessao.get(ParceiroModel, p.id)
    if modelo is None:
        modelo = ParceiroModel(id=p.id, ordem_gravacao=proxima_ordem(sessao, ParceiroModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(p, c) for c in _CAMPOS_PARCEIRO})


def _gravar_trilha(sessao: Session, t: Trilha) -> None:
    modelo = sessao.get(TrilhaModel, t.chave)
    if modelo is None:
        modelo = TrilhaModel(chave=t.chave, ordem_gravacao=proxima_ordem(sessao, TrilhaModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(t, c) for c in _CAMPOS_TRILHA})


def _gravar_beneficio(sessao: Session, b: Beneficio) -> None:
    modelo = sessao.get(BeneficioModel, b.id)
    if modelo is None:
        modelo = BeneficioModel(id=b.id, ordem_gravacao=proxima_ordem(sessao, BeneficioModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(b, c) for c in _CAMPOS_BENEFICIO})


def _gravar_resgate(sessao: Session, r: Resgate) -> None:
    modelo = sessao.get(ResgateModel, r.id)
    if modelo is None:
        modelo = ResgateModel(id=r.id, ordem_gravacao=proxima_ordem(sessao, ResgateModel))
        sessao.add(modelo)
    copiar_campos(modelo, **{c: getattr(r, c) for c in _CAMPOS_RESGATE})


class SqlBeneficioRepository(RepositorioSql):
    def __init__(self, session_factory) -> None:
        super().__init__(session_factory)
        # Mesma trava da versão em memória: serializa as decisões de resgate deste processo.
        self.trava = threading.Lock()

    def _entregar_beneficio(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Beneficio, modelo.id) or u.rastrear(
            _beneficio_para_dominio(modelo), modelo.id, _gravar_beneficio
        )

    def _entregar_resgate(self, u, modelo):
        if modelo is None:
            return None
        return u.obter(Resgate, modelo.id) or u.rastrear(_resgate_para_dominio(modelo), modelo.id, _gravar_resgate)

    def listar_trilhas(self) -> List[Trilha]:
        # Trilhas e parceiros são catálogo: nenhum service os altera, então não precisam ser rastreados.
        with self._unidade() as u:
            modelos = u.sessao.scalars(select(TrilhaModel).order_by(TrilhaModel.ordem_gravacao))
            return [_trilha_para_dominio(m) for m in modelos]

    def obter_parceiro(self, parceiro_id: str) -> Parceiro:
        with self._unidade() as u:
            modelo = u.sessao.get(ParceiroModel, parceiro_id)
            if modelo is None:
                raise KeyError(parceiro_id)
            return _parceiro_para_dominio(modelo)

    def listar_beneficios(self) -> List[Beneficio]:
        with self._unidade() as u:
            modelos = u.sessao.scalars(select(BeneficioModel).order_by(BeneficioModel.ordem_gravacao))
            return [self._entregar_beneficio(u, m) for m in modelos]

    def obter_beneficio(self, beneficio_id: str) -> Optional[Beneficio]:
        with self._unidade() as u:
            return self._entregar_beneficio(u, u.sessao.get(BeneficioModel, beneficio_id))

    def resgate_por_chave(self, cliente_id: str, chave: str) -> Optional[Resgate]:
        with self._unidade() as u:
            consulta = select(ResgateModel).where(
                ResgateModel.cliente_id == cliente_id, ResgateModel.chave_idempotencia == chave
            )
            return self._entregar_resgate(u, u.sessao.scalars(consulta).first())

    def cliente_ja_resgatou(self, cliente_id: str, beneficio_id: str) -> bool:
        with self._unidade() as u:
            consulta = select(ResgateModel.id).where(
                ResgateModel.cliente_id == cliente_id, ResgateModel.beneficio_id == beneficio_id
            )
            return u.sessao.scalars(consulta).first() is not None

    def salvar_resgate(self, resgate: Resgate) -> None:
        """Grava resgate e contador na mesma transação. Chamar com a trava já tomada.

        O commit acontece aqui, ainda com a trava: a próxima requisição que tomar a
        trava já enxerga este resgate no banco. Se algo falhar, a transação inteira
        é desfeita (nem resgate, nem contador).
        """
        with self._unidade() as u:
            _gravar_resgate(u.sessao, resgate)
            self._incrementar_contador(u, resgate.beneficio_id)
            u.rastrear(resgate, resgate.id, _gravar_resgate)
            u.confirmar()

    def _incrementar_contador(self, u, beneficio_id: str) -> None:
        modelo = u.sessao.get(BeneficioModel, beneficio_id)
        # UPDATE ... SET total_resgates = total_resgates + 1: o próprio banco soma, sem corrida.
        modelo.total_resgates = BeneficioModel.total_resgates + 1
        u.sessao.flush()
        u.sessao.refresh(modelo, ["total_resgates"])
        beneficio = u.obter(Beneficio, beneficio_id)
        if beneficio is not None:
            beneficio.total_resgates = modelo.total_resgates

    def listar_resgates_por_cliente(self, cliente_id: str) -> List[Resgate]:
        # Mais recentes primeiro. Em empate de horário, vale a ordem de gravação.
        with self._unidade() as u:
            consulta = (
                select(ResgateModel)
                .where(ResgateModel.cliente_id == cliente_id)
                .order_by(ResgateModel.resgatado_em.desc(), ResgateModel.ordem_gravacao.desc())
            )
            return [self._entregar_resgate(u, m) for m in u.sessao.scalars(consulta)]

    # Usados pelo seed (catálogo de demonstração).

    def salvar_parceiro(self, parceiro: Parceiro) -> None:
        with self._unidade() as u:
            _gravar_parceiro(u.sessao, parceiro)
            u.sessao.flush()

    def salvar_trilha(self, trilha: Trilha) -> None:
        with self._unidade() as u:
            _gravar_trilha(u.sessao, trilha)
            u.sessao.flush()

    def salvar_beneficio(self, beneficio: Beneficio) -> None:
        with self._unidade() as u:
            _gravar_beneficio(u.sessao, beneficio)
            u.sessao.flush()
            u.rastrear(beneficio, beneficio.id, _gravar_beneficio)
