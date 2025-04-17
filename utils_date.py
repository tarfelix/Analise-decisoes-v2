# -*- coding: utf-8 -*-
import holidays
from datetime import date, timedelta, datetime
import streamlit as st
import logging
from dateutil.relativedelta import relativedelta # <<< Importar relativedelta

log = logging.getLogger(__name__)

# --- Cache para Feriados ---
@st.cache_data
def get_holidays(year):
    # ... (código mantido) ...
    log.info(f"Carregando feriados para o ano {year}...")
    try:
        h = holidays.country_holidays('BR', years=year)
        log.info(f"Feriados para {year} carregados com sucesso.")
        return h
    except Exception as e:
        log.error(f"Erro ao carregar feriados para {year}: {e}")
        return {}

# --- Função add_business_days (mantida) ---
def add_business_days(from_date, num_days):
    # ... (código mantido) ...
    if not isinstance(from_date, date): return None
    br_holidays = get_holidays(from_date.year)
    potential_end_year = (from_date + timedelta(days=num_days*2 if num_days !=0 else 30)).year
    if potential_end_year != from_date.year: br_holidays.update(get_holidays(potential_end_year))
    current_date = from_date
    if num_days == 0:
        current_year_holidays = get_holidays(current_date.year)
        while current_date.weekday() >= 5 or current_date in current_year_holidays:
            current_date += timedelta(days=1)
            if current_date.year != from_date.year: current_year_holidays = get_holidays(current_date.year)
        return current_date
    days_added = 0; increment = 1 if num_days > 0 else -1; absolute_days = abs(num_days); current_year = from_date.year
    while days_added < absolute_days:
        current_date += timedelta(days=increment); weekday = current_date.weekday()
        if current_date.year != current_year: current_year = current_date.year; br_holidays = get_holidays(current_year)
        if weekday >= 5 or current_date in br_holidays: continue
        days_added += 1
    return current_date

# --- NOVA FUNÇÃO: Adicionar Meses ---
def add_months(source_date, months):
    """Adiciona um número de meses a uma data usando relativedelta."""
    if not isinstance(source_date, date): return None
    try:
        return source_date + relativedelta(months=months)
    except Exception as e:
        log.error(f"Erro ao adicionar {months} meses a {source_date}: {e}")
        return None # Retorna None em caso de erro
