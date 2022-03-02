#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
from abc import abstractmethod
import numpy as np
from scipy.stats import norm
from .. import tools, volatility as vol

# package info
__all__ = [
    'binarytree'
]

__author__ = 'Felipe Oliveira'
__version__ = '1.3.0'

# black scholes merton
class BlackScholes:
    """Black-Scholes-Merton european call pricing model
    """

    def __init__(self,
        S0: float,
        K: float,
        r: float,
        T: float,
        vol: float,
        q: float = 0,
        *args, **kwargs
    ):
        """Black-Scholes-Merton european option pricing model

        Args:
            S0 (float): underlying asset spot price at t0
            K (float): strike (price at which payoff curve changes behavior)
            r (float): risk-free rate (in % p.p.)
            T (float): expiration (units are the same period as the risk free rate. e.g. if risk-free rate is % p.a., then expiration is in years)
            q (float, optional): rate at which the underlying asset pays out dividends. Defaults to 0.
            vol (float or vol.Volatility): volatility. Accepts a float (also same unit as risk-free rate)
        """

        self.S0 = S0
        self.K = K
        self.r = r
        self.q = q
        self.T = T

        self.vol = self._get_check_vol(vol)

        # calculation
        self.d1 = (np.log(self.S0 / self.K) + (self.r - self.q + self.vol**2 / 2) * self.T) / (self.vol * np.sqrt(self.T))
        self.d2 = self.d1 - self.vol * np.sqrt(self.T)

    @property
    def call(self):
        """call price"""
        return self.S0 * np.exp(-self.q * self.T) * norm.cdf(self.d1) - self.K * np.exp(-self.r * self.T) * norm.cdf(self.d2)
    
    @property
    def put(self):
        """put price"""
        return self.K * np.exp(-self.r * self.T) * norm.cdf(-self.d2) - self.S0 * np.exp(-self.q * self.T) * norm.cdf(-self.d1)
    
    def _get_check_vol(self, vol):
        if vol < 0:
            raise ValueError(f"Volatility must be non-negative.")
        
        return vol


class BlackScholesPortfolio:  # vol.Volatility already inherits from Portfolio
    """Black-Scholes-Merton european call pricing model based on portfolios"""

    def __init__(self,
        K: float,
        r: float,
        T: float,
        base_date: str or dt.date or dt.datetime,
        q: float = 0,
        *args, **kwargs
    ):
        """Black-Scholes-Merton european option pricing model based on portfolio

        Args:
            K (float): strike (price at which payoff curve changes behavior)
            r (float): risk-free rate (in % p.p.)
            T (float): expiration (units are the same period as the risk free rate. e.g. if risk-free rate is % p.a., then expiration is in years)
            q (float, optional): rate at which the underlying asset pays out dividends. Defaults to 0.
            all other inputs to the Black-Scholes-Merton model are calculated from the portfolio and the volatility parameters
        """

        # call vol.Volatility __init__ method (which will call Portfolio __init__ method). if a portfolio exists, then we can get a few things 
        # automagically
        # rename argument 'volmodel' to 'model'
        if 'volmodel' in kwargs:
            kwargs['model'] = kwargs['volmodel']
        self.vol_model = vol.Volatility(*args, **kwargs)
        
        # store base_date
        self.base_date = self._get_check_base_date(base_date)

        # spot price is price at base date
        try:
            S0 = self.vol_model.portfolio_total[self.base_date]
        except AttributeError:  # no portfolio_value, meaning no portfolio built
            raise TypeError(f"Must input parameters to build portfolio.")

        vol_bs = self._get_check_vol(self.vol_model.vol)

        self.blackscholes = BlackScholes(
            S0 = S0,
            K = K,
            T = T,
            r = r,
            q = q,
            vol = vol_bs
        )
    
    @property
    def call(self):
        """call price"""
        return self.blackscholes.call
    
    @property
    def put(self):
        """put price"""
        return self.blackscholes.put

    def _get_check_base_date(self, base_date):
        if isinstance(base_date, str):
            return tools.str2dt(base_date)
        else:
            return base_date

    def _get_check_vol(self, vol):
       
        # vol is a float: no window parameter
        if isinstance(vol, float):            
            return vol
        
        # vol is not a float, probably a Series. get the series on the base_date
        else:
            return vol[self.base_date]
