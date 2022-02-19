import numpy as np
from .. import br_sovereign_debt_securities as brdebt, tools
import unittest

import warnings
warnings.filterwarnings('ignore')

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
            f"Prazo anualizado (DU/252) de {ntnf} errado. Esperava '{prazo_esperado:.3f}', retornou '{prazo}'"
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
            f"Prazo (DC/360) de {ntnf} errado. Esperava '{prazo_esperado:n}' dias, retornou '{prazo:n}' dias"
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
            f"PU de {ltn26} errado. Em {ltn26.dt_compra:%d/%m/%Y}, esperava '{pu1_esperado}', retornou '{pu1}'"
        )
    
    def test_pu_ntnf(self):    

        ntnf31 = brdebt.Prefixado(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022',
            taxa_cupom = True,
            convencao = 'DU/252'
        )

        pu, _ = ntnf31.calcula_pu_ntnf()
        pu = tools.Money(pu)
        pu_esperado = tools.Money(932.85)
        self.assertTrue(
            np.isclose(pu, pu_esperado, atol = 0.01), 
            f"PU de {ntnf31} errado. Em {ntnf31.dt_compra:%d/%m/%Y}, esperava '{pu_esperado}', retornou '{pu}'"
        )

    def test_taxa_anual_ltn(self):
        ltn26 = brdebt.Prefixado(
            vencimento = 2026, 
            taxa_anual = 11.36/100, 
            dt_compra = '14/02/2022', 
            taxa_cupom = False,
        )
        
        pu = tools.Money(658.91)
        taxa = ltn26.calcula_taxa_anual(pu = pu, valor_base = 1000)
        taxa_esperada = 0.1136
        self.assertAlmostEqual(
            taxa, taxa_esperada, 4, 
            f"Taxa de {ltn26} errado. Com PU = {pu}, a taxa deveria ser '{taxa_esperada:.2%}' a.a., mas o cálculo deu '{taxa:.2%}' a.a."
        )
    
    def test_constroi_fluxo(self):        
        ntnf31 = brdebt.Prefixado(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022',
            taxa_cupom = True,
            convencao = 'DU/252'
        )
        lista_fluxo = ntnf31.constroi_fluxo()
        n_fluxos = len(lista_fluxo)
        n_esperados = 1 + (2030 - 2023 +1) * 2 + 1 # um em julho de 2022 + 2 por ano de 2023 a 2030 + final no vencimento em janeiro de 2031
        self.assertEqual(
            n_fluxos, n_esperados, 
            f"Número de eventos de pagamento de uma {ntnf31} errado. Esperava '{n_esperados:n}' eventos, retornou '{n_fluxos:n}' eventos"
        )

