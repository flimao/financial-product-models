#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import pandas as pd
import numpy as np

class Portfolio:
    """ define Portfolio class. ingest and massage portfolio prices and notionals"""
    def __init__(self, 
        securities_values: pd.DataFrame or pd.Series = None, 
        notionals: pd.DataFrame or pd.Series or None = None,
        na: str or None = 'drop',
    ):
        """__init__ function

        Args:
            securities_values (DataFrame or Series): timeseries for prices of each security in a portfolio
                            Each column is a security (if Series, assumed only one security)
            notionals (DataFrame or Series, optional): Quantities of each security. 
                If DataFrame, columns are securities (same as securities_values) and rows are dates (same as securities_values)
                If Series, quantities for each security are on each row and assumed to be constant over time
                If int or float, there is only one security whose notional is fixed in time
                If None, securities_values assumed to be the actual values in the portfolio (as opposed to prices)
            dropna (bool): drop the NaN values from the portfolio values or not
        """

        if securities_values is None:
            # no securities_values provided
            # nothing to be done
            return 

        if isinstance(securities_values, pd.Series):
            # securities_values is Series
            # assumed to be only one security
            # securities_values.name must be set to the security name
            self.securities_values = securities_values.to_frame()
        
        else:
            self.securities_values = securities_values

        if notionals is None:
            # notionals is None, therefore
            # portfolio totals for each security is assumed to be securities_values
            self.notionals = pd.DataFrame(1, columns = self.securities_values.columns, index = self.securities_values.index)
            self.portfolio_values = self.securities_values.copy()
        
        elif isinstance(notionals, pd.Series):
            # notionals is Series, therefore is assumed to be timeseries of notionals
            # for each security
            # multiply each row of securities_values by notional Series
            self.notionals = notionals
            self.portfolio_values = self.securities_values.multiply(self.notionals)
        
        elif isinstance(notionals, pd.DataFrame):
            # notionals is DataFrame
            # multiply elementwise securities_values by notionals
            self.notionals = notionals.reindex(self.securities_values.index).fillna(method = 'ffill')
            self.portfolio_values = self.securities_values.multiply(self.notionals)
        else:
            # notionals is an int or float, therefore all securities assumed to have the same notional in the entire timeseries
            self.notionals = pd.DataFrame(notionals, columns = self.securities_values.columns, index = self.securities_values.index)
            self.portfolio_values = self.securities_values * notionals
        
        # drop NaNs
        if na == 'drop':
            self.portfolio_values.dropna(
                how = 'all',  # only when all values are nans in a given date
                inplace = True,
            )
        elif isinstance(na, str):  # na is string but not drop. filling na
            self.portfolio_values.fillna(
                method = na,
                inplace = True,
            )
        # if na is None, do nothing to address NaNs
        
        # sum each row (time) of portfolio_values
        self.portfolio_total = self.portfolio_values.sum(axis = 1)
        self.portfolio_total.name = 'portfolio_total' 


