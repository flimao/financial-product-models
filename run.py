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
import warnings

warnings.filterwarnings('ignore')
#%%
# CONSTS
HISTBRDEBTSEC = r'https://www.tesourotransparente.gov.br/ckan/dataset/df56aa42-484a-4a59-8184-7676580c81e3/resource/796d2059-14e9-44e3-80c9-2d9e30b405c1/download/PrecoTaxaTesouroDireto.csv'

#%%
# download brdebt history

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
    
    for datecol in ['maturity_date', 'base_date']:
        df[datecol] = pd.to_datetime(df[datecol], dayfirst = True)
        df[datecol] = df[datecol].dt.date
    
    for col in ['rate_buy', 'rate_sell', 'pu_buy', 'pu_sell', 'pu_base' ]:
        df[col] = df[col].str.replace('.', '').str.replace(',', '.').astype(float)

    return df

brdebt_raw = pd.read_csv(HISTBRDEBTSEC, sep=';')
brdebt = (brdebt_raw
    .pipe(brdebt_rename_cols)
    .pipe(brdebt_change_types)
)

#%%
# test

holidays = tools.get_holidays_anbima()

ntnf_hist_full = brdebt[brdebt['security_type'] == 'Tesouro Prefixado com Juros Semestrais'].sort_values('base_date')
ntnf_hist = ntnf_hist_full.sample(1).iloc[0]

ntnf_dados = {}
ntnf_dados['vencimento'] = ntnf_hist['maturity_date']
ntnf_dados['taxa_anual'] = ntnf_hist['rate_buy'] / 100
ntnf_dados['taxa_cupom'] = True

ntnfX = Prefixado(**ntnf_dados)

# pu_buy : taxa buy, D+1 a partir da data base
pu_buy, _ = ntnfX.calcula_pu_ntnf(
    dt_base = ntnf_hist['base_date'] + pd.offsets.BDay(1),
    tir = ntnf_hist['rate_buy']/100
)
pu_buy_expect = ntnf_hist['pu_buy']

# pu_sell: taxa sell, D+1 a partir da data base
pu_sell, _ = ntnfX.calcula_pu_ntnf(
    dt_base = ntnf_hist['base_date'] + pd.offsets.BDay(1),
    tir = ntnf_hist['rate_sell']/100
)
pu_sell_expect = ntnf_hist['pu_sell']

# pu_base: taxa sell, D+0 da data base
pu_base, _ = ntnfX.calcula_pu_ntnf(
    dt_base = ntnf_hist['base_date'],
    tir = ntnf_hist['rate_sell']/100
)
pu_base_expect = ntnf_hist['pu_base']

print(f"PUs de {ntnfX} (data base {ntnf_hist['base_date']:%d/%m/%Y}):")
print(f'     PU Buy (D+1): esperado {tools.Money(pu_buy_expect)}, retornou {tools.Money(pu_buy)}')
print(f'    PU Sell (D+1): esperado {tools.Money(pu_sell_expect)}, retornou {tools.Money(pu_sell)}')
print(f'    PU Base (D+0): esperado {tools.Money(pu_base_expect)}, retornou {tools.Money(pu_base)}')

#%%
# titulos prefixados em 12/02/2022
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
