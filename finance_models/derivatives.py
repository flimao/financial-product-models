#!/usr/bin/env python3
#-*- coding: utf-8 -*-


import numpy as np
from scipy.stats import norm
from . import portfolio, volatility as vol

class BlackScholes(portfolio.Portfolio):
    """Black-Scholes-Merton european call pricing model
    """

    def __init__(self,
        S0: float,
        K: float,
        r: float,
        T: float,
        q: float = 0,
        vol: float or vol.Volatility = None,
        *args, **kwargs
    ):
        """Black-Scholes-Merton european option pricing model

        Args:
            S0 (float): underlying asset spot price at t0
            K (float): strike (price at which payoff curve changes behavior)
            r (float): risk-free rate (in % p.p.)
            T (float): expiration (units are the same period as the risk free rate. e.g. if risk-free rate is % p.a., then expiration is in years)
            q (float, optional): rate at which the underlying asset pays out dividends. Defaults to 0.
            vol (float or vol.Volatility): volatility. Accepts a float or a Volatility object (also same unit as risk-free rate)
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
       
        # vol is a float
        if isinstance(vol, float):
            if vol < 0:
                raise ValueError(f"Volatility must be non-negative.")
            
            return vol
        
        # vol is not a float. Must be a Volatility object
        else:
            vol_obj = vol.vol
            
            # .vol is a float, probably because window wass not specified
            if isinstance(vol_obj, float):
                return vol_obj
            
            # .vol is not a float. Probably a Series
            else:
                return vol_obj[-1]
