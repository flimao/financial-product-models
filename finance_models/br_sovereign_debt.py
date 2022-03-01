#!/usr/bin/env python3
#-*- coding: utf-8 -*-

from typing import List
import datetime as dt
import numpy as np
import pandas as pd
from . import tools, fixed_income

# INDICES (códigos para baixar as timeseries do BCB)

SELIC = 11
IPCA = 433
IGPM = 189


class TesouroDireto:
    """
    Define um Título Genérico de Dívida Soberana do Brasil
    """
    def __init__(self, 
        vencimento: int or dt.date or dt.datetime,
        taxa_anual: float,
        dt_compra: str or dt.date or dt.datetime or None = None,
        convencao: str = 'DU/252',
    ):
        """
        parâmetros:

        'vencimento': data do vencimento. Caso seja um int, interpretamos como o ano do vencimento,
            a data do vencimento é 01/01/'vencimento'
        
        'taxa_anual': a taxa prefixada (% a.a.) pelo qual o título foi adquirido
        
        'dt_compra': data da compra (liquidacao) do título. Pode ser None, caso não queiramos incluir a data de compra

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
        prazo_anualizado = tools.get_annualized_time(
            date_begin = dt_inicio,
            date_end = dt_fim,
            holidays = feriados,
            convention = convencao
        )

        return prazo_anualizado
    
    def calcula_pu(self,
        vf: float or None = None, 
        prazo_anual: float or None = None, 
        taxa_anual: float or None = None,
    ):
        """
        calcula o PU de um fluxo dado o valor futuro, o prazo anualizado e a taxa % a.a.

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

        pu = fixed_income.calc_pv(fv = vf, time = prazo_anual, rate = taxa_anual)

        return pu
    
    def calcula_taxa_anual(self,
        pu: float,
        valor_base: float = 100,
        prazo_anual: float or None = None,

    ):
        """
        calcula a taxa anual % a.a. associada a um fluxo dados o PU (valor presente), o prazo anualizado e o valor base (valor futuro)

        valor_base: float -> valor de face ou valor futuro. Se None, default para R$ 100 (base percentual)
        prazo_anual: float -> prazo anualizado (segundo convencao). Se None, default para prazo entre compra e vencimento
        pu: float -> PU correspondente ao prazo anualizado (valor presente)
        """

        # prazo_anual default
        if prazo_anual is None:
            prazo_anual = self.calcula_prazo(
                dt_inicio = self.dt_compra,
                dt_fim = self.vencimento
            )

        taxa_anual = fixed_income.calc_rate(pv = pu, fv = valor_base, time = prazo_anual)
        
        return taxa_anual
    
    def constroi_fluxo(self,
        dt_fim: str or dt.datetime or dt.date or None = None, 
        frequencia: int = 6, # meses
        dt_base: str or dt.datetime or dt.date or None = None, 
    ):

        """
        calcula lista com as datas dos eventos (pagamento de cupom e retorno do principal) de uma LTN/NTN-F

        dt_fim: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        frequencia: int -> o número de meses entre eventos
        dt_base: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data que queremos para o começo do fluxo
            Se None, default para data de compra
        """
        # datas dos pagamentos dos cupons, amortização etc
        # em títulos do tesouro direto, só cupons mesmo
        if dt_fim is None:
            dt_fim = self.vencimento
        elif isinstance(dt_fim, str):
            dt_fim = tools.str2dt(dt_fim)

        # dt_base default
        if dt_base is None:
            if self.dt_compra is None:
                raise TypeError(f"Não foi especificada a data de compra do título {self}.")
            dt_base = self.dt_compra
        elif isinstance(dt_base, str):
            dt_base = tools.str2dt(dt_base)


        # f_periods = (dt_fim - dt_base) / dt.timedelta(days = frequencia * (360/12))
        # n_periods = int(f_periods) + 1
        
        # # os pagamentos são espaçados de 6 em 6 meses, a contar para trás desde o vencimento do título, até a data base (que pode ou não cair no fluxo)
        # series_datas_fluxos = pd.date_range(
        #     freq = f'{frequencia}M',
        #     end = dt_fim,
        #     periods = n_periods,
        #     name = 'data'
        # ) + pd.Timedelta(f'{dt_fim.day} days')

        lista_data_fluxos = [ pd.Timestamp(dt_fim) ]

        while lista_data_fluxos[-1] > pd.Timestamp(dt_base):
            nova_data = lista_data_fluxos[-1] - pd.offsets.DateOffset(months = frequencia)
            lista_data_fluxos.append(nova_data)

        return list(reversed(lista_data_fluxos[:-1]))
    
    def __str__(self):
        s = f'Titulo Genérico com vencimento em {self.vencimento:{tools.DT_FMT}} a {self.taxa_anual:.2%} a.a.'
        if self.dt_compra is not None:
            s += f' comprado em {self.dt_compra:{tools.DT_FMT}}'
        
        return s

    def __repr__(self):
        r = f'{self.__class__.__name__}('
        r += f'vencimento = {self.vencimento:{tools.DT_FMT}}, '
        r += f'taxa_anual = {self.taxa_anual}, '
        
        if self.dt_compra is not None:
            r += f'dt_compra = {self.dt_compra:{tools.DT_FMT}}, '
               
        r += f"convencao = '{self.convencao}'"
        r += ')'
        
        return r

