#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
from abc import abstractmethod
import numpy as np
from . import portfolio

class Volatility(portfolio.Portfolio):
    """ Volatility models for a portfolio of securities"""

    models = [ 'hist', 'ewma' ]

    def __new__(cls,     
        model: str = 'ewma',
        window: int or None = None,
        annualize: float = 252,
        *args, **kwargs
    ):

       # if cls.__name__ == 'Volatility': # base class. Let's try to instantiate one of the subclasses directly
       # Let's try to instantiate one of the subclasses directly
        if model in MODELS:
            cls = MODELS[model]
        else:  # failed. Raise Exception
            classes = [ f"{klass.__name__}()" for klass in MODELS.values() ]
            raise TypeError(f"Instantiate one of {', '.join(classes)} directly")

        # create self object of class 'cls' (which we tried to define above)
        self = portfolio.Portfolio.__new__(cls)

        # call Portfolio __init__ method with all the arguments for building the portfolio on which we'll model the volatility
        super(cls, self).__init__(*args, **kwargs)

        # set some properties
        self.model = model
        self.annualize = annualize
        self.window = window

        # finally, call the subclass __init__ method (which might have additional arguments for each vol model)
        self.__init__(*args, **kwargs)

        return self

    @property
    @abstractmethod
    def vol_pp(self):
        raise NotImplementedError("'vol_pp()' method on this volatility model is not implemented.")

    @property
    def vol(self):
        return self.vol_pp * np.sqrt(self.annualize)
    
    # check attributes for illegal values and requirements for each model type
    
    def _get_check_model(self, model = 'ewma'):
        if model not in self.models:
            model_list = [ f"'{model}'" for model in self.models ]
            raise ValueError(f"Invalid model. Must be one of {', '.join(model_list)}.")
        return model

    @property
    def model(self):
        return self.__model

    @model.setter
    def model(self, model):
        self.__model = self._get_check_model(model = model)
        
    def _get_check_window(self, window, *args, **kwargs):
        argname = 'window'

        check_val = window is None or int(window) + 0 > 0
        if not check_val:
            raise ValueError(f"Argument '{argname}' must be an integer greater than zero.")
            
        if window is None:
            return window    
        else:
            return int(window)
    
    @property
    def window(self):
        return self.__window
    
    @window.setter
    def window(self, window):
        self.__window = self._get_check_window(window = window, model = self.model)

    def _get_check_annualize(self, annualize, *args, **kwargs):
        argname = 'annualize'

        if annualize is None:
            raise TypeError(f"Argument '{argname}' must be set for all volatility models.")

        check_val = float(annualize) + 0 > 0
        if not check_val:
            raise ValueError(f"Argument '{argname}' must be an float greater than zero.")
            
        return float(annualize)

    @property
    def annualize(self):
        return self.__annualize

    @annualize.setter
    def annualize(self, annualize):
        self.__annualize = self._get_check_annualize(annualize = annualize, model = self.model)
    
    def __str__(self):
        s = f'{__name__}.{self.__class__.__name__}'

        if self.window is not None:
            s += f', window = {self.window} periods'
        
        if not np.isclose(self.annualize, 252):
            s += f', annualization factor = √{self.annualize}'
        
        return s

class EWMA(Volatility):

    def __init__(self, 
        lambd: float, 
        *args, **kwargs
    ):
        self.lambd = lambd
    
    @property
    def vol_pp(self):
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
    
    def _get_check_lambd(self, lambd, *args, **kwargs):
        argname = 'lambd'
        model = self.__class__.__name__.lower()

        # if lambd is None:
        #     raise TypeError(f"Argument '{argname}' must be set for model '{model}'.")

        check_val = isinstance(lambd, float)
        if not check_val:
            raise ValueError(f"Argument '{argname}' must be a float-like object.")
            
        return float(lambd)

    @property
    def lambd(self):
        return getattr(self, f'_{self.__class__.__name__}__lambd')

    @lambd.setter
    def lambd(self, lambd):
        self.__lambd = self._get_check_lambd(lambd = lambd)

    def __str__(self):
        s = super().__str__()

        s += f', λ = {self.lambd}'
        
        return s

class Hist(Volatility):
    
    @property
    def vol_pp(self):
        logrets = self.logreturns
        
        if self.window is not None:
            return logrets.rolling(
                window = self.window,
            ).std()
        
        else:
            return logrets.std()


MODELS = { 
    volmodel_name.lower(): volmodel for volmodel_name, volmodel in locals().items() 
    if (
        isinstance(volmodel, type) and
        issubclass(volmodel, Volatility) and 
        volmodel.__name__ != 'Volatility' 
    )
}