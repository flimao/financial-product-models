#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import datetime as dt
from abc import abstractmethod, ABC
import numpy as np
from tqdm import tqdm
from .. import volatility as volm, portfolio, tools


class BinomialTreePricing(ABC):
    """Binary Tree pricing model for derivatives.
    Abstract class (do not instantiate it directly)
    """

    def __new__(cls,
        
        T: float = None,
        dT: float = None,
        N: int = None,
        progressbar: bool = False,
        *args, **kwargs
    ):
        """Derivatives pricing model based on Binary Trees

        Args:
            T (float): expiration (units are the same period as the risk free rate. e.g. if risk-free rate is % p.a., then expiration is in years)
            dT (float): time step in the calculation
            N (float): number of instants in time in the binary tree
            progressbar (bool): whether tho show a progress bar in building the trees or not. Defaults to not (False)
        """

        self = super().__new__(cls)

        self.T, self.dT, self.N = self._get_check_steps(T = T, dT = dT, N = N)

        self.progressbar = progressbar

        return self

    @property
    def price(self):
        
        # calculation
        # if asset price tree doesn't exist, calculate it
        if getattr(self, 'asset_price_tree', None) is None:
            self.asset_price_tree = self.build_asset_tree()

        # same for derivative price tree
        if getattr(self, 'derivative_price_tree', None) is None:
            self.derivative_price_tree = self.build_derivative_tree()

        try:
            p = self.derivative_price_tree[0, 0]
        except TypeError:  # can't subscript the tree. Probably returned a NaN
            p = self.derivative_price_tree

        return p

    @abstractmethod
    def build_asset_node(self, current_node, *args, **kwargs):
        pass

    @abstractmethod
    def build_asset_tree(self):
        pass

    @abstractmethod
    def build_derivative_node(self, current_node, current_asset_node, *args, **kwargs):
        pass
    
    @abstractmethod
    def build_derivative_tree(self):
        pass
    
    def _get_check_steps(self, T, dT, N):
        
        # if more than one variable (out of the three ones) is None, raise TypeError
        if sum([ var is None for var in [T, dT, N] ]) > 1:
            raise TypeError("Two of ['T', 'dT', 'N'] arguments must be present.")

        # the relationship between the variables is (N-1) = T / dT

        if N is None:  # T and dT present
            N = T / dT + 1

            # if T isn't an exact multiple of dT, N will be fractional.
            # let's round N up (for better precision) and recalculate dT so the three match
            if T / dT != int(T / dT):
                N = int(N) + 1
                dT = T / (N - 1)

        elif T is None: # N and dT present
            T = (int(N) - 1) * dT
        
        else: # T and N present
            dT = T / (int(N) - 1)
        
        return T, dT, int(N)


class RandomWalkRisk(ABC):
    """abstract class implementing risk calculations for any asset whose risk is modelled as a random walk"""

    def calc_riskfree_proportion(self):
        # calculate risk-free proportion factor
        u = np.exp(self.vol * np.sqrt(self.dT))
        d = 1 / u
        p = (np.exp((self.r - self.q) * self.dT) - d)/(u - d)

        return u, d, p

# assets
class LinearPayoffAsset(ABC):
    """abstract class implementing any asset with a linear payoff."""

    def build_asset_tree(self):
        """builds binary tree for any asset with a linear payoff"""    
        # calculate up and down factors
        u, d, _ = self.calc_riskfree_proportion()

        # build tree
        # first node is the spot price
        #root = bt.Node(self.S0)
        tree = np.zeros((self.N, self.N))

        # for each level in the tree ...
        iterator = range(0, self.N - 1)
        if self.progressbar:
            iterator = tqdm(iterator, desc = 'Building asset price tree')

        for i in iterator:

            # for each node in the level i+1...
            for j in range(0, i+1):
                nd = tree[i:i+2, j:j+2]
                tree[i:i+2, j:j+2] = self.build_asset_node(current_node = nd, current_step = i, u = u, d = d)

        return tree


class StockGeneral(LinearPayoffAsset, ABC):
    """ abstract class implementing a stock asset, paying out dividends at a rate of q """
    def build_asset_node(self, current_node, current_step, u, d):
        
        # if it's the first node in the tree, S0
        if current_step == 0:
            current_node[0, 0] = self.S0
        
        curr_val = current_node[0, 0]

        current_node[1, 0] = curr_val * d
        current_node[1, 1] = curr_val * u

        return current_node


