# -*- coding: utf-8 -*-
import holidays
from datetime import date, timedelta, datetime
import streamlit as st # Para usar o cache
import logging # Usar logging

# Configuração do logging para este módulo
log = logging.getLogger(__name__)

# --- Cache para Feriados ---
@st.cache_data # Cacheia o resultado da função
def get_holidays(year):
    """Carrega e retorna feriados nacionais para um ano específico."""
    log.info(f"Carregando feriados para o ano {year}...")
    try:
        # Considerar usar subdiv='SP' ou outra se feriados regionais forem relevantes
        h = holidays.country_holidays('BR', years=year)
        log.info(f"Feriados para {year} carregados com sucesso.")
        return h
    except Exception as e:
        log.error(f"Erro ao carregar feriados para {year}: {e}")
        st.error(f"Erro ao carregar feriados: {e}")
        return {}

def add_business_days(from_date, num_days):
    """Calcula a data resultante após adicionar 'num_days' dias úteis a 'from_date'.
       Se num_days for 0, retorna o próximo dia útil se from_date não for útil.
    """
    if not isinstance(from_date, date): return None

    br_holidays = get_holidays(from_date.year)
    # Se o cálculo cruzar a virada do ano, carrega feriados do ano seguinte também
    potential_end_year = (from_date + timedelta(days=num_days*2 if num_days !=0 else 30)).year # Estimativa
    if potential_end_year != from_date.year:
         br_holidays.update(get_holidays(potential_end_year))

    current_date = from_date
    if num_days == 0:
        while current_date.weekday() >= 5 or current_date in br_holidays:
            current_date += timedelta(days=1)
            # Recarrega feriados se virar o ano durante a busca do dia 0
            if current_date.year != from_date.year and current_date.year not in br_holidays:
                 br_holidays.update(get_holidays(current_date.year))
        return current_date

    days_added = 0
    increment = 1 if num_days > 0 else -1
    absolute_days = abs(num_days)
    current_year = from_date.year # Ano inicial para checagem de feriados

    while days_added < absolute_days:
        current_date += timedelta(days=increment); weekday = current_date.weekday()
        # Recarrega feriados se virar o ano durante o loop principal
        if current_date.year != current_year:
            current_year = current_date.year
            if current_year not in br_holidays: # Só carrega se ainda não tiver
                 br_holidays.update(get_holidays(current_year))

        if weekday >= 5 or current_date in br_holidays: continue
        days_added += 1
    return current_date