#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports

import datetime as dt
import numpy as np
import pandas as pd
from . import tools
#from seriesbr import bcb

#%%
# ntnf
class Prefixado:
    """
    Define um Título Prefixado de Dívida Soberana do Brasil
    """

    def __init__(self, 
        vencimento: int or dt.date or dt.datetime,
        taxa_anual: float,
        dt_compra: str or dt.date or dt.datetime or None = None,
        taxa_cupom: float or bool = True,
        valor_face: float = 1000.,
        convencao: str = 'DU/252',
        *args, **kwargs
    ):
        """
        parâmetros:

        'vencimento': data do vencimento. Caso seja um int, interpretamos como o ano do vencimento,
            a data do vencimento é 01/01/'vencimento'
        
        'taxa_anual': a taxa prefixada (% a.a.) pelo qual o título foi adquirido
        
        'dt_compra': data da compra (liquidacao) do título. Pode ser None, caso não queiramos incluir a data de compra
        
        'taxa_cupom': a taxa segundo a qual o título paga cupom. 
            Caso seja True, 'taxa_cupom' = 10% a.a., se for False, o título não paga cupom

        'valor_face': o valor de face do título no vencimento. Default é 1000.

        """
        # vencimento
        if isinstance(vencimento, int):
            self.vencimento = dt.date(vencimento, 1, 1)
        else:
            self.vencimento = vencimento
        
        # taxa
        self.taxa_anual = taxa_anual

        # dt_compra
        if isinstance(dt_compra, str):
            self.dt_compra = tools.str2dt(dt_compra)
        else:
            self.dt_compra = dt_compra
        
        # taxa do cupom
        if isinstance(taxa_cupom, bool):
            if taxa_cupom:
                self.taxa_cupom = 10/100
            else:
                self.taxa_cupom = 0.
        else:
            self.taxa_cupom = taxa_cupom
        
        # valor de face
        self.valor_face = valor_face

        # valor do cupom
        self.cupom = self.valor_face * ((1 + self.taxa_cupom)**0.5 - 1)

        # feriados
        self.feriados = tools.get_holidays_anbima()

        # convencao de contagem de dias
        self.convencao = convencao
    
    def calcula_prazo(self,
        dt_inicio = None,
        dt_fim = None,
        feriados = None,
        convencao = None,
    ):
        if dt_inicio is None:
            dt_inicio = self.dt_compra

        if dt_fim is None:
            dt_fim = self.vencimento

        if feriados is None:
            feriados = self.feriados
        
        if convencao is None:
            convencao = self.convencao

        dias = tools.get_days(
            date_begin = dt_inicio,
            date_end = dt_fim,
            holidays = feriados,
            closed = 'left',
            convention = convencao
        )

        if convencao == 'DU/252':
            prazo_anualizado = len(dias) / 252
        else:
            prazo_anualizado = len(dias) / 360

        return prazo_anualizado

    def constroi_fluxo(self,
        dt_fim, frequencia
    ):
        # datas dos pagamentos dos cupons, amortização etc
        # ntnf é só cupons mesmo
        lista_datas_fluxos = []


        return lista_datas_fluxos

    def calcula_pu(self,
        vf = None, 
        prazo_anual = None, 
        taxa_anual = None,
    ):
        # vf
        if vf is None:
            vf = self.valor_face
        
        # prazo anual
        if prazo_anual is None:
            prazo_anual = self.calcula_prazo()
        
        # taxa anual
        if taxa_anual is None:
            taxa_anual = self.taxa_anual

        pu = vf / (1 + taxa_anual) ** prazo_anual

        return pu

    def calcula_taxa_anual(self,
        pu, 
        prazo_anual,
        valor_base
    ):
        taxa_anual = 0.0
        return taxa_anual

    def calcula_pu_ntnf(self,
        dt_base: str or dt.datetime or dt.date,
        tir: float,
        dt_venc: str or dt.datetime or dt.date = None,
    ):
        # vencimento
        if dt_venc is None:
            dt_venc = self.vencimento

        prazo_anualizado_final = self.calcula_prazo(
            dt_inicio = dt_base,
            dt_fim = dt_venc
        )

        # pu = self.valor_face / (1 + tir) ** prazo_anualizado_final

        ncupons = int(prazo_anualizado_final * 2) + 1  # arredondar para cima
        cashflow_dtidx = pd.date_range(
            end = dt_venc,
            freq = '6MS',
            periods = ncupons,
            name = 'data'
        )
        
        cashflow = pd.DataFrame([],
            #columns = ['vf', 'du', 'fator_desconto', 'pu'],
            index = cashflow_dtidx
        )

        data = cashflow.index.to_series()

        # valor futuro
        cashflow['vf'] = self.cupom
        cashflow.loc[self.vencimento.isoformat(), 'vf'] += self.valor_face
    
        # dias (du ou dc a depender da convencao)
        cashflow['dias'] = data.apply(
            lambda dt_ate: len(tools.get_days(
                date_begin = dt_base, 
                date_end = dt_ate, 
                holidays = self.feriados, 
                closed = 'left',
                convention = self.convencao
            ))
        )

        # prazo anualizado (DU252 ou DC360 a depender da convencao)
        prazo_anualizado_s = data.apply(
            lambda dt_ate: self.calcula_prazo(
                dt_inicio = dt_base,
                dt_fim = dt_ate
            )
        )

        cashflow['fator_desconto'] = prazo_anualizado_s.apply(lambda prazo_anual: (1 + self.taxa_anual) ** prazo_anual)

        cashflow['pu'] = cashflow['vf'] / cashflow['fator_desconto']

        pu = cashflow['pu'].sum()

        # display(cashflow)
        
        return pu, cashflow
    
## OBS: se pagamento cair no feriado, pagamento no dia anterior
# data emissao - emissao do título
# data de vencimento - 
# %%
