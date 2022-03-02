#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
import numpy as np
import pandas as pd
from . import tools, portfolio

class Volatility(portfolio.Portfolio):
    """ Volatility models for a portfolio of securities"""

    models = [ 'hist', 'ewma' ]

    def __init__(self,
        model: str = 'ewma',
        annualize: float = 252,
        window: int = None,
        lambd: int = None,
        *args, **kwargs
    ):
        """create volatility model

        Args:
            model (str, optional): model specification. One of a list of model specs. Defaults to 'ewma'.
            annualize (int, optional): number of periods in one year e.g. 252 if daily periods. Defaults to 252.
            window (int, optional): size of rolling window for volatility calculations. Defaults to None, which includes the whole timeseries
            lambd (int, optional): if model == 'ewma', weight given to old vol. (1 - lambd) weight is given to new return
        """

        super().__init__(*args, **kwargs)

        self.model = self.get_check_model(model)
        self.annualize = annualize
        self.window = window
        self.lambd = lambd

    def get_check_model(self, model = 'ewma'):
        if model is not None and model not in self.models:
            raise ValueError(f"Invalid model. Must be one of {', '.join(self.models)[:-2]}.")
        return model

    def __vol_pp_hist(self):
        logrets = self.logreturns
        
        if self.window is not None:
            return logrets.rolling(
                window = self.window,
            ).std()
        
        else:
            return logrets.std()


    def __vol_pp_ewma(self):
        logrets = self.logreturns
        vol_ewma = logrets.ewm(
            alpha = 1 - self.lambd,
            adjust = False,
            min_periods = self.window or logrets.shape[0] - 1,
        ).std()

        if self.window is None:
            return vol_ewma[-1]
        else:
            return vol_ewma

    @property
    def vol_pp(self):
        
        func_vol = [ 
            v for k, v in self.__class__.__dict__.items()
            if k.startswith(f'_{self.__class__.__name__}__vol_pp') and # mangling
               k.endswith(self.model) ] 

        if len(func_vol) == 0:
            raise ReferenceError(f"No function available to model vol (to fix, define function '__vol_pp_{self.model}').") 

        else:
            return func_vol[0](self) 

    @property
    def vol(self):
        return self.vol_pp * np.sqrt(self.annualize)
    

