import numpy as np
import pandas as pd
from .. import br_sovereign_debt as brdebt, tools
import unittest

import warnings
warnings.filterwarnings('ignore')

M = tools.Money

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

class TestTesouroDireto(unittest.TestCase):
    def test_prazo_anualizado_du(self):
        titulo = brdebt.TesouroDireto(
            vencimento = 2031, 
            taxa_anual = 11.54/100, 
            dt_compra = '14/02/2022', 
            convencao = 'DU/252'
        )

        prazo_anual = titulo.calcula_prazo() * 252
        prazo_anual_esperado = 2230
        self.assertEqual(
            prazo_anual, prazo_anual_esperado, 
            f"Prazo anualizado (DU/252) de {titulo} errado. Esperava '{prazo_anual_esperado:.3f}' dias, retornou '{prazo_anual}' dias"
        )

        prazo2 = titulo.calcula_prazo(
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
    
    def test_pu(self):
        titulo = brdebt.TesouroDireto(
            vencimento = 2026, 
            taxa_anual = 11.36/100, 
            dt_compra = '14/02/2022', 
        )

        pu1 = titulo.calcula_pu(vf = tools.Money(1000))
        pu1_esperado = tools.Money(658.91)  # checado tesouro direto em 2022-02-12
        self.assertAlmostEqual(
            pu1, pu1_esperado, delta = tools.Money(0.01), 
            msg = f"PU de {titulo} errado. Em {titulo.dt_compra:%d/%m/%Y}, esperava '{pu1_esperado}', retornou '{pu1}'"
        )
    
    def test_taxa_anual(self):
        titulo = brdebt.TesouroDireto(
            vencimento = 2026, 
            taxa_anual = 11.36/100, 
            dt_compra = '14/02/2022', 
        )
        
        pu = tools.Money(658.91)
        valor_base = tools.Money(1000)
        taxa = titulo.calcula_taxa_anual(pu = pu, valor_base = valor_base)
        taxa_esperada = 0.1136
        self.assertAlmostEqual(
            taxa, taxa_esperada, delta = 1e-4, 
            msg = f"Taxa de {titulo} errado. Com VP = {pu} e VF = {valor_base}, a taxa deveria ser '{taxa_esperada:.2%}' a.a., mas o cálculo deu '{taxa:.2%}' a.a."
        )
    
    def test_constroi_fluxo(self):

        titulo = brdebt.TesouroDireto(
            vencimento = 2026, 
            taxa_anual = 11.36/100, 
            dt_compra = '14/02/2022', 
        )

        f = titulo.constroi_fluxo

        freq = 6
        lista_fluxo = titulo.constroi_fluxo(frequencia = freq)

        nfluxos = len(lista_fluxo)
        nfluxos_expected = 8

        self.assertEqual(
            nfluxos, nfluxos_expected,
            msg = f'{f.__name__}: número de fluxos para {titulo} errado. Esperava {nfluxos_expected}, deu {nfluxos}.'
        )

        primeira_data = lista_fluxo[0]
        primeira_data_expected = pd.Timestamp('2022-07-01')

        self.assertEqual(
            primeira_data, primeira_data_expected,
            msg = f'{f.__name__}: primeira data do fluxo de {titulo} errada. Esperava {primeira_data_expected:{tools.DT_FMT}}, deu {primeira_data:{tools.DT_FMT}}'
        )

        ultima_data = lista_fluxo[-1]
        ultima_data_expected = pd.Timestamp(titulo.vencimento)

        self.assertEqual(
            ultima_data, ultima_data_expected,
            msg = f'{f.__name__}: última data do fluxo de {titulo} errada. Esperava {ultima_data_expected:{tools.DT_FMT}}, deu {ultima_data:{tools.DT_FMT}}'
        )

        delta_t = lista_fluxo[1] - lista_fluxo[0]

        self.assertTrue(
            pd.Timedelta('30 days') * 6 <= delta_t <= pd.Timedelta('31 days') * 6,
            msg = f'{f.__name__}: intervalo entre dois fluxos ({delta_t}) incompatível com {freq} meses.'
        )

class TestIndexado(unittest.TestCase):

    def calc_delta(self, f_series, delta1 = 1e-4, sqrt = False):
        F = np.exp(np.log(f_series).sum())
        if sqrt:
            sum_delta_over_fi = np.sqrt(((delta1 / f_series)**2).sum())
        else:
            sum_delta_over_fi = (delta1 / f_series).sum()
        
        deltaF = F * sum_delta_over_fi

        return deltaF

    def setUp(self):
        self.ntnb = brdebt.Indexado(
            vencimento = 2032,
            indice = brdebt.IPCA,
            taxa_anual = 5.72/100,
            taxa_cupom = True,
            dt_compra = '15/02/2022'
        )

        self.ntnb_short = brdebt.Indexado(
            vencimento = 2023,
            indice = brdebt.IPCA,
            taxa_anual = 0.061,
            taxa_cupom = True,
        )

        self.ntnb_long = brdebt.Indexado(
            vencimento = 2040,
            indice = brdebt.IPCA,
            taxa_anual = 5.62/100,
            taxa_cupom = True,
            dt_compra = '15/02/2022',
        )

    def test_conserta_indice_class(self):
        f = brdebt.Indexado.conserta_indice
        
        ipca = self.ntnb.conserta_indice()
        ipca0_em = ipca.index[0]
        ipca0 = ipca.iloc[0]
        ipca0_expected = 1.61

        self.assertAlmostEqual(
            ipca0, ipca0_expected, places = 1,
            msg = f"{f.__name__}: no início ({ipca0_em:%d/%m/%Y}) do {self.ntnb}, esperava-se IPCA = {ipca0_expected/100:.2%} a.m., mas retornou {ipca0/100:.2%} a.m."
        )
    
    def test_calcula_vna_class(self):
        f = self.ntnb.calcula_vna

        vna = M(f())
        vna_expected = M(3810.86) # verificado na série baixada do site do Tesouro Direto (https://www.tesourotransparente.gov.br/publicacoes/valor-nominal-de-ntn-b/)

        delta = self.calc_delta(f_series = 1 + self.ntnb.indice/100)

        self.assertAlmostEqual(
            vna, vna_expected, delta = M(delta),
            msg = f"{f.__name__}: VNA de {self.ntnb} incorreto. Em {self.ntnb.dt_compra:{tools.DT_FMT}}, esperava-se VNA = {vna_expected}, obteve-se {vna}."
        )
    
    def test_calcula_vna_fun_indice_num(self):
        f = self.ntnb.calcula_vna

        vna = M(f(indice = 433))
        vna_expected = M(3810.86) # verificado na série baixada do site do Tesouro Direto (https://www.tesourotransparente.gov.br/publicacoes/valor-nominal-de-ntn-b/)

        delta = self.calc_delta(f_series = 1 + self.ntnb.indice/100)

        self.assertAlmostEqual(
            vna, vna_expected, delta = M(delta),
            msg = f"{f.__name__}: VNA de {self.ntnb} incorreto. Em {self.ntnb.dt_compra:{tools.DT_FMT}}, esperava-se VNA = {vna_expected}, obteve-se {vna}."
        )
    
    def test_calcula_vna_fun_indice_dt_fim(self):
        f = self.ntnb.calcula_vna
        
        dt_fim = '15/01/2022'
        vna = M(f(dt_fim = dt_fim))
        vna_expected = M(3790.39)  # verificado na série baixada do site do Tesouro Direto (https://www.tesourotransparente.gov.br/publicacoes/valor-nominal-de-ntn-b/)

        delta = self.calc_delta(f_series = 1 + self.ntnb.indice[:-1]/100)

        self.assertAlmostEqual(
            vna, vna_expected, delta = M(delta),
            msg = f"{f.__name__}: VNA de {self.ntnb} incorreto. Em {dt_fim}, esperava-se VNA = {vna_expected}, obteve-se {vna}."
        )
    
    def test_calcula_cotacao_df(self):
        f = self.ntnb_short.calcula_cotacao_df
        dt_base = '15/08/2022'

        cashflow = self.ntnb_short.calcula_cotacao_df(dt_base = dt_base)
        
        cotacao = cashflow['cotacao'].sum()
        cotacao_expected = 1.014665

        self.assertAlmostEqual(
            cotacao, cotacao_expected, places = 6,
            msg = f'{f.__name__}: cálculo errado da cotação do título {self.ntnb_short}. Na data base {dt_base}, esperava-se cotação de {cotacao_expected:.3%}, obteve-se {cotacao:.3%}'
        )

        dt_base = '15/02/2022'

        cashflow = self.ntnb_long.calcula_cotacao_df(dt_base = dt_base)

        cotacao = cashflow['cotacao'].sum()
        cotacao_expected = 3928.96 / 3810.859521

        delta = self.calc_delta(f_series = 1 + self.ntnb_long.indice/100)

        self.assertAlmostEqual(
            cotacao, cotacao_expected, delta = delta,
            msg = f'{f.__name__}: cálculo errado da cotação do título {self.ntnb_long}. Na data base {dt_base}, esperava-se cotação de {cotacao_expected:.3%}, obteve-se {cotacao:.3%}'
        )

    def test_calcula_pu(self):
        f = self.ntnb_short.calcula_pu_indexado

        dt_base_venda = '15/02/2022'
        pu = M(self.ntnb_long.calcula_pu_indexado(
            dt_base = dt_base_venda,
            taxa_anual = 5.74/100
        ))
        
        pu_expected = M(3928.96)

        nfluxos = len(self.ntnb_long.constroi_fluxo(dt_base = dt_base_venda))

        delta = self.calc_delta(f_series = 1 + self.ntnb_long.indice/100)

        self.assertAlmostEqual(
            pu, pu_expected, delta = np.sqrt(nfluxos)*delta,
            msg = f'{f.__name__}: PU errado do título {self.ntnb_short}. Na data base {dt_base_venda}, esperava-se PU de {pu_expected}, obteve-se {pu}'
        )

    