class Prefixado(TesouroDireto):
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
        super().__init__(
            vencimento = vencimento,
            taxa_anual = taxa_anual,
            dt_compra = dt_compra,
            convencao = convencao
        )
        
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
    
    def constroi_fluxo2(self,
        dt_fim: str or dt.datetime or dt.date or None = None, 
        frequencia: int = 6, # meses
        dt_base: str or dt.datetime or dt.date or None = None, 
    ):

        """
        calcula lista com as datas dos eventos (pagamento de cupom e retorno do principal) de uma LTN/NTN-F

        dt_fim: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        frequencia: int -> o número de meses entre eventos
        dt_base: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data que queremos para o começo do fluxo
            Se None, default para data de compra
        """
        f = self.constroi_fluxo2
        #raise DeprecationWarning(f"{f.__name__} is deprecated and will be removed in a future version.")

        # datas dos pagamentos dos cupons, amortização etc
        # ntnf é só cupons mesmo
        if dt_fim is None:
            dt_fim = self.vencimento
        elif isinstance(dt_fim, str):
            dt_fim = tools.str2dt(dt_fim)

        # dt_base default
        if dt_base is None:
            dt_base = self.dt_compra
        elif isinstance(dt_base, str):
            dt_base = tools.str2dt(dt_base)

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

        # construindo o dataframe de cashflow
        # o índice são as datas dos eventos
        cashflow_dtidx = self.constroi_fluxo(
            dt_base = dt_base,
            dt_fim = dt_venc,
            frequencia = 6 # meses
        ) # os argumentos padrão (dt_fim = data do vencimento e tir = taxa anual) já servem

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
            s += f" comprado em {self.dt_compra:{tools.DT_FMT}}"
        
        return s
    
    def __repr__(self):
        r = f'{self.__class__.__name__}('
        r += f'vencimento = {self.vencimento:{tools.DT_FMT}}, '
        r += f'taxa_anual = {self.taxa_anual}, '
        
        if self.dt_compra is not None:
            r += f'dt_compra = {self.dt_compra:{tools.DT_FMT}}, '
        
        r += f'taxa_cupom = {self.taxa_cupom}, '

        if self.valor_face != 1000:
            r += f'valor_face = {self.valor_face}, '
        
        r += f"convencao = '{self.convencao}'"
        r += ')'
        
        return r
        
