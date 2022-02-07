#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd

DT_FMT = '%d/%m/%Y'

def dt2str(date: dt.date or dt.datetime, fmt: str = DT_FMT):
    dtstr = date.strftime(fmt)
    return dtstr

def str2dt(dtstr: str, fmt: str = DT_FMT):
    dtobj = dt.datetime.strptime(dtstr, fmt).date()
    return dtobj

def get_holidays_anbima():
    holidays_raw = pd.read_excel('https://www.anbima.com.br/feriados/arqs/feriados_nacionais.xls')
    holidays = (holidays_raw
        .dropna()
        .drop(columns = ['Dia da Semana', 'Feriado'])
    )

    holiday_s = pd.to_datetime(holidays['Data'])

    return holiday_s.dt.date