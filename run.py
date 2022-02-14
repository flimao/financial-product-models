#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports

# pip install git+ssh://git@github.com:flimao/financial-product-models.git

import datetime as dt
import numpy as np
import pandas as pd
from finance_models.br_sovereign_debt_securities import Prefixado
from finance_models import tools

#%%
# CONSTS
HISTBRDEBTSEC = r'https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv'

#%%

def brdebt_rename_cols(df):
    df = df.copy()

    ren_from = [
        'Tipo Titulo', 'Data Vencimento', 'Data Base', 'Taxa Compra Manha',
        'Taxa Venda Manha', 'PU Compra Manha', 'PU Venda Manha',
        'PU Base Manha',
    ]
    ren_to = [
        'security_type', 'maturity_date', 'base_date', 
        'rate_buy', 'rate_sell', 
        'pu_buy', 'pu_sell', 'pu_base'
    ]

    ren_dict = { f: t for f, t in zip(ren_from, ren_to)}
    df = df.rename(columns = ren_dict)
    return df

def brdebt_change_types(df):
    df = df.copy()

    df['security_type'] = df['security_type'].astype('category')
    #for

    return df

#brdebt_raw = pd.read_csv(HISTBRDEBTSEC, sep=';')

#%%
# test

holidays = tools.get_holidays_anbima()

ntnf31 = Prefixado(
    vencimento = 2031,
    taxa_anual = 11.54/100,
    taxa_cupom = True,
    dt_compra = '14/02/2022'
)

ltn24 = Prefixado(
    vencimento = '01/07/2024',
    taxa_anual = 11.74/100,
    taxa_cupom = False,
    dt_compra = '14/02/2022'
)

ltn26 = Prefixado(
    vencimento = 2026,
    taxa_anual = 11.36/100,
    taxa_cupom = False,
    dt_compra = '14/02/2022'
)

#pu, cashflow = ntnf31.calcula_pu_ntnf(dt_base = ntnf31.dt_compra, tir = 13.15/100)
# %%
