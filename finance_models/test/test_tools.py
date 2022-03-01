import datetime as dt
import numpy as np
import pandas as pd
from .. import tools
import unittest

import warnings
warnings.filterwarnings('ignore')

class TestTools(unittest.TestCase):
    def setUp(self):
        self.holidays = tools.get_holidays_anbima()
        self.ipca_1y = tools.get_bcb_ts(433, dt_inicio = '15/07/2000', dt_fim = '15/07/2001')
        self.ipca_1y.iloc[2] = np.nan
        self.ipca_1y.iloc[5] = np.nan
        self.ipca_1y.iloc[-1] = np.nan

    def test_holidays(self):
        holidays = self.holidays
        holidays_22Q1 = holidays[(holidays >= '2022-01') & (holidays < '2022-04')]
        nholidays_22Q1 = holidays_22Q1.shape[0]
        self.assertEqual(
            nholidays_22Q1, 3, 
            f"Wrong number of holidays for 22Q1 (expected '3', found '{nholidays_22Q1}')"
        )

    def test_days_du(self):
        dus = tools.get_days(
            date_begin = '01/01/2022', 
            date_end = '01/04/2022', 
            holidays = self.holidays,
            closed = 'left',
            convention = 'DU/252'
        )
        ndus = dus.shape[0]

        ndus_expected = 62
        self.assertEqual(
            ndus, ndus_expected, 
            f"Wrong number of business days for 22Q1 (expected '{ndus_expected}', found '{ndus}')"
        )

    def test_days_dc(self):
        dcs = tools.get_days(
            date_begin = '01/01/2022', 
            date_end = '01/04/2022', 
            holidays = self.holidays,
            closed = 'left',
            convention = 'DC/360'
        )
        ndcs = dcs.shape[0]

        ndcs_expected = 90
        self.assertEqual(
            ndcs, ndcs_expected, 
            f"Wrong number of running days for 22Q1 (expected '{ndcs_expected}', found '{ndcs}')"
        )

    def test_annualized_time_du(self):
        ndus_atime = tools.get_annualized_time(
            date_begin = '01/01/2022', 
            date_end = '01/04/2022', 
            holidays = self.holidays,
            convention = 'DU/252'
        )

        ndus_atime_expected = 62/252
        self.assertAlmostEqual(
            ndus_atime, ndus_atime_expected, places = 4, 
            msg = f"Wrong annualized number of business days for 22Q1 (expected '{ndus_atime_expected:4f}', found '{ndus_atime:4f}')"
        )

    def test_annualized_time_dc(self):
        ndcs_atime = tools.get_annualized_time(
            date_begin = '01/01/2022', 
            date_end = '01/04/2022', 
            holidays = self.holidays,
            convention = 'DC/360'
        )

        ndcs_atime_expected = 90/360
        self.assertAlmostEqual(
            ndcs_atime, ndcs_atime_expected, places = 4,
            msg = f"Wrong number of running days for 22Q1 (expected '{ndcs_atime_expected:.4f}', found '{ndcs_atime:.4f}')"
        )
    
    def test_get_bcb_ts(self):
        f = tools.get_bcb_ts

        # ipca em janeiro de 2020
        ipca_s = tools.get_bcb_ts(433, dt_inicio = '01/01/2020', dt_fim = '31/01/2020')
        
        ipca_em = ipca_s.index[0]
        ipca = ipca_s.iloc[0]
        ipca_expected = 0.21

        self.assertAlmostEqual(
            ipca, ipca_expected, delta = 0.01,
            msg = f"{f.__name__}: IPCA at {ipca_em:%d/%m/%Y}, expected value {ipca_expected/100:.2%} a.m., got {ipca/100:.2%} a.m."
        )

    def test_fix_timeseries_ends_do_nothing(self):
        f = tools.fix_timeseries_ends
        ts = tools.fix_timeseries_ends(
            ts_orig = self.ipca_1y,
            date_begin = '15/07/2000',
            date_end = '15/07/2001'
        )

        ts0 = ts.iloc[0]
        ts0_expected = self.ipca_1y.iloc[0]

        tsend = ts.iloc[-1]
        tsend_expected = self.ipca_1y.iloc[-1]

        self.assertEqual(
            ts0, ts0_expected,
            msg = f"{f.__name__}: wrong fix: at beginning of fixed timeseries, expected value {ts0_expected:.2f}%, got {ts0:.2f}%"
        )

        self.assertTrue(
            np.isnan(tsend) & np.isnan(tsend_expected),
            msg = f"{f.__name__}: wrong fix: at end of fixed timeseries, expected value {tsend_expected:.2f}%, got {tsend:.2f}%"
        )
    
    def test_fix_timeseries_ends_begin_extrap(self):
        f = tools.fix_timeseries_ends
        ts = tools.fix_timeseries_ends(
            ts_orig = self.ipca_1y,
            date_begin = '14/07/2000',
            date_end = '15/07/2001'
        )

        ts0 = ts.iloc[0]
        ts0_expected = 0

        self.assertEqual(
            ts0, ts0_expected,
            msg = f"{f.__name__}: wrong fix: at beginning of fixed timeseries, expected value {ts0_expected:.2f}%, got {ts0:.2f}%"
        )
    
    def test_fix_timeseries_ends_begin_interp(self):
        f = tools.fix_timeseries_ends
        ts = tools.fix_timeseries_ends(
            ts_orig = self.ipca_1y,
            date_begin = '16/07/2000',
            date_end = '15/07/2001'
        )

        ts0 = ts.iloc[0]
        ts0_expected = 1.557662

        self.assertAlmostEqual(
            ts0, ts0_expected, places = 6,
            msg = f"{f.__name__}: wrong fix: at beginning of fixed timeseries, expected value {ts0_expected:.2f}%, got {ts0:.2f}%"
        )

    def test_fix_timeseries_ends_end_extrap(self):
        f = tools.fix_timeseries_ends
        ts = tools.fix_timeseries_ends(
            ts_orig = self.ipca_1y,
            date_begin = '15/07/2000',
            date_end = '16/07/2001'
        )

        tsend = ts.iloc[-1]
        tsend_expected = 0

        self.assertAlmostEqual(
            tsend, tsend_expected, places = 6,
            msg = f"{f.__name__}: wrong fix: at end of fixed timeseries, expected value {tsend_expected:.2f}%, got {tsend:.2f}%"
        )
    
    def test_fix_timeseries_ends_end_interp(self):
        f = tools.fix_timeseries_ends
        ts = tools.fix_timeseries_ends(
            ts_orig = self.ipca_1y,
            date_begin = '15/07/2000',
            date_end = '14/07/2001'
        )

        var_junho = ((1 + ts.iloc[-2:]/100).prod() - 1) * 100
        var_junho_expected = self.ipca_1y.iloc[-2]

        self.assertAlmostEqual(
            var_junho, var_junho_expected, places = 6,
            msg = f"{f.__name__}: wrong fix: IPCA expected variation in June-2001 {var_junho_expected:.2f}%, got {var_junho:.2f}%"
        )
