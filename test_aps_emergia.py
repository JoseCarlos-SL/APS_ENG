"""Testes automatizados para aps_emergia.py.

Coloque este arquivo na mesma pasta de aps_emergia.py e execute no terminal:

    python -m unittest -v test_aps_emergia.py

Utiliza somente a biblioteca padrão do Python.
"""

import csv
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from aps_emergia import ErroDados, calcular, carregar, criar_exemplo, numero_positivo


class TestesNucleoEmergia(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta_temporaria.cleanup)
        self.diretorio = Path(self.pasta_temporaria.name) / "exemplo"
        criar_exemplo(self.diretorio)

    def calcular_exemplo(self, quantidade="10", unidade="kg"):
        return calcular(
            *carregar(self.diretorio),
            "s2",
            Decimal(quantidade),
            unidade,
        )

    def adicionar_linha(self, nome_arquivo, linha):
        caminho = self.diretorio / nome_arquivo
        with caminho.open("a", encoding="utf-8", newline="") as arquivo:
            csv.writer(arquivo).writerow(linha)

    def test_resultado_do_exemplo_para_dez_quilos(self):
        resultado = self.calcular_exemplo()

        self.assertEqual(resultado["saida"], "s2")
        self.assertEqual(
            resultado["unidade_funcional"],
            {"quantidade": "10", "unidade": "kg"},
        )
        self.assertEqual(Decimal(resultado["emergia_total_sej"]), Decimal("32"))
        self.assertEqual(
            Decimal(resultado["emergia_por_unidade_funcional_sej"]),
            Decimal("3.2"),
        )

        contribuicoes = {
            item["id_fonte"]: Decimal(item["emergia_sej"])
            for item in resultado["contribuicoes"]
        }
        self.assertEqual(contribuicoes, {"f1": Decimal("12"), "f2": Decimal("20")})

    def test_resultado_escala_com_a_unidade_funcional(self):
        resultado = self.calcular_exemplo(quantidade="5")

        self.assertEqual(Decimal(resultado["emergia_total_sej"]), Decimal("16"))
        self.assertEqual(
            Decimal(resultado["emergia_por_unidade_funcional_sej"]),
            Decimal("3.2"),
        )

    def test_unidade_funcional_incompativel_e_rejeitada(self):
        with self.assertRaisesRegex(ErroDados, "Unidade funcional incompatível"):
            self.calcular_exemplo(unidade="J")

    def test_saida_inexistente_e_rejeitada(self):
        with self.assertRaisesRegex(ErroDados, "Saída selecionada inexistente"):
            calcular(*carregar(self.diretorio), "inexistente", Decimal("1"), "kg")

    def test_quantidades_invalidas_sao_rejeitadas(self):
        for valor in ("0", "-1", "NaN", "Infinity", "abc"):
            with self.subTest(valor=valor):
                with self.assertRaises(ErroDados):
                    numero_positivo(valor, "teste")

    def test_unidade_incompativel_na_conexao_e_rejeitada(self):
        caminho = self.diretorio / "conexoes.csv"
        caminho.write_text(
            "id_saida,id_processo_consumidor,quantidade,unidade\n"
            "s1,p2,1,J\n",
            encoding="utf-8",
        )

        with self.assertRaisesRegex(ErroDados, "unidade .* incompatível"):
            carregar(self.diretorio)

    def test_coprodutos_nao_sao_calculados_silenciosamente(self):
        self.adicionar_linha("saidas.csv", ["s3", "p2", "1", "kg", "nao"])

        with self.assertRaisesRegex(ErroDados, "Coprodutos"):
            self.calcular_exemplo()

    def test_realimentacao_nao_e_calculada_silenciosamente(self):
        self.adicionar_linha("conexoes.csv", ["s2", "p1", "1", "kg"])

        with self.assertRaisesRegex(ErroDados, "Realimentação"):
            self.calcular_exemplo()

    def test_criacao_do_exemplo_nao_sobrescreve_arquivos(self):
        with self.assertRaisesRegex(ErroDados, "já existe"):
            criar_exemplo(self.diretorio)


if __name__ == "__main__":
    unittest.main()
