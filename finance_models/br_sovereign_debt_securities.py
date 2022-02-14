#!/usr/bin/env python3
#-*- coding: utf-8 -*-

#%%
# imports

from typing import List
import datetime as dt
import numpy as np
import pandas as pd
from . import tools

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

        'convencao': pode ser 'DU/252' (dias uteis) ou 'DC/360' (dias corridos em base 360 dias)

        """
        # vencimento
        if isinstance(vencimento, int):
            self.vencimento = dt.date(vencimento, 1, 1)
        elif isinstance(vencimento, str):
            self.vencimento = tools.str2dt(vencimento)
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
        dt_inicio: str or dt.datetime or dt.date or None = None, 
        dt_fim: str or dt.datetime or dt.date or None = None, 
        feriados: List or pd.Series or None = None,
        convencao: str = None,
    ):
        """
        calcula o prazo anualizado (prazo anualizado = 1 -> 1 ano) dados o dia inicial, o dia final, uma lista de feriados e a convencao

        dt_inicio: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do começo do intervalo
            Se None, default para data de compra
        dt_fim: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim do intervalo
            Se None, default para data de vencimento
        feriados: list ou pandas.Series -> lista (ou series) de feriados. Se None, default para lista de feriados da Anbima
        convencao: str -> convencao de contagem de dias. Default para o definido na classe
        """
        # dt_inicio default
        if dt_inicio is None:
            dt_inicio = self.dt_compra

        # dt_fim default
        if dt_fim is None:
            dt_fim = self.vencimento

        # feriados default
        if feriados is None:
            feriados = self.feriados
        
        # convencao default
        if convencao is None:
            convencao = self.convencao

        # contagem dos dias é feita em uma função de auxílio
        dias = tools.get_days(
            date_begin = dt_inicio,
            date_end = dt_fim,
            holidays = feriados,
            closed = 'left',  ## a prática é contar os dias entre a data de inicio (inclusive) e a data de termino (exclusive)
            convention = convencao
        )

        # convertendo para prazo anualizado
        if convencao == 'DU/252':
            prazo_anualizado = len(dias) / 252
        else:
            prazo_anualizado = len(dias) / 360

        return prazo_anualizado

    def constroi_fluxo(self,
        dt_fim: str or dt.datetime or dt.date or None = None, 
        frequencia: int = 6 # meses
    ):

        """
        calcula lista com as datas dos eventos (pagamento de cupom e retorno do principal) de uma LTN/NTN-F

        dt_fim: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        frequencia: int -> o número de meses entre eventos
        """
        # datas dos pagamentos dos cupons, amortização etc
        # ntnf é só cupons mesmo
        if dt_fim is None:
            dt_fim = self.vencimento
        elif isinstance(dt_fim, str):
            dt_fim = tools.str2dt(dt_fim)

        # a data base é a data de compra
        dt_base = self.dt_compra

        # a data inicio deve ser ou 01/07/(ANO DA DATA BASE) ou 01/01/(ANO SEGUINTE AO ANO DA DATA BASE), o que ocorrer primeiro
        dt_inicio = dt.date(
            year = dt_base.year if dt_base.month < 7 else dt_base.year + 1,
            month = 7 if dt_base.month < 7 else 1,
            day = 1
        )
        
        # os pagamentos são espaçados de 6 em 6 meses
        # como o vencimento do título sempre cai em 1o janeiro, ele se encaixa perfeitamente nesse fluxo
        series_datas_fluxos = pd.date_range(
            start = dt_inicio,
            freq = f'{frequencia}MS',
            end = dt_fim,
            name = 'data'
        )

        lista_datas_fluxos = series_datas_fluxos.tolist()

        return lista_datas_fluxos

    def calcula_pu(self,
        vf: float or None = None, 
        prazo_anual: float or None = None, 
        taxa_anual: float or None = None,
    ):
        """
        calcula o PU de um prefixado sem cupom dado o valor futuro (valor de face), o prazo anualizado e a taxa % a.a.

        vf: float -> valor de face ou valor futuro. Se None, default para o valor de face padrão (R$ 1000)
        prazo_anual: float -> prazo anualizado (segundo convencao). Se None, default para prazo entre compra e vencimento
        taxa_anual: float -> taxa anualizada % a.a. Se None, default para a taxa anualizada setada na definição da classe
        """

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
        pu: float, 
        prazo_anual: float or None = None,
        valor_base: float or None = None
    ):
        """
        calcula a taxa anual % a.a. de um título prefixado sem cupom dados o PU, o prazo anualizado e o valor base ou valor de face

        valor_base: float -> valor de face ou valor futuro. Se None, default para o valor de face padrão (R$ 1000)
        prazo_anual: float -> prazo anualizado (segundo convencao). Se None, default para prazo entre compra e vencimento
        pu: float -> PU correspondente ao prazo anualizado
        """

        # prazo_anual default
        if prazo_anual is None:
            prazo_anual = self.calcula_prazo(
                dt_inicio = self.dt_compra,
                dt_fim = self.vencimento
            )

        # valor base default
        if valor_base is None:
            valor_base = self.valor_face

        # valor_base = pu * (1 + taxa_anual) ** prazo_anual
        taxa_anual = np.exp((np.log(valor_base) - np.log(pu)) / prazo_anual) - 1
        
        return taxa_anual

    def calcula_pu_ntnf(self,
        dt_base: str or dt.datetime or dt.date or None = None,
        tir: float or None = None,
        dt_venc: str or dt.datetime or dt.date = None,
    ):
        """
        calcula o fluxo de caixa completo dos eventos de uma LTN/NTN-F (cupons e retorno do principal).
        Retorna o PU final e um dataframe com o fluxop de caixa

        dt_base: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data a partir da qual queremos calcular o fluxo
            Se None, default para data de compra
        tir: float -> a taxa interna de retorno. Se None, default para a taxa anual definida na classe
        dt_venc: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        """

        # dt_base default
        if dt_base is None:
            dt_base = self.dt_compra

        # tir default
        if tir is None:
            tir = self.taxa_anual

        # vencimento default
        if dt_venc is None:
            dt_venc = self.vencimento

        # prazo_anualizado_final = self.calcula_prazo(
        #     dt_inicio = dt_base,
        #     dt_fim = dt_venc
        # )

        # ncupons = int(prazo_anualizado_final * 2) + 1  # arredondar para cima
        # cashflow_dtidx = pd.date_range(
        #     end = dt_venc,
        #     freq = '6MS',
        #     periods = ncupons,
        #     name = 'data'
        # )
        
        # construindo o dataframe de cashflow
        # o índice são as datas dos eventos
        cashflow_dtidx = self.constroi_fluxo() # os argumentos padrão (dt_fim = data do vencimento e tir = taxa anual) já servem

        # estruturando o dataframe
        # vamos adicionar as colunas uma a uma
        cashflow = pd.DataFrame([],
            index = cashflow_dtidx
        )

        # vamos transformar o indice do dataframe em Series para facilitar a operação
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
                closed = 'left',  # o número de dias entre a data base (inclusive) e a data do evento (exclusive)
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

        # fator de desconto
        cashflow['fator_desconto'] = prazo_anualizado_s.apply(lambda prazo_anual: (1 + tir) ** prazo_anual)

        # parcela do PU devido a cada um dos pagamentos trazidos a valor presente
        cashflow['pu'] = cashflow['vf'] / cashflow['fator_desconto']

        # dropar pu's == 0 (LTN)
        cashflow = cashflow.drop(labels = cashflow.index[np.isclose(cashflow['pu'], 0)])

        pu = cashflow['pu'].sum()
        
        return pu, cashflow
    
    def __str__(self):        
        if self.taxa_cupom == 0:
            s = 'LTN (Tesouro Prefixado)'
        else:
            s = 'NTN-F (Tesouro Prefixado com pagamento de cupom)'
        
        s += f' {self.vencimento.year}'
        s += f' a {self.taxa_anual:.2%} a.a.'

        if self.dt_compra is not None:
            s += f" comprado em {self.dt_compra:%d/%m/%Y}"
        
        return s
    
    def __repr__(self):
        r = 'Prefixado('
        r += f'vencimento = {self.vencimento:%d/%m/%Y}, '
        r += f'taxa_anual = {self.taxa_anual}, '
        
        if self.dt_compra is not None:
            r += f'dt_compra = {self.dt_compra:%d/%m/%Y}, '
        
        r += f'taxa_cupom = {self.taxa_cupom}, '

        if self.valor_face != 1000:
            r += f'valor_face = {self.valor_face}, '
        
        r += f"convencao = '{self.convencao}'"
        r += ')'
        
        return r
        

## OBS: se pagamento cair no feriado, pagamento no dia anterior
# data emissao - emissao do título
# data de vencimento - 
# %%