class FuturesGeneral(StockGeneral, ABC):
    """abstract class implementing a futures contract asset.

    A futures contract is special because, in theory, one doesn't incur any risk by entering into a futures contract. Therefore, the total riskfree rate
    is zero. One can think of this as a composition of the riskfree rate and a dividend paying out at a rate which is the same as the riskfree rate.
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.q = self.r


class CurrencyGeneral(StockGeneral, ABC):
    """ abstract class implementing a currency asset. 
    
    A currency asset is special because the total risk free rate is a composition of the riskfree rates of the pair ends
    E.g. if the currency pair is USD x ARS, then the total riskfree rate is rf_USD - rf_ARS
    """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.rf = kwargs.get('rf', None)
        if self.rf is not None:
            self.q = self.rf


# asset specialization
class Stock(StockGeneral, RandomWalkRisk, ABC):
    pass


class Futures(FuturesGeneral, RandomWalkRisk, ABC):
    pass


class Currency(CurrencyGeneral, RandomWalkRisk, ABC):
    pass


class OptionGeneralPricing(ABC):
# derivatives
    """ abstract class implementing the tree building rule for an option """

    def __init__(self,
        K: float,
        r: float,
        S0: float = None,
        vol: float = None,
        q: float = 0,
        *args, **kwargs
    ):
        """Derivatives pricing model based on Binary Trees

        Args:
            S0 (float): underlying asset spot price at t0
            K (float): strike (price at which payoff curve changes behavior)
            r (float): risk-free rate (in % p.p.)
            q (float, optional): rate at which the underlying asset pays out dividends. Defaults to 0.
            vol (float): volatility. Accepts a float (also same unit as risk-free rate) or a volatility model
        """

        self.K = K
        self.r = r
        self.q = q

        # check whether there are arguments for building a portfolio
        self.S0 = self._get_check_spot(S0, *args, **kwargs)

        # check whether there are arguments for builing a volatility model
        self.vol = self._get_check_vol(vol, *args, **kwargs)
 
    def build_derivative_tree(self):
        # calculate risk-free proportion factor
        _, _, p = self.calc_riskfree_proportion()

        # build tree
        # default is price the derivative at the last level then
        # bring it to today's dollars
        der_tree = np.zeros_like(self.asset_price_tree)
        
        # go one by one
        iterator = range(self.N - 2, -1, -1)

        if self.progressbar:
            iterator = tqdm(iterator, desc = 'Build derivative price tree')

        # backwards progression
        for i in iterator:
            
            for j in range(0, i+1):
                asset_node = self.asset_price_tree[i:i + 2, j: j + 2]
                der_node = der_tree[i: i + 2, j:j + 2]

                der_tree[i: i + 2, j:j + 2] = self.build_derivative_node(
                    current_node = der_node, 
                    current_asset_node = asset_node,
                    current_step = i,
                    proportion = p
                )
                    
        return der_tree
    
    def _get_check_spot(self, S0, *args, **kwargs):
        if S0 is not None:  # S0 is float-like
            return S0
        
        else: # S0 is None: Meaning inputs for building portfolio must have been passed
            base_date_raw = kwargs.get('base_date', None)
            base_date = self._get_check_date(base_date_raw)

            self.portfolio = portfolio.Portfolio(*args, **kwargs)
            pf = self.portfolio.portfolio_total

            if base_date is None:  # if base_date doesn't exist, get last entry from portfolio total
                return pf.iloc[-1]
            else:
                return pf[base_date]
            
    def _get_check_vol(self, vol, *args, **kwargs):

        if vol is not None:
            if vol < 0:
                raise ValueError(f"Volatility must be non-negative.")
        
        else: # vol is None. Meaning parameters were passed to create a vol model directly
            if 'volmodel' in kwargs:
                kwargs['model'] = kwargs['volmodel']
            self.volmodel = volm.Volatility(*args, **kwargs)
            vol = self.volmodel.vol

        return vol
    
    def _get_check_date(self, date_raw):
        date = date_raw
        if isinstance(date_raw, str):
            date = tools.str2dt(date_raw)
        
        return date

   
class Option(OptionGeneralPricing, BinomialTreePricing, ABC):
    """ abstract class implementing an option priced via binary trees """

    def __str__(self):
        s = f', with spot price $ {self.S0:.3f}, and strike $ {self.K:.3f}'
        s += f' (expiration = {self.T:.2f} years'
        s += f', risk-free rate = {self.r:.3%} p.a.'
        
        if self.q > 0:
            s += f', dividend yield = {self.q:.3%} p.a.'

        s += f', Binary Tree with {self.N} steps)'
        
        return s

class Call(ABC):
    """abstract class implementing the pricing rule for a call option"""
    def option_price(self, spot, strike):
        return max(spot - strike, 0)


class Put(ABC):
    """abstract class implementing the pricing rule for a put option"""
    def option_price(self, spot, strike):
        return max(strike - spot, 0)


class EuropeanOption(Option, ABC):
    """ abstract class implementing an european option, i.e. one may only exercise it at the time of expiration"""
    def build_derivative_node(self, current_node, current_asset_node, current_step, proportion):
        Stdown, Stup = current_asset_node[1, :]

        # if at expiration, price the call
        if current_step == self.N - 2:
            current_node[1, 0] = self.option_price(spot = Stdown, strike = self.K)
            current_node[1, 1] = self.option_price(spot = Stup, strike = self.K)

        # regardless, bring from future prices to today's dollars

        down, up = current_node[1, :]
        current_node[0, 0] = np.exp(-self.r * self.dT) * (
            proportion * up + (1 - proportion) * down
        )
    
        return current_node
    
    def __str__(self):
        return ' (european style)' + super().__str__()

class AmericanOption(Option, ABC):
    """ abstract class implementing an american option, i.e. one may exercise it at any time, from the beginning until the expiration"""
    def build_derivative_node(self, current_node, current_asset_node, current_step, proportion):
        Stdown, Stup = current_asset_node[1, :]

        # if at expiration, price the call
        if current_step == self.N - 2:
            current_node[1, 0] = self.option_price(spot = Stdown, strike = self.K)
            current_node[1, 1] = self.option_price(spot = Stup, strike = self.K)

        # regardless, bring from future prices to today's dollars

        down, up = current_node[1, :]
        
        # this is the price if we kept the option
        keep = np.exp(-self.r * self.dT) * (
            proportion * up + (1 - proportion) * down
        )

        # this is the price for which we'd be able to sell the option
        # at the current_time
        Stnow = current_asset_node[0, 0]
        sell = self.option_price(spot = Stnow, strike = self.K)

        current_node[0, 0] = max(keep, sell)
    
        return current_node

    def __str__(self):
        return ' (american style)' + super().__str__()


## from now on, all classes are concrete classe (instantiable classes)
# stock options
class EuropeanCallStockOption(Stock, EuropeanOption, Call):
    def __str__(self):
        s = f'Call Stock Option' + super().__str__()
        return s

class EuropeanPutStockOption(Stock, EuropeanOption, Put):
    def __str__(self):
        s = f'Put Stock Option' + super().__str__()
        return s

class AmericanCallStockOption(Stock, AmericanOption, Call):
    def __str__(self):
        s = f'Call Stock Option' + super().__str__()
        return s


class AmericanPutStockOption(Stock, AmericanOption, Put):
    def __str__(self):
        s = f'Put Stock Option' + super().__str__()
        return s


# currency options
class EuropeanCallCurrencyOption(Currency, EuropeanOption, Call):
    def __str__(self):
        s = f'Call Currency Option' + super().__str__()
        return s


class EuropeanPutCurrencyOption(Currency, EuropeanOption, Put):
    def __str__(self):
        s = f'Put Currency Option' + super().__str__()
        return s


class AmericanCallCurrencyOption(Currency, AmericanOption, Call):
    def __str__(self):
        s = f'Call Currency Option' + super().__str__()
        return s


class AmericanPutCurrencyOption(Currency, AmericanOption, Put):
    def __str__(self):
        s = f'Call Currency Option' + super().__str__()
        return s


BUILDINGBLOCKS = { 
    dermodel for dermodel in locals().values() 
    if (
        isinstance(dermodel, type) and                      # object is a class
        ABC in getattr(dermodel, '__bases__', set())        # class does not inherit directly from ABC
   )
}

MODELS = { 
    dermodel for dermodel in locals().values() 
    if (
        isinstance(dermodel, type) and                         # object is a class
        not getattr(dermodel, '__abstractmethods__', [1]) and  # set of abstract methods is empty
        ABC not in getattr(dermodel, '__bases__', set()) and   # class does not inherit directly from ABC
        dermodel != ABC                                        # class isn't ABC
   )
}