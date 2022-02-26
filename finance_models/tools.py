#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports
#import locale 
import datetime as dt
from typing import List
import numpy as np
import pandas as pd
import babel.numbers

#%%
# CONSTS
DT_FMT = '%d/%m/%Y'
CUR = 'BRL'

#%%
# money display
# choose locale
# locales = locale.locale_alias
# locale_candidates_pt_br = [ k for k in locales.keys() if k.startswith('pt') and 'br' in k ]

# if len(locale_candidates_pt_br) > 0:
#     best_locale = locale_candidates_pt_br[0]
# else:
#     locale_candidates_en = [ k for k in locales.keys() if k.startswith('en') ]
#     best_locale = locale_candidates_en[0]

# locale.setlocale(
#     category = locale.LC_ALL, 
#     locale = best_locale
# )
#
# money = lambda m: locale.currency(m, grouping = True)

money = lambda m: babel.numbers.format_currency(m, CUR, locale = 'pt_BR')

class Money(float):
    """ class that implements a float whose representation is a string formatted using locale-specific rules """    
    def __str__(self):
        m = float(self)
        return money(m)
    def __repr__(self):
        m = float(self)
        return f'{money(m)}'
    
    # math
    def __add__(self, other):
        return Money(float(self) + float(other))
    def __radd__(self, other):
        return self.__add__(other)
    
    def __mul__(self, other):
        op = float(self) * float(other)
        if isinstance(other, Money):
            # money squared, just return float
            return op
        else:
            return Money(op)
    
    def __rmul__(self, other):
        return self.__mul__(other)

    def __truediv__(self, other):
        op = float(self) / float(other)

        if isinstance(other, Money):
            return op
        else:
            return Money(op)
        
    def __rtruediv__(self, other):
        op = float(other) / float(self)

        if isinstance(other, Money):
            return op
        else:
            # 1 / money, just return op
            return op

#%% funcs
def dt2str(date: dt.date or dt.datetime, fmt: str = DT_FMT) -> str:
    """
    transforms a datetime object in a str object
    """
    dtstr = date.strftime(fmt)
    return dtstr

def str2dt(dtstr: str, fmt: str = DT_FMT) -> dt.date:
    """
    transforms a str object into a date object
    """
    dtobj = dt.datetime.strptime(dtstr, fmt).date()
    return dtobj

def get_holidays_anbima() -> pd.DatetimeIndex:
    """
    downloads and formats the bank holidays between 2001 and 2078 in a pandas.DatetimeIndex format
    """
    # download holidays file
    holidays_raw = pd.read_excel('https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls')

    # drops nulls and keeps only de dates column
    holidays = (holidays_raw
        .dropna()
        .drop(columns = ['Dia da Semana', 'Feriado'])
    )

    # process dates in the series
    holiday_s = pd.to_datetime(holidays['Data'])
    holiday_dtidx = pd.DatetimeIndex(holiday_s.dt.date)
    holiday_dtidx.name = 'holidays'

    return pd.DatetimeIndex(holiday_dtidx)

def get_days(
    date_begin: str or dt.date or dt.datetime,
    date_end: str or dt.date or dt.datetime,
    holidays: List or None = None,
    closed: str or None = None,
    convention: str = 'DU/252'
):
    """
    List the business days between two dates, 'date_begin' and 'date_end'
    'date_begin' and 'date_end' can be either strings or actual datetime/date objects
    'holidays' is a list-like (actual lists, sets, pandas.DatetimeIndex etc) object of bank holidays
    'closed' controls whether the dates are inclusive or exclusive. Possible options are 'left', 'right', 'both' (default) or 'neither'
    'convention' controls the day count method. 
        Two available are 'DU/252' (business days/252) or 'DC/360' (running days/360)
        In this function, if convention is 'DU/252', return only business days (excluding bank holidays)
        Otherwise return running days (including bank holidays and weekends)
    """
    # transforms date_begin
    if isinstance(date_begin, str):
        date_begin = str2dt(dtstr = date_begin)

    # transforms date_end
    if isinstance(date_end, str):
        date_end = str2dt(dtstr = date_end)
    
    if convention == 'DU/252':
        # list business days
        bdays = pd.date_range(start = date_begin, end = date_end, freq = 'B', closed = closed)

        if holidays is not None:
            # shrink holiday list to only between the date range.
            # this is to improve set performance
            holidays_range = holidays[(holidays >= date_begin.isoformat()) & (holidays <= date_end.isoformat())]

            # set operation: days which are business days but aren't holidays
            bdays_holidays_set = set(bdays) - set(holidays_range)

            # go back to datetimeindex
            bdays_holidays = pd.DatetimeIndex(sorted(list(bdays_holidays_set)))

            return bdays_holidays        
        else:
            return bdays

    else:
        days = pd.date_range(start = date_begin, end = date_end, freq = 'D', closed = closed)

        return days

def get_annualized_time(
        date_begin: str or dt.datetime or dt.date, 
        date_end: str or dt.datetime or dt.date,
        holidays: List or pd.Series or None = None,
        convention: str = 'DC/360',
    ):
        """
        annualized time (annualized time = 1 -> 1 year time difference between dates) given two dates, holiday list and date calculation convention

        date_begin: date (str no formato 'DD/MM/YYYY' ou objeto date/datetime): first date
        date_fim: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): second date
        holidays: list ou pandas.Series -> list (or series) of holiday dates. Se None, default to no holidays
        convencao: str -> convention for counting days. Default to "DC/360" (count all dates, annualize by dividing by 360)
        """
        # feriados default
        if holidays is None:
            holidays = []
        
        days = get_days(
            date_begin = date_begin,
            date_end = date_end,
            holidays = holidays,
            closed = 'left',  ## common practice is to count dates between beginning (inclusive) and ending (exclusive)
            convention = convention
        )

        # convertendo para prazo anualizado
        if convention == 'DU/252':
            annualized_time = len(days) / 252
        else:
            annualized_time = len(days) / 360

        return annualized_time

def get_bcb_ts(
    codigo_bcb: int, 
    dt_inicio: dt.date or str, 
    dt_fim: dt.date or str
):
    """extract timeseries from Brazil's Central Bank database between two dates

    Args:
        codigo_bcb (int): a code unique to the timeseries. Examples below in comments
        dt_ini (dt.dateorstr): begin date
        dt_fin (dt.dateorstr): end date

    Returns:
        pd.Series: desired timeseries
    """
    # common codes:
        # ipca = 433
        # igp_m = 189
        # selic = 11 -> Percentual diário
        # selic meta = 4390 -> Percentual mensal
        # selic_copom = 432
        # ima-b = 12466
        # ima = 12469
        # ima_s = 12462
        # ima_c = 12463
        # cdi = 12 -> Percentual diário
        # cdi = 4391 -> Percentual mensal
        # irf_m_menos1 = 17626
        # irf_m_mais1 = 17627
        # consumer price index (IPC-Br) = 191
        # commodity index - Brazil = 27574
        # Net public debt (% GDP) - Total - Federal Government and Banco Central = 4503
        # Net general government debt (% GDP) = 4536

    url = 'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{}/dados?formato=json&dataInicial={}&dataFinal={}'.format(codigo_bcb, dt_inicio, dt_fim)

    df = pd.read_json(url)
    df['data'] = pd.to_datetime(df['data'], dayfirst=True)
    
    return df