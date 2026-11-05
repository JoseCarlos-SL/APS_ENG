"""Confere os valores de referência do exemplo com o núcleo da APS.

Salve este arquivo na pasta do projeto e execute:
    python -m unittest discover -s . -p "test_*.py" -v
"""

import json
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from aps_emergia import calcular, carregar, criar_exemplo


class TestConferenciaPlanilha(unittest.TestCase):
    def setUp(self):
        self.pasta_temporaria = tempfile.TemporaryDirectory()
        self.addCleanup(self.pasta_temporaria.cleanup)
        self.diretorio = Path(self.pasta_temporaria.name) / "exemplo"
        criar_exemplo(self.diretorio)

    def calcular_exemplo(self, quantidade):
        return calcular(
            *carregar(self.diretorio),
            "s2",
            Decimal(quantidade),
            "kg",
        )

    def test_dez_quilos_conferem_com_calculo_manual(self):
        resultado = self.calcular_exemplo("10")

        # p2: 10 kg / 5 kg por execução = 2 execuções.
        # Fonte f2: 2 J × 5 sej/J × 2 = 20 sej.
        # Entrada de p2: 1 kg de s1 × 2 = 2 kg de s1.
        # p1: 2 kg / 2 kg por execução = 1 execução.
        # Fonte f1: 4 J × 3 sej/J × 1 = 12 sej.
        esperado = {"p1": Decimal("12"), "p2": Decimal("20")}
        contribuicoes = {
            item["id_processo"]: Decimal(item["emergia_sej"])
            for item in resultado["contribuicoes"]
        }

        self.assertEqual(contribuicoes, esperado)
        self.assertEqual(
            Decimal(resultado["emergia_total_sej"]), Decimal("32")
        )
        self.assertEqual(
            Decimal(resultado["emergia_por_unidade_funcional_sej"]),
            Decimal("3.2"),
        )
        self.assertEqual(
            resultado["unidade_funcional"],
            {"quantidade": "10", "unidade": "kg"},
        )

    def test_cinco_quilos_reduzem_as_contribuicoes_pela_metade(self):
        resultado = self.calcular_exemplo("5")
        contribuicoes = {
            item["id_processo"]: Decimal(item["emergia_sej"])
            for item in resultado["contribuicoes"]
        }

        self.assertEqual(
            contribuicoes, {"p1": Decimal("6"), "p2": Decimal("10")}
        )
        self.assertEqual(
            Decimal(resultado["emergia_total_sej"]), Decimal("16")
        )
        self.assertEqual(
            Decimal(resultado["emergia_por_unidade_funcional_sej"]),
            Decimal("3.2"),
        )

    def test_resultado_pode_ser_registrado_em_json(self):
        resultado = self.calcular_exemplo("10")
        caminho = Path(self.pasta_temporaria.name) / "resultado.json"
        caminho.write_text(
            json.dumps(resultado, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        recuperado = json.loads(caminho.read_text(encoding="utf-8"))
        self.assertEqual(
            Decimal(recuperado["emergia_total_sej"]), Decimal("32")
        )
        self.assertEqual(len(recuperado["contribuicoes"]), 2)


if __name__ == "__main__":
    unittest.main()
