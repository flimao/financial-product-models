#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports

import datetime as dt
import numpy as np
import pandas as pd
from . import tools
from seriesbr import bcb

#%%
# ntnf
class Prefixado:
    def __init__(*args, **kwargs):
        pass
    
    def calcula_prazo(self,
        dt_inicio,
        dt_fim,
        feriados,
        convencao,
    ):
        prazo_anualizado = 0.0
        return prazo_anualizado

    def constroi_fluxo(self,
        dt_fim, frequencia
    ):
        # datas dos pagamentos dos cupons, amortização etc
        # ntnf é só cupons mesmo
        lista_datas_fluxos = []
        return lista_datas_fluxos

    def calcula_pu(self,
        vf, 
        prazo_anual, 
        taxa_anual,
    ):
        # vf = 1000
        pu = 0.0
        return pu

    def calcula_taxa_anual(self,
        pu, 
        prazo_anual,  # calcula_prazo()
        valor_base = 100,
    ):
        taxa_anual = 0.0
        return taxa_anual

    def calcula_pu_ntnf(self,
        dt_venc,
        dt_base,
        tir,
    ):
        cashflow = pd.DataFrame([],
            columns = ['data', 'vf', 'du', 'fator_desconto', 'pu']
        )
        display(cashflow)

        pu = 0.0
        return pu
    
## OBS: se pagamento cair no feriado, pagamento no dia anterior
# data emissao - emissao do título
# data de vencimento - 