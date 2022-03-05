#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports
#import locale 
import datetime as dt
from typing import List, Tuple
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
    
    # argument for date generating function
    if pd.__version__ >= '1.4.0':
        kwargs = { 'inclusive': closed }
    else:
        kwargs = { 'closed': closed }
    
    if convention == 'DU/252':
        # list business days
        bdays = pd.date_range(start = date_begin, end = date_end, freq = 'B', **kwargs)

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
        days = pd.date_range(start = date_begin, end = date_end, freq = 'D', **kwargs)

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
    dt_inicio: dt.date or dt.datetime or str or None = None, 
    dt_fim: dt.date or dt.datetime or str or None = None
):
    """extract timeseries from Brazil's Central Bank database between two dates

    Args:
        codigo_bcb (int): a code unique to the timeseries. Examples below in comments
        dt_inicio (dt.date or dt.datetime or str): begin date
        dt_fim (dt.date or dt.datetime or str): end date

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

    url = f'http://api.bcb.gov.br/dados/serie/bcdata.sgs.{codigo_bcb}/dados?formato=json'

    # dt_inicio in text format
    if dt_inicio is not None:
        if not isinstance(dt_inicio, str):
            dt_inicio = dt2str(dt_inicio)
        
        url += f'&dataInicial={dt_inicio}'
    
    # dt_fim in text format
    if dt_fim is not None:
        if not isinstance(dt_fim, str):
            dt_fim = dt2str(dt_fim)
        
        url += f'&dataFinal={dt_fim}'

    df = pd.read_json(url)
    df['data'] = pd.to_datetime(df['data'], dayfirst=True)

    if codigo_bcb == 433: # ipca é disponibilizada no dia 15 de cada mes
        df['data'] += dt.timedelta(days = 14)

    s = df.set_index('data')['valor']
    
    return s

def interp_compound(
    f_total: float, 
    x2: float, 
    xi: float,
    x1: float = 0, 
) -> Tuple[float]:
    """interpolate so that the compound interest between to periods stays the same

    Args:
        f_total (float): total interest between two periods
        x1 (float): first period. defaults to zero
        x2 (float): second period
        xi (float): interval between first and second periods

    Returns:
        Tuple[float]: what the interest between x1 and xi periods (f1i) and between xi and x2 periods (fi2), so they compound to f_total regardless
    """
    f1i = f_total ** ((xi - x1) / (x2 - x1))
    fi2 = f_total ** ((x2 - xi) / (x2 - x1))

    return f1i, fi2

def fix_timeseries_ends(
        ts_orig: pd.Series, 
        date_begin: dt.date or dt.datetime or str or None, 
        date_end: dt.date or dt.datetime or str or None,
    ):
        """fix both ends of a timeseries so they match the given dates

        Args:
            ts_orig (int or pd.Series): timeseries.
            dt_inicio (dt.date or dt.datetime or str): first date
            dt_fim (dt.date or dt.datetime or str): second date

        Returns:
            pd.Series: fixed timeseries
        """
        
        if isinstance(date_begin, str):
            date_begin = str2dt(date_begin)

        if isinstance(date_end, str):
            date_end = str2dt(date_end)

        # convert to timestamp so they work with pandas
        if date_begin is not None:
            date_begin = pd.Timestamp(date_begin)
        else:
            date_begin = ts_orig.index[0]

        if date_end is not None:
            date_end = pd.Timestamp(date_end)
        else:
            date_end = ts_orig.index[-1]

        # first, let's store the existing NaNs in a separate series
        nans_dates = ts_orig.index[ts_orig.isna()]
        
        # let's assume that whatever NaNs are zeros
        indice = ts_orig.fillna(0)
     
        # before we get on with the strategy, let's complete the series and extrapolate linearly:
        delta_t = indice.index[-1] - indice.index[-2]
        xextr = indice.index[-1]
        while xextr <= date_end:
            xextr += delta_t
            y1, y2 = indice.iloc[-3:-1].values
            x1, x2 = indice.index[-3:-1]
            yextr = (xextr - x1) * (y2 - y1) / (x2 - x1) + y1
            indice[xextr] = yextr

        # the strategy is to get NaNs in place of the missing dates (date_begin and date_end), and then fill them with interpolations or extrapolations
        newidx = []

        if date_begin not in indice.index: # if timeseries begins on date_begin, nothing to do on this end
            newidx.append(date_begin)
        
        if date_end not in indice.index: # same for the other end
            newidx.append(date_end)

        # if it's misaligned on either end, create new series with nans and concatenate with original series
        if len(newidx) > 0:
            newseries = pd.Series(
                index = newidx, 
                dtype = float
            )

            indice = pd.concat([indice, newseries]).sort_index()
        
        # now let's find the inserted NaNs in our series
        # first, if it's in the beginning, this means it's the first of the entire timeseries.
        # there is no good information. let's zero it 
        if np.isnan(indice.iloc[0]):
            indice.iloc[0] = 0
            
        # if it's in the middle: use the interpolation preserving the compound rate
        indice_fixed = indice.copy()
        if indice.shape[0] >= 3:
            for i in range(0, indice.shape[0]-2):
                janela = indice.iloc[i:i+3]
                if np.isnan(janela.iloc[1]) and janela.index[1] not in nans_dates:
                    f1i, fi2 = interp_compound(
                        f_total = 1 + janela.iloc[0]/100, 
                        x2 = janela.index[2], 
                        xi = janela.index[1],
                        x1 = janela.index[0], 
                    )
                    indice_fixed.iloc[i] = (f1i - 1) * 100
                    indice_fixed.iloc[i+1] = (fi2 - 1) * 100
               
        # in the end, this means that is the last of the timeseries
        # there is reasonable expectation that the trend will continue
        # linear extrapolation

        #indice_fixed = indice_fixed.fillna(method = 'ffill')
        if np.isnan(indice_fixed.iloc[-1]):
            y1, y2 = indice_fixed.iloc[-3:-1].values
            x1, x2, xextr = indice_fixed.index[-3:].to_numpy().astype('int64')
            yextr = (xextr - x1) * (y2 - y1) / (x2 - x1) + y1
            
            indice_fixed.iloc[-1] = yextr

        # finally, let's add back the nans ...
        indice_fixed.loc[nans_dates] = np.nan
        # ... and lop off the sections before the begin date and after the end date
        indice_fixed = indice_fixed[
            (indice_fixed.index >= date_begin) &
            (indice_fixed.index <= date_end)
        ]

        return indice_fixed