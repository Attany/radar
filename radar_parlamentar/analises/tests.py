# coding=utf8

# Copyright (C) 2012, Leonardo Leite
#
# This file is part of Radar Parlamentar.
# 
# Radar Parlamentar is free software: you can redistribute it and/or modify
# it under the terms of the GNU Affero General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Radar Parlamentar is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with Radar Parlamentar.  If not, see <http://www.gnu.org/licenses/>.

from __future__ import unicode_literals
from django.test import TestCase
from analises import analise
from analises import grafico
from analises import filtro
from grafico import GeradorGrafico
from importadores import convencao
from modelagem import models
import numpy

def mean(v):
    return 1.0 * sum(v) / len(v)
    
class AnaliseTest(TestCase):

    @classmethod
    def setUpClass(cls):
        cls.importer = convencao.ImportadorConvencao()
        cls.importer.importar()

    @classmethod
    def tearDownClass(cls):
        from util_test import flush_db
        flush_db(cls)

    def setUp(self):
        self.casa_legislativa = models.CasaLegislativa.objects.get(nome_curto='conv')
        self.partidos = AnaliseTest.importer.partidos
        self.votacoes = models.Votacao.objects.filter(proposicao__casa_legislativa__nome_curto='conv')

    def test_casa(self):
        """Testa se casa legislativa foi corretamente recuperada do banco"""

        self.assertAlmostEqual(self.casa_legislativa.nome, 'Convenção Nacional Francesa')
        
    def test_tamanho_partidos(self):
        builder = analise.TamanhoPartidoBuilder(self.partidos, self.casa_legislativa)
        tamanhos = builder.gera_dic_tamanho_partidos()
        tamanho_jacobinos = tamanhos[convencao.JACOBINOS]
        tamanho_girondinos = tamanhos[convencao.GIRONDINOS]
        tamanho_monarquistas = tamanhos[convencao.MONARQUISTAS]
        tamanho = convencao.PARLAMENTARES_POR_PARTIDO
        self.assertEqual(tamanho_jacobinos, tamanho)
        self.assertEqual(tamanho_girondinos, tamanho)
        self.assertEqual(tamanho_monarquistas, tamanho)
        soma = 3*tamanho
        self.assertEqual(builder.soma_dos_tamanhos_dos_partidos, soma)
        
    def test_matriz_votacao(self):
        vetor_girondinos =   [mean([1, 0, -1]), mean([-1, -1, -1]), mean([-1, -1, 1]), mean([1, 1, 1]), mean([1, 1, 0]), mean([1, 1, 1]), mean([1, 1, 0]), mean([-1, -1, -1])]
        vetor_jacobinos =    [mean([1, 1, 1]), mean([-1, -1, -1]), mean([-1, -1, -1]), mean([1, 0 -1]), mean([1, 1, 1]), mean([1, 1, 1]), mean([1, 1, 1]), mean([0, -1, -1])]
        vetor_monarquistas = [mean([-1, -1, -1]), mean([1, 1, 1]), mean([1, 1, 1]), mean([1, -1]), mean([-1, -1, -1]), mean([1, 1]), mean([1,  1]), mean([1, 1])]
        MATRIZ_VOTACAO_ESPERADA = numpy.matrix([vetor_girondinos, vetor_jacobinos, vetor_monarquistas])
        builder = analise.MatrizDeVotacoesBuilder(self.votacoes, self.partidos)
        matriz_votacao = builder.gera_matriz()
        self.assertTrue((matriz_votacao == MATRIZ_VOTACAO_ESPERADA).all()) 

    def test_partidos_2d(self):
        an = analise.AnalisadorPeriodo(self.casa_legislativa, partidos=self.partidos)
        grafico = an.partidos_2d()
        self.assertAlmostEqual(grafico[convencao.JACOBINOS][0], -0.49321534, 4)
        self.assertAlmostEqual(grafico[convencao.JACOBINOS][1], -0.65069601, 4)
        self.assertAlmostEqual(grafico[convencao.MONARQUISTAS][0], 0.81012694, 4)
        self.assertAlmostEqual(grafico[convencao.MONARQUISTAS][1], -0.10178901, 4)
        self.assertAlmostEqual(grafico[convencao.GIRONDINOS][0], -0.31691161, 4)
        self.assertAlmostEqual(grafico[convencao.GIRONDINOS][1], 0.75248502, 4)
        

