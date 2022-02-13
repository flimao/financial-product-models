import numpy as np
from finance_models import br_sovereign_debt_securities as brdebt, tools
import unittest
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
        

class TestPrefixado(unittest.TestCase):
    
    def test_prazo_du(self):
        ntnf = brdebt.Prefixado(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022', 
            taxa_cupom = True,
            convencao = 'DU/252'
        )

        prazo = ntnf.calcula_prazo() * 252
        prazo_esperado = 2230
        self.assertEqual(
            prazo, prazo_esperado, 
            f"Prazo anualizado (DU/252) errado. Esperava '{prazo_esperado:.3f}', retornou '{prazo}'"
        )

        prazo2 = ntnf.calcula_prazo(
            dt_inicio = '15/02/2022', 
            dt_fim = '01/01/2031', 
            feriados = tools.get_holidays_anbima(), 
            convencao = 'DU/252'
        ) * 252
        prazo_esperado2 = 2229.
        self.assertEqual(
            prazo2, prazo_esperado2, 
            f"Prazo anualizado (DU/252) errado. Esperava '{prazo_esperado2:.3f}', retornou '{prazo2}'"
        )
    
    def test_prazo_dc(self):
        ntnf = brdebt.Prefixado(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022',
            taxa_cupom = True,
            convencao = 'DC/360'
        )

        prazo = ntnf.calcula_prazo() * 360
        prazo_esperado = 3243.
        self.assertEqual(
            prazo, prazo_esperado, 
            f"Prazo (DC/360) errado. Esperava '{prazo_esperado:n}' dias, retornou '{prazo:n}' dias"
        )
    
    def test_pu_ltn(self):
        ltn26 = brdebt.Prefixado(
            vencimento = 2026, 
            taxa_anual = 11.36/100, 
            dt_compra = '14/02/2022', 
            taxa_cupom = False,
        )

        pu1 = tools.Money(ltn26.calcula_pu())
        pu1_esperado = tools.Money(658.91)  # checado tesouro direto em 2022-02-12
        self.assertTrue(
            np.isclose(pu1, pu1_esperado, atol = 0.01), 
            f"PU errado. Esperava '{pu1_esperado}', retornou '{pu1}'"
        )
    
    def test_pu_ntnf(self):    

        ntnf31 = brdebt.Prefixado(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022',
            taxa_cupom = True,
            convencao = 'DU/252'
        )

        pu, _ = ntnf31.calcula_pu_ntnf(dt_base = ntnf31.dt_compra, tir = 0)
        pu = tools.Money(pu)
        pu_esperado = tools.Money(932.85)
        self.assertTrue(
            np.isclose(pu, pu_esperado, atol = 0.01), 
            f"PU de NTN-F errado. Esperava '{pu_esperado}', retornou '{pu}'"
        )
