import numpy as np
from .. import fixed_income, tools
import unittest

import warnings
warnings.filterwarnings('ignore')

M = tools.Money

class TestFixedIncome(unittest.TestCase):
    
    def test_calc_pv(self):
        pv = fixed_income.calc_pv(fv = M(1000), time = 0.5, rate = 10/100)

        pv_expected = M(953.46)

        self.assertAlmostEqual(
            pv, pv_expected, delta = 0.01,
            msg = f'{__class__.__name__}: VP is wrong. Expected {pv_expected}, got {pv}.'
        )
    
    def test_calc_rate(self):
        rate = fixed_income.calc_rate(fv = M(1000), pv = M(953.46), time = 0.5)

        rate_expected = 10/100

        self.assertAlmostEqual(
            rate, rate_expected, delta = 1e-5,
            msg = f'{__class__.__name__}: Rate is wrong. Expected {rate_expected:.3%}, got {rate:.3%}.'
        )
    
    