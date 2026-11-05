"""Testes de validação para chamadas diretas à função calcular.

Execute na pasta do projeto:
    python -m unittest discover -s . -p "test_*.py" -v
"""

import unittest
from decimal import Decimal

from aps_emergia import ErroDados, Fonte, Saida, calcular


class TestValidacaoCalculo(unittest.TestCase):
    def setUp(self):
        self.processos = {"p1": "Produto"}
        self.saidas = {
            "s1": Saida("s1", "p1", Decimal("5"), "kg")
        }
        self.fontes = [
            Fonte("f1", "p1", Decimal("2"), "J", Decimal("3"))
        ]

    def test_rejeita_quantidade_funcional_invalida(self):
        for valor in ("0", "-1", "NaN", "Infinity"):
            with self.subTest(quantidade=valor):
                with self.assertRaises(ErroDados):
                    calcular(
                        self.processos,
                        self.saidas,
                        [],
                        self.fontes,
                        "s1",
                        Decimal(valor),
                        "kg",
                    )


if __name__ == "__main__":
    unittest.main()
