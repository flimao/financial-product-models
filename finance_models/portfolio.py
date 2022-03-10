#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import numpy as np
import pandas as pd
from matplotlib import pyplot as plt

class Portfolio:
    """ define Portfolio class. ingest and massage portfolio prices and notionals"""
    def __init__(self, 
        securities_values: pd.DataFrame or pd.Series = None, 
        notionals: pd.DataFrame or pd.Series or None = None,
        na: str or None = 'drop',
        individual: bool = False,
        holding_period: int = 1,
        *args, **kwargs
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
            na (bool): drop the NaN values from the portfolio values or not
        """
        # if portfolio is passed directly, transfer their properties to this one
        portfolio = kwargs.get('portfolio', None)

        if portfolio is not None and isinstance(portfolio, Portfolio):
            # set a list of properties to transfer to self
            attr_list = [ 
                'securities_values', 
                'notionals', 
                'portfolio_values', 
                'portfolio_total',
                'holding_period',
                'individual',
            ]
            for attr in attr_list:
                setattr(self, attr, getattr(portfolio, attr))

            return  # nothing else to do
        
        # holding period
        self.holding_period = holding_period

        # whether we get returns on the consolidated portfolio or for each indvidual asset
        self.individual = individual

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


    
    def get_returns(self, holding_period = 1, log = False, individual = False):
        if not individual:
            prices = self.portfolio_total
        else:
            prices = self.securities_values

        ret = prices / prices.shift(holding_period)

        if log:
            return np.log(ret)
        else:
            return ret - 1
    
    @property
    def returns(self):
        rets = self.get_returns(holding_period = 1, log = False, individual = self.individual)
        rets.name = 'returns'
        return rets

    @property
    def logreturns(self):
        logrets = self.get_returns(holding_period = 1, log = True, individual = self.individual)
        logrets.name = 'log_returns'
        return logrets


# why is the import statement here, rather than at the top?
# the volatility module imports this module to get a hold of the Portfolio class
# if this import statement were at the top, it would cause a circular import issue.
# we needed to define the Portfolio class before importing the Volatility class
from .volatility import Volatility


class Optimization:
    """ implements optimization from an efficient frontier standpoint """
    
    def __init__(self, 
        nsims: int = 10_000,
        *args, 
        **kwargs
    ):
        kwargs['individual'] = True
        
        # TODO: implement diferent volatility models for optimization
        kwargs['volmodel'] = 'hist'
        kwargs['window'] = None
        
        self.volmodel = Volatility(*args, **kwargs)

        self.nsims = nsims

        self.individual_logreturns = self.volmodel.logreturns
        self._cov_matrix = self.individual_logreturns.cov()
        self._means = self.individual_logreturns.mean()

        vol = self.volmodel.vol_pp
        if isinstance(vol, pd.Series):
            self._risks = vol
        
        else:
            self._risks = vol.iloc[-1]

        if self.nsims > 0:
            self._risk_return, self._Ws = self.simulate_weights()

    def simulate_weights(self):
        secs = self.volmodel.securities_values.columns
        n_secs = len(secs)

        pesos = np.random.dirichlet(np.ones(n_secs), size = self.nsims)

        Ws = pd.DataFrame(pesos,
            columns = secs
        )

        muP = Ws @ self._means

        riskP = pd.Series(
            np.sqrt((Ws @ self._cov_matrix @ Ws.transpose()).values.diagonal()),
            index = Ws.index
        )

        risk_return = pd.concat([muP, riskP], axis = 1)
        risk_return.columns = ['return', 'risk']

        return risk_return, Ws
    
    def _return_results(self, result, weights, param, return_weights, return_param):
        ret = result

        if return_weights or return_param:
            ret = (ret, )

            if return_weights:
                ret += (weights, )

            if return_param:
                ret += (param, )
            
        
        return ret
    
    def maximize_returns(self, max_risk, return_weights = False, return_max_risk = False):
        
        applicable_returns = self._risk_return[self._risk_return['risk'] <= max_risk]
        idxes = applicable_returns.index

        try:
            idxoptimum = applicable_returns['return'].argmax()
        except ValueError:  # risk is too low
            return self._return_results(
                result = None, 
                weights = None, 
                param = None, 
                return_weights = return_weights,
                return_param = return_max_risk
            )
        
        max_ret, min_risk_at_max_ret = applicable_returns.iloc[idxoptimum]
        w = self._Ws.loc[idxes].iloc[idxoptimum]
        
        return self._return_results(
            result = max_ret,
            weights = w,
            param = min_risk_at_max_ret,
            return_weights = return_weights,
            return_param = return_max_risk,
        )

    def minimize_risk(self, min_return, return_weights = False, return_min_return = False):
        
        applicable_risk = self._risk_return[self._risk_return['return'] >= min_return]
        idxes = applicable_risk.index

        try:
            idxoptimum = applicable_risk['risk'].argmin()
        except ValueError:  # risk is too low        
            return self._return_results(
                result = None,
                weights = None,
                param = None,
                return_weights = return_weights,
                return_param = return_min_return,
            )
        
        max_return_at_min_risk, min_risk = applicable_risk.iloc[idxoptimum]
        w = self._Ws.loc[idxes].iloc[idxoptimum]
        
        return self._return_results(
            result = min_risk,
            weights = w,
            param = max_return_at_min_risk,
            return_weights = return_weights,
            return_param = return_min_return,
        )

    def plot_risk_return(self, 
        plot_min_risk = False, 
        plot_weights = False, 
        opt_max_risk = None, 
        opt_min_return = None, 
        fmt = '.2%'
    ):
        fig, ax = plt.subplots()

        # mark 0 return
        ax.axhline(0, ls = '--', color = 'gray', alpha = 0.4)

        # plot the simulated data
        ax.plot(
            self._risk_return['risk'], self._risk_return['return'], 
            'o', color = 'blue', alpha = 0.2, label = 'Simulated portfolios', zorder = 1.1,
        )
        
        # plot the original securities returns
        ax.plot(
            self._risks, self._means, 
            'o', color = 'orange', label = 'Original securities'
        )

        # annotate the original securities
        for ativo, s, m in zip(
            self.volmodel.securities_values.columns, 
            self._risks,
            self._means, 
        ):
            ax.annotate(ativo, (s, m))

        # graph configuration
        ax.set_xlabel(r'Risk/volatility (% p.p.)')
        ax.xaxis.set_major_formatter(lambda x, pos: f'{x:{fmt}}')
        ax.set_ylabel(r'Returns (% p.p.)')
        ax.yaxis.set_major_formatter(lambda y, pos: f'{y:{fmt}}')
        ax.set_title(r'Risk vs Return')

        # minimal risk point if option
        if plot_min_risk:
            ax = self._plot_least_risk(ax = ax, plot_weights = plot_weights, fmt = fmt)
        
        # plot possible risk minimization/return maximization
        if opt_max_risk is not None:
            ax = self._plot_max_return(ax = ax, max_risk = opt_max_risk, plot_weights = plot_weights, fmt = fmt)
        
        if opt_min_return is not None:
            ax = self._plot_min_risk(ax = ax, min_return = opt_min_return, plot_weights = plot_weights, fmt = fmt)

        plt.legend()

        return fig

    def _plot_least_risk(self, ax, plot_weights, fmt):
        # identify the minimal risk point
        idx_min_risk = self._risk_return['risk'].argmin()

        # get the values
        pt_min_return_at_min_risk, pt_min_risk = self._risk_return.iloc[idx_min_risk]

        # start the label
        min_risk_label = (
            fr'Minimal risk = {pt_min_risk:{fmt}}'
            '\n'
            fr'Min return @ min risk = {pt_min_return_at_min_risk:{fmt}}'
        )
        
        # add the weights to the label if option
        if plot_weights:
            
            # get the weights
            ws_at_min_risk = self._Ws.iloc[idx_min_risk]
            min_risk_label += '\nWeights:'
            
            # get the maximum number of characters in the securities' names
            nfield = pd.Series(ws_at_min_risk.index).apply(len).max() + 4
            for asset, weight in ws_at_min_risk.iteritems():
                # add to the label
                min_risk_label += '\n' + f"{asset:>{nfield}}: {weight:{fmt}}"
        
        # plot the minimal risk point
        ax.plot(
            pt_min_risk, pt_min_return_at_min_risk, 
            'o', color = 'red', 
            label = min_risk_label,
        )

        return ax

    def _plot_max_return(self, ax, max_risk, plot_weights, fmt):
        
        max_ret, w, risk = self.maximize_returns(max_risk = max_risk, return_weights=True, return_max_risk=True)
        
        point_max_risk = max_risk
        point_risk = risk
        point_return = max_ret

        if point_return is not None:  # max_risk is not so low as to exclude all simulated portfolios
            label = f'Return @ max risk {point_max_risk:{fmt}} = {point_return:{fmt}}'

            if plot_weights:
                label += '\nWeights:'
                # get the maximum number of characters in the securities' names
                nfield = pd.Series(w.index).apply(len).max() + 4
                for asset, weight in w.iteritems():
                    # add to the label
                    label += '\n' + f"{asset:>{nfield}}: {weight:{fmt}}"
            
            ax.plot(point_risk, point_return, 'o', color = 'lightgreen', label = label)
        
        # plot boundary limitation
        ax.axvline(point_max_risk, ls = '--', color = 'lightgreen')
        
        y_lims = ax.get_ylim()
        x_lim_max = ax.get_xlim()[1]

        # annotate the horizontal line for the maximum risk optimization
        ax.annotate(f'Risk <= {max_risk:{fmt}} p.p.', (point_max_risk*1.04, y_lims[0]*1.04), 
            ha = 'left', va = 'bottom',
            color = 'green',
        )

        # blur simulated whose risks are larger than max_risk
        ax.fill_betweenx(
            y = y_lims, 
            x1 = point_max_risk, 
            x2 = x_lim_max,
            color = 'white',
            alpha = 0.8, zorder = 1.5,
        )

        return ax
    
    def _plot_min_risk(self, ax, min_return, plot_weights, fmt):
        
        min_risk, w, ret = self.minimize_risk(min_return = min_return, return_weights = True, return_min_return = True)
    
        point_risk = min_risk
        point_return = ret
        point_min_return = min_return

        if point_risk is not None:
            label = f'Risk @ min return {point_return:{fmt}} = {point_risk:{fmt}}'

            if plot_weights:
                label += '\nWeights:'
                # get the maximum number of characters in the securities' names
                nfield = pd.Series(w.index).apply(len).max() + 4
                for asset, weight in w.iteritems():
                    # add to the label
                    label += '\n' + f"{asset:>{nfield}}: {weight:{fmt}}"
            
            ax.plot(point_risk, point_return, 'o', color = 'lightgreen', label = label)

        # plot boundary limitation
        ax.axhline(point_min_return, ls = '--', color = 'lightgreen')
        
        x_lims = ax.get_xlim()
        y_lim_min = ax.get_ylim()[0]

        # annotate the horizontal line for the minimum return optimization
        ax.annotate(f'Return >= {min_return:{fmt}} p.p.', (x_lims[1], point_min_return*0.96), 
            ha = 'right', va = 'top',
            color = 'green',
        )

        # blur simulated whose returns are lower than min_return
        ax.fill_between(
            x = x_lims, 
            y1 = point_min_return, 
            y2 = y_lim_min,
            color = 'white',
            alpha = 0.8, zorder = 1.5,
        )

        return ax