class Indexado(TesouroDireto):
    """
    Define um Título Indexado/Pós-fixado de Dívida Soberana do Brasil
    """

    # atributo de classe: dicionario com as timeseries do BCB, sendo preenchidos conforme 
    # classe vai sendo instanciada
    indices = dict()

    def __init__(self,
        vencimento: int or dt.date or dt.datetime,
        taxa_anual: float,
        indice: pd.Series or int,
        dt_compra: str or dt.date or dt.datetime or None = None,
        taxa_cupom: float or bool = True,
        vna0: float = 1000.,
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
        super().__init__(
            vencimento = vencimento,
            taxa_anual = taxa_anual,
            dt_compra = dt_compra,
            convencao = convencao
        )

        # indice original
        self.indice_original = indice

        # temos que sobrescrever o vencimento caso se trate de uma NTN-B
        # vence dia 15 de maio em ano de vencimento ímpar e 15 de agosto em ano de vencimento par
        if self.indice_original == IPCA:
            venc_day = 15
            if self.vencimento.year % 2 == 0:
                venc_mon = 8
            else:
                venc_mon = 5
            
            self.vencimento = dt.date(
                year = self.vencimento.year,
                month = venc_mon,
                day = venc_day
            )
        
        elif self.indice_original == SELIC:
            if self.vencimento.year % 2 == 0:
                venc_mon = 9
            else:
                venc_mon = 3
            
            self.vencimento = dt.date(
                year = self.vencimento.year,
                month = venc_mon,
                day = self.vencimento.day
            )
                
        # vna original
        self.vna0 = vna0
        if isinstance(self.indice_original, int) and self.indice_original == IPCA:
            self.vna_data0 = '15/07/2000'
        else:
            self.vna_data0 = '01/07/2000'

        # indice timeseries
        if isinstance(indice, int):
            self.indice = self.conserta_indice(
                indice_original = indice,
                dt_inicio = self.vna_data0,
                dt_fim = self.dt_compra
            )
        else:  # se não for int, é a própria timeseries
            self.indice = indice
        
        # taxa_cupom
        if isinstance(taxa_cupom, bool):
            if taxa_cupom:
                self.taxa_cupom = 6/100
            else:
                self.taxa_cupom = 0.
        else:
            self.taxa_cupom = taxa_cupom
                  
    def conserta_indice(self,
        indice_original: int or pd.Series or None = None, 
        dt_inicio: dt.date or dt.datetime or str or None = None, 
        dt_fim: dt.date or dt.datetime or str or None = None
    ):
        """acerta uma serie temporal para iniciar e terminar nas datas estipuladas, projetando linearmente

        Args:
            indice_original (int or pd.Series): uma serie temporal com a evolução do índice. Caso seja um int, baixa a serie correspondente do BCB
            dt_inicio (dt.date or dt.datetime or str): data de inicio estipulada
            dt_fim (dt.date or dt.datetime or str): data de fim estipulada

        Returns:
            pd.Series: serie temporal acertada
        """
        
        # dt_inicio default
        if dt_inicio is None:
            dt_inicio = self.vna_data0

        # dt_fim default
        if dt_fim is None:
            dt_fim = self.dt_compra
        
        # indice_original default
        if indice_original is None:
            indice_original = self.indice_original

        # primeiro baixa a serie do BCB se necessário
        if isinstance(indice_original, int):
                     
            ts = tools.get_bcb_ts(
                codigo_bcb = indice_original,
            )

            if indice_original not in Indexado.indices:
                Indexado.indices[indice_original] = ts
            
        else:
            ts = indice_original.copy()

            # a série do BCB é estranha: e.g. a variação do IPCA de julho para agosto de 2000 foi de 1.61% a.m.. Na série do BCB
            # isso está registrado na entrada de julho de 2000. Sendo assim, vamos shiftar a série do BCB em um período. No exemplo,
            # a série passa a indicar a variação entre o mês anterior e o mês atual (a variação de julho para agosto passa a ser indicada
            # na entrada de agosto)


        # depois acerta a timeseries do indice para bater as datas de inicio e fim
        indice = tools.fix_timeseries_ends(
            ts_orig = ts,
            date_begin = dt_inicio,
            date_end = dt_fim
        )

        return indice      
    
    def calcula_vna(self,
        indice: int or pd.Series or None = None, 
        dt_inicio: dt.date or dt.datetime or str or None = None, 
        dt_fim: dt.date or dt.datetime or str or None = None,
        vna0: float or None = None
    ):
        """acerta uma serie temporal para iniciar e terminar nas datas estipuladas, projetando linearmente

        Args:
            indice_original (int or pd.Series): uma serie temporal com a evolução do índice. Caso seja um int, baixa a serie correspondente do BCB
            dt_inicio (dt.date or dt.datetime or str): data de inicio estipulada. Se None, default para data do VNA0
            dt_fim (dt.date or dt.datetime or str): data de fim estipulada. Se None, default para data de compra
            vna0 (float): VNA na dt_inicio. Caso None, default para R$ 1000

        Returns:
            pd.Series: serie temporal acertada
        """
        
        # precisamos construir uma nova timeseries?
        construir_ts = False

        # dt_inicio default
        if dt_inicio is None:
            dt_inicio = self.vna_data0
        else:
            construir_ts = True
        if isinstance(dt_inicio, str):
            dt_inicio = tools.str2dt(dt_inicio)


        # dt_fim default
        if dt_fim is None:
            dt_fim = self.dt_compra
        else:
            construir_ts = True
        if isinstance(dt_fim, str):
            dt_fim = tools.str2dt(dt_fim)
    
        # indice default
        if indice is None and not construir_ts:
            indice = self.indice

        else:
            indice = self.conserta_indice(
                indice_original = self.indice_original,
                dt_inicio = dt_inicio,
                dt_fim = dt_fim
            )
        
        # indice é um pouco estranho. Por exemplo, a inflação entre julho e agosto de 2000 foi de 1.61% a.m.
        # o indice registra isso em julho de 2000 (ao invés de agosto, que seria o mais natural)
        # vamos corrigir essa série antes de calcular o VNA
        indice = indice.shift(1).fillna(0)

        # vna default
        if vna0 is None:
            vna0 = self.vna0    

        fator_vna = np.exp(np.log(1 + indice/100).sum())
        #fator_vna = (1 + indice/100).prod()

        vna = vna0 * fator_vna

        return vna

    def calcula_cotacao_df(self,
        dt_base: str or dt.datetime or dt.date or None = None,
        taxa_anual: float or None = None,
        dt_venc: str or dt.datetime or dt.date = None,
    ):
        """
        Retorna um dataframe com o cashflow final de um título Indexado (com ou sem pagamento de cupons)

        dt_base: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data a partir da qual queremos calcular o fluxo
            Se None, default para data de compra
        taxa_anual: float -> a taxa interna de retorno. Se None, default para a taxa anual definida na classe
        dt_venc: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        """

        # dt_base default
        if dt_base is None:
            dt_base = self.dt_compra

        # tir default
        if taxa_anual is None:
            taxa_anual = self.taxa_anual

        # vencimento default
        if dt_venc is None:
            dt_venc = self.vencimento
        
        # construindo o dataframe de cashflow
        # o índice são as datas dos eventos
        cashflow_dtidx = self.constroi_fluxo(
            dt_base = dt_base,
            dt_fim = dt_venc,
            frequencia = 6 # meses
        )

        # estruturando o dataframe
        # vamos adicionar as colunas uma a uma
        cashflow = pd.DataFrame([],
            index = cashflow_dtidx
        )
        cashflow.index.name = 'data'

        # vamos transformar o indice do dataframe em Series para facilitar a operação
        data = cashflow.index.to_series()
    
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
        cashflow['fator_desconto'] = prazo_anualizado_s.apply(lambda prazo_anual: (1 + taxa_anual) ** prazo_anual)

        # cotação individual
        taxa_cupom_as = (1 + self.taxa_cupom) ** (6/12) - 1
        cashflow['cotacao'] = taxa_cupom_as / cashflow['fator_desconto']

        cashflow.loc[pd.Timestamp(dt_venc), 'cotacao'] += 1 / cashflow.loc[pd.Timestamp(dt_venc), 'fator_desconto']
        cashflow = cashflow.drop(index = cashflow.index[np.isclose(cashflow['cotacao'], 0)])
        
        return cashflow 
    
    def calcula_pu_indexado(self,
        dt_base: str or dt.datetime or dt.date or None = None,
        taxa_anual: float or None = None,
        dt_venc: str or dt.datetime or dt.date = None,
    ):
        """
        Retorna o PU final de um título Indexado (com ou sem pagamento de cupons)

        dt_base: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data a partir da qual queremos calcular o fluxo
            Se None, default para data de compra
        taxa_anual: float -> a taxa interna de retorno. Se None, default para a taxa anual definida na classe
        dt_venc: data (str no formato 'DD/MM/YYYY' ou objeto date/datetime): a data do fim dos pagamentos
            Se None, default para data de vencimento
        """
        # dt_base default
        if dt_base is None:
            dt_base = self.dt_compra

        # tir default
        if taxa_anual is None:
            taxa_anual = self.taxa_anual

        # vencimento default
        if dt_venc is None:
            dt_venc = self.vencimento
        
        cashflow = self.calcula_cotacao_df(dt_base = dt_base, taxa_anual = taxa_anual, dt_venc = dt_venc)
        cotacao = cashflow['cotacao'].sum()

        vna = self.calcula_vna(dt_fim = dt_base)
        
        pu = vna * cotacao
        return pu


    def __str__(self):
        if not isinstance(self.indice_original, int):
            return super().__str__()

        if self.indice_original == SELIC:
            nome_antigo = 'LFT'
            nome_novo = 'Tesouro SELIC'
            indice = 'SELIC'

        elif self.indice_original == IPCA:
            indice = 'IPCA'
            if self.taxa_cupom == 0:
                nome_antigo = 'NTN-B Principal'
                nome_novo = 'Tesouro IPCA+'
            else:
                nome_antigo = 'NTN-B'
                nome_novo = 'Tesouro IPCA+ com pagamento de cupom'

        elif self.indice_original == IGPM:
            nome_antigo = 'NTN-C'
            nome_novo = 'Tesouro IGPM+ com pagamento de cupom'
            indice = 'IGP-M'          

        s = f'{nome_antigo} ({nome_novo})'
        
        s += f' {self.vencimento.year}'
        s += f' a {indice} {self.taxa_anual:+.2%} a.a.'

        if self.dt_compra is not None:
            s += f" comprado em {self.dt_compra:{tools.DT_FMT}}"
        
        return s
    
    def __repr__(self):
        r = f'{self.__class__.__name__}('
        r += f'vencimento = {self.vencimento:{tools.DT_FMT}}, '
        r += f'taxa_anual = {self.taxa_anual}, '
        
        if isinstance(self.indice_original, int):
            r += f'indice = {self.indice_original}, '
        
        if self.dt_compra is not None:
            r += f'dt_compra = {self.dt_compra:{tools.DT_FMT}}, '
        
        r += f'taxa_cupom = {self.taxa_cupom}, '
        
        r += f"convencao = '{self.convencao}'"
        r += ')'
        
        return r