class GraficoTest(TestCase):
    @classmethod
    def setUpClass(cls):
        cls.importer = convencao.ImportadorConvencao()
        cls.importer.importar()

    @classmethod
    def tearDownClass(cls):
        from util_test import flush_db
        flush_db(cls)

    def setUp(self):
        self.casa_legislativa = models.CasaLegislativa.objects.get(nome_curto='conv')
    
    def test_graph_scale(self):
        partidos = {}
        partidos['Jacobinos'] = [0.1, -0.2]
        partidos['Girondinos'] = [0.5, 1]
        scaler = grafico.GraphScaler()
        scaled = scaler.scale(partidos)
        self.assertEqual(55, scaled['Jacobinos'][0])
        self.assertEqual(40, scaled['Jacobinos'][1])
        self.assertEqual(75, scaled['Girondinos'][0])
        self.assertEqual(100, scaled['Girondinos'][1])
        
    def test_json(self):
        EXPECTED_JSON = {u'periodos': {'1': {u'quantidade_votacoes': 8, u'nome': u'1989 e 1990'}}, u'partidos': [{u'cor': u'#000000', u'nome': u'Girondinos', u'tamanho': [[1, 26.0]], u'numero': 27, u'y': [[1, 87.62]], u'x': [[1, 34.15]]}, {u'cor': u'#000000', u'nome': u'Monarquistas', u'tamanho': [[1, 26.0]], u'numero': 79, u'y': [[1, 44.91]], u'x': [[1, 90.51]]}, {u'cor': u'#000000', u'nome': u'Jacobinos', u'tamanho': [[1, 26.0]], u'numero': 42, u'y': [[1, 17.47]], u'x': [[1, 25.34]]}]}
        gen = grafico.JsonAnaliseGenerator()
        json = gen.get_json_dic(self.casa_legislativa)
        self.maxDiff = None
        self.assertEqual(json, EXPECTED_JSON)

class TemasTest(TestCase):

    dici = None

    def setUp(self):
        self.dici = filtro.Temas.get_temas_padrao()
        self.dici.inserir_sinonimo("testing","test")

    def test_criacao_dicionario(self):
        self.assertTrue(len(self.dici.dicionario.items()) > 0)
    
    def test_insercao_palavra_nova(self):
        self.dici.inserir_sinonimo("teste", "test")
        self.assertTrue(self.dici.dicionario.has_key("teste"))

    def test_insercao_sinonimo_novo(self):
        self.dici.inserir_sinonimo("testing", "teste")
        self.assertEquals(2, len(self.dici.dicionario["testing"]))

    def test_insercao_erro(self):
        with self.assertRaises(ValueError):
            self.dici.inserir_sinonimo("testing", None)
            
        with self.assertRaises(ValueError):
            self.dici.inserir_sinonimo(None, "dinossauro")

    def test_recuperacao_com_uma_chave(self):
        self.dici.inserir_sinonimo("testing","assert")
        palavras = self.dici.recuperar_palavras_por_sinonimo("assert")
        self.assertEquals(1, len(palavras))

        self.dici.inserir_sinonimo("another","assert")
        palavras = self.dici.recuperar_palavras_por_sinonimo("assert")
        self.assertEquals(2, len(palavras))

        palavras = self.dici.recuperar_palavras_por_sinonimo("sandslash")
        self.assertEquals(0, len(palavras))

    def test_recuperacao_erro(self):
        with self.assertRaises(ValueError):
            self.dici.recuperar_palavras_por_sinonimo(None)

############################
# Testes não automatizados #
############################

class GraficoTestManual():

    def importa_dados(self):
        if not models.CasaLegislativa.objects.filter(nome_curto='conv').exists():
            importer = convencao.ImportadorConvencao()
            importer.importar()
        self.casa_legislativa = models.CasaLegislativa.objects.get(nome_curto='conv')
        g = models.Partido.objects.get(nome=convencao.GIRONDINOS)
        j = models.Partido.objects.get(nome=convencao.JACOBINOS)
        m = models.Partido.objects.get(nome=convencao.MONARQUISTAS)
        self.partidos = [g, j, m]

    def testa_geracao_figura(self):
        self.importa_dados()
        an = analise.AnalisadorPeriodo(self.casa_legislativa, partidos=self.partidos)
        an.partidos_2d()
        gen = GeradorGrafico(an)
        gen.figura()

def main():
    test = GraficoTest()
    test.testa_geracao_figura()


            