class VaR(Portfolio):
    """ calcula Value at Risk e Expected Shortfall de um Portfolio

    Args:
        Portfolio: objeto Portfolio
    """
    def calcula_retorno(self,
        precos: pd.Series or None = None, 
        holding_period: int = 1,
    ) -> pd.Series:
        """calcula o retorno relativo simples

        Args:
            precos (pd.Series): série temporal de preços
            holding_period (int): períodos entre o preço base e o preço atualizado
            
        Returns:
            pd.Series: série temporal de retorno relativo simples
        """
        
        # precos default
        if precos is None:
            precos = self.portfolio_total
        
        # construir os retornos
        ret = (precos

            # janela rolante com o holding_period + 1. Se o holding_period = 1, deseja-se que haja dois elementos na janela (dia 1 - dia 0)
            .rolling(holding_period + 1)

            # aplicar a função do retorno
            .apply(
                lambda precos_holding: precos_holding.iloc[-1] / precos_holding.iloc[0] - 1
            )
        )
        
        ret.name = 'retorno'
        return ret

    def calcula_log_retorno(self,
        precos: pd.Series or None = None,
        holding_period: int = 1,
    ) -> pd.Series:
        """calcula o log-retorno de uma serie temporal de preços

        Args:
            precos (pd.Series): série temporal de preços
            holding_period (int): períodos entre o preço base e o preço atualizado

        Returns:
            pd.Series: série temporal de log-retorno
        """
        # precos default
        if precos is None:
            precos = self.portfolio_total
        
        # construir os log-retornos
        ret = (precos

            # janela rolante com o holding_period + 1. Se o holding_period = 1, deseja-se que haja dois elementos na janela (dia 1 - dia 0)
            .rolling(holding_period + 1) 

            # aplicar a função do log-retorno
            .apply(
                lambda precos_holding: np.log(precos_holding.iloc[-1] / precos_holding.iloc[0])
            )
        )
        
        ret.name = 'log_retorno'
        return ret

    def calcula_var(self,
        retornos: pd.Series = None, 
        alpha: float = 0.05, 
        vlr_carteira_atual: float = None,
    ) -> float:
        """calcula o Value at Risk para uma série temporal de retornos

        Args:
            retornos (pd.Series): série temporal de retornos
            alpha (int or float): intervalo de confianca para o cálculo do VaR
            vlr_carteira_atual (float): valor atual da carteira

        Returns:
            float: valor do VaR calculado
        """
        # retornos default
        if retornos is None:
            retornos = self.calcula_retorno().iloc[:-1] # o VaR é calculado para ser aplicado no dia seguinte
        
        # vlr_carteira_atual default
        if vlr_carteira_atual is None:
            vlr_carteira_atual = self.portfolio_total.iloc[-1]

        # calculamos o percentil alpha dos retornos
        var_ret = retornos.quantile(alpha)

        # para obter o VaR (unidade monetária), precisamos multiplicar pelo valor da carteira atual
        var = var_ret * vlr_carteira_atual
        return var

    def calcula_es(self,
        retornos: pd.Series = None, 
        alpha: int or float = 0.05, 
        vlr_carteira_atual: float = None,
    ) -> float:
        """calcula o Expected Shortfall para uma série temporal de retornos

        Args:
            retornos (pd.Series): série temporal de retornos
            alpha (int or float): intervalo de confianca para o cálculo do VaR
            vlr_carteira_atual (float): valor atual da carteira

        Returns:
            float: valor do ES calculado
        """
        
        # retornos default
        if retornos is None:
            retornos = self.calcula_retorno().iloc[:-1] # o VaR é calculado para ser aplicado no dia seguinte
        
        # vlr_carteira_atual default
        if vlr_carteira_atual is None:
            vlr_carteira_atual = self.portfolio_total.iloc[-1]
        
        # primeiramente, calculamos o var
        var = self.calcula_var(retornos, alpha, vlr_carteira_atual)

        # convertemos para o var em forma de retornos
        var_ret = var / vlr_carteira_atual

        # selecionamos dentre a lista de retornos somente os que estão abaixo do var_ret
        var_es = retornos[retornos <= var_ret]

        # dentre estes, convertemos novamente para unidades monetarias e fazemos a média
        es = (var_es * vlr_carteira_atual).mean()

        return es
    
    # função extra: cálculo da série temporal de VaR
    def calcula_ts_var(self,
        retornos: pd.Series or None = None, 
        alpha: float = 0.05, 
        valores: pd.Series or None = None,
        janela_var: int = 1000,
    ) -> pd.Series:
        """calcula uma série temporal de Value at Risk para uma série temporal de retornos

        Args:
            retornos (pd.Series): série temporal de retornos
            alpha (int or float): intervalo de confianca para o cálculo do VaR
            valores (pd.Series): série temporal com o valor da carteira em cada instante de tempo
            janela_var (int): número de períodos para calcular cada VaR
        Returns:
            pd.Series: valor dos VaRs calculados
        """
        # retornos default
        if retornos is None:
            retornos = self.calcula_retorno()

        # valores default
        if valores is None:
            valores = self.portfolio_total
        
        vars = (retornos
            # janela rolante do número de períodos para calcular o número de VaR's + 1
            .rolling(janela_var + 1)
            # aplicar função para cálculo de cada VaR
            .apply(
                lambda retorno_janela: self.calcula_var(
                    retornos = retorno_janela.iloc[:-1],
                    alpha = alpha,
                    vlr_carteira_atual = valores[retorno_janela.index[-1]],
                ),
            )
        )
        vars.name = f'VaR {1-alpha:.1%}'
        return vars
    
    
    # função extra: calcula a série temporal de ES
    def calcula_ts_es(self,
        retornos: pd.Series or None = None, 
        alpha: float = 0.05, 
        valores: pd.Series or None = None,
        janela_var: int = 1000,
    ) -> pd.Series:
        """calcula uma série temporal de Expected Shortfall para uma série temporal de retornos

        Args:
            retornos (pd.Series): série temporal de retornos
            alpha (int or float): intervalo de confianca para o cálculo do VaR
            valores (pd.Series): série temporal com o valor da carteira em cada instante de tempo
            janela_var (int): número de períodos para calcular cada VaR
        Returns:
            pd.Series: valor dos ES's calculados
        """
        # retornos default
        if retornos is None:
            retornos = self.calcula_retorno()

        # valores default
        if valores is None:
            valores = self.portfolio_total
        
        es = (retornos
            # janela rolante do número de períodos para calcular o número de VaR's + 1
            .rolling(janela_var + 1)
            # aplicar função para cálculo de cada VaR
            .apply(
                lambda retorno_janela: self.calcula_es(
                    retornos = retorno_janela.iloc[:-1],
                    alpha = alpha,
                    vlr_carteira_atual = valores.loc[retorno_janela.index[-1]],
                ),
            )
        )
        es.name = f'ES {1-alpha:.1%}'
        return es
    
    # função extra: calcula serie temporal de pnl
    def calcula_pnl(self,
        precos: pd.Series or None = None, 
        holding_period: int = 1,
    ) -> pd.Series:
        """calcula o retorno simples (PnL)

        Args:
            precos (pd.Series): série temporal de preços
            holding_period (int): períodos entre o preço base e o preço atualizado
            
        Returns:
            pd.Series: série temporal de PnL
        """
        
        # precos default
        if precos is None:
            precos = self.portfolio_total
        
        # construir os retornos
        ret = (precos

            # janela rolante com o holding_period + 1. Se o holding_period = 1, deseja-se que haja dois elementos na janela (dia 1 - dia 0)
            .rolling(holding_period + 1)

            # aplicar a função do retorno
            .apply(
                lambda precos_holding: precos_holding.iloc[-1] - precos_holding.iloc[0]
            )
        )
        
        ret.name = 'PnL'
        return ret