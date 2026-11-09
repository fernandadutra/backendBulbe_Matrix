"""Tipos de coluna próprios do projeto."""

from datetime import datetime, timezone

from sqlalchemy import DateTime
from sqlalchemy.types import TypeDecorator

from app.core import relogio


class DataHora(TypeDecorator):
    """Data e hora com fuso, igual em qualquer banco.

    O SQLite não guarda fuso horário. Por isso gravamos sempre em UTC e,
    na leitura, devolvemos no fuso da aplicação (America/Sao_Paulo).
    Assim o domínio continua recebendo datetimes com fuso, como antes.
    """

    impl = DateTime
    cache_ok = True

    def process_bind_param(self, valor, dialeto):
        if valor is None:
            return None
        if valor.tzinfo is None:
            raise ValueError("DataHora exige datetime com fuso horário")
        return valor.astimezone(timezone.utc).replace(tzinfo=None)

    def process_result_value(self, valor, dialeto):
        if valor is None:
            return None
        return valor.replace(tzinfo=timezone.utc).astimezone(relogio.FUSO)
