from datetime import date, datetime
from typing import Callable
from zoneinfo import ZoneInfo

FUSO = ZoneInfo("America/Sao_Paulo")

def _agora_real() -> datetime:
    # Sem microssegundos, como nos exemplos da especificação.
    return datetime.now(FUSO).replace(microsecond=0)


_funcao_agora: Callable[[], datetime] = _agora_real


def agora() -> datetime:
    return _funcao_agora()


def hoje() -> date:
    return agora().date()


def definir_relogio(funcao: Callable[[], datetime]) -> None:
    """Troca a fonte de tempo. Usado nos testes para congelar o relógio."""
    global _funcao_agora
    _funcao_agora = funcao


def restaurar_relogio() -> None:
    definir_relogio(_agora_real)
