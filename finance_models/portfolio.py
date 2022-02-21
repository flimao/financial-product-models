#!/usr/bin/env python3
#-*- coding: utf-8 -*-

import pandas as pd

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
