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

money = lambda m: babel.numbers.format_currency(m, CUR)

class Money(float):
    """ class that implements a float whose representation is a string formatted using locale-specific rules """    
    def __str__(self):
        return money(self)
    def __repr__(self):
        return money(self)
    
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


#%%
# tests
if __name__ == '__main__':
    holidays = get_holidays_anbima()
    dus = get_days(date_begin = '01/01/2022', date_end = '01/04/2022', holidays = holidays, closed = 'left')

