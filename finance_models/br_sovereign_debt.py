#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
from . import tools

class NTNF:
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
        lista_datas_fluxos = []
        return lista_datas_fluxos

    def calcula_pu(self,
        vf, 
        prazo_anual, 
        taxa_anual,
    ):
        pu = 0.0
        return pu

    def calcula_taxa_anual(self,
        pu, 
        prazo_anual,
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