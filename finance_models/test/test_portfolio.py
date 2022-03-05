import datetime as dt
import numpy as np
import pandas as pd
from .. import portfolio, tools
import unittest

import warnings
warnings.filterwarnings('ignore')

class TestPortfolio(unittest.TestCase):
    def setUp(self):
        self.date_idx = pd.date_range(
            start = dt.date(2022, 1, 1),
            end = dt.date(2022, 1, 7),
            freq = 'D'
        )

        self.sec_names = [ 'S1', 'S2', 'S3' ]
        
        self.secs_values = pd.DataFrame(
            [
                [11.1349419, 12.45459113, 11.65418345],
                [9.300009683, 11.88696042, 12.5906423],
                [11.65175549, 7.504452931, 13.04502693],
                [9.275835792, 8.429503342, np.nan],
                [12.31792534, 11.90068811, 13.34205007],
                [11.03412628, 11.80362515, 14.05605982],
                [10.81213237, 12.10794911, 14.17710639],
            ],
            columns = self.sec_names,
            index = self.date_idx
        )

    def test_portfolio_notionals_int(self):
        pf = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = 1000
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(32925.65)          # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )
    
    def test_portfolio_notionals_series(self):
        notionals = pd.Series(
            [1500, 2000, 500],
            index = self.sec_names,
        )
        
        pf = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = notionals
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(43556.88)           # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )
    
    def test_portfolio_notionals_df(self):
        notionals = pd.DataFrame(
            [[1500, 2000, 500], [2000, 1500, 600]],
            columns = self.sec_names,
            index = self.date_idx[[0, 2]],
        )
        
        pf = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = notionals
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(44576.14)          # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )

    def test_portfolio_notionals_dropna(self):
        notionals = 1000
        secs_values = self.secs_values.copy()
        secs_values.loc['2022-01-04'] = np.nan
        
        pf = portfolio.Portfolio(
            securities_values = secs_values,
            notionals = notionals,
            na = 'drop',
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(35462.37)          # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )

    def test_portfolio_notionals_ffillna(self):
        notionals = 1000
        
        pf = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = notionals,
            na = 'ffill',
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(34789.23)          # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )
    
    def test_portfolio_notionals_bfillna(self):
        notionals = 1000
        
        pf = portfolio.Portfolio(
            securities_values = self.secs_values,
            notionals = notionals,
            na = 'bfill',
        )

        pf_mean = tools.Money(pf.portfolio_total.mean())
        pf_mean_expected = tools.Money(34831.66)          # calculations in Excel

        self.assertAlmostEqual(
            pf_mean, pf_mean_expected, places = None, delta = 0.01,
            msg = f"Wrong average portfolio total. Expected {pf_mean_expected}, got {pf_mean}"
        )
