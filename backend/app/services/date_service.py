"""Date and deadline calculation service.

Uses Brazilian holidays for business day calculations.
Delegates to shared_utils when available, with local fallback.
"""

import logging
from datetime import date, timedelta

import holidays as holidays_lib
from dateutil.relativedelta import relativedelta
from functools import lru_cache

logger = logging.getLogger(__name__)


@lru_cache(maxsize=10)
def get_holidays(year: int) -> set:
    """Get Brazilian holidays for a given year (cached)."""
    return set(holidays_lib.country_holidays("BR", years=year).keys())


def is_business_day(d: date) -> bool:
    """Check if a date is a business day (not weekend, not holiday)."""
    if d.weekday() >= 5:  # Saturday=5, Sunday=6
        return False
    return d not in get_holidays(d.year)


def add_business_days(from_date: date, num_days: int) -> date:
    """Add (or subtract) business days from a date.

    Skips weekends and Brazilian national holidays.
    If num_days=0, returns the next business day if from_date is not one.
    """
    if num_days == 0:
        current = from_date
        while not is_business_day(current):
            current += timedelta(days=1)
        return current

    direction = 1 if num_days > 0 else -1
    remaining = abs(num_days)
    current = from_date

    while remaining > 0:
        current += timedelta(days=direction)
        if is_business_day(current):
            remaining -= 1

    return current


def add_months(source_date: date, months: int) -> date:
    """Add months to a date using relativedelta."""
    return source_date + relativedelta(months=months)


def calculate_d_minus(fatal_date: date, days_before: int = 3) -> date:
    """Calculate D- date (business days before fatal date)."""
    return add_business_days(fatal_date, -days_before)


def calcular_parcelas_916(
    valor_total: float,
    data_fatal: date,
) -> list[dict]:
    """Calculate Art. 916 CPC installment plan.

    30% entry on fatal date + 6 monthly installments with 1% simple interest.

    Returns:
        List of dicts with keys: parcela, valor, data, data_formatada
    """
    entrada = round(valor_total * 0.30, 2)
    saldo = valor_total - entrada
    valor_parcela_base = round(saldo / 6, 2)

    parcelas = [
        {
            "parcela": "Entrada (30%)",
            "valor": entrada,
            "data": data_fatal,
            "data_formatada": data_fatal.strftime("%d/%m/%Y"),
        }
    ]

    for i in range(1, 7):
        juros = 1 + (0.01 * i)  # 1% simple interest per month
        valor = round(valor_parcela_base * juros, 2)
        data_parcela = add_months(data_fatal, i)
        data_util = add_business_days(data_parcela, 0)  # Ensure business day

        parcelas.append(
            {
                "parcela": f"{i}ª Parcela",
                "valor": valor,
                "data": data_util,
                "data_formatada": data_util.strftime("%d/%m/%Y"),
            }
        )

    return parcelas
