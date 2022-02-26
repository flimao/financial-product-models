from .. import tools
import unittest

import warnings
warnings.filterwarnings('ignore')

class TestTools(unittest.TestCase):
    def setUp(self):
        self.holidays = tools.get_holidays_anbima()

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
