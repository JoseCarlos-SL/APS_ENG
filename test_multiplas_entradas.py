"""Testes do próximo incremento: múltiplas entradas independentes.

Execute com:
    python -m unittest test_multiplas_entradas.py -v

Os dois primeiros testes devem falhar antes da alteração do núcleo.
"""

import unittest
from decimal import Decimal

from aps_emergia import Conexao, ErroDados, Fonte, Saida, calcular


def d(valor: str) -> Decimal:
    return Decimal(valor)


class TestMultiplasEntradas(unittest.TestCase):
    def test_duas_entradas_independentes_total_44_sej(self):
        """Resultado conferível à mão para 10 kg da saída s2.

        p2: 2 execuções × (2 J × 5 sej/J) = 20 sej
        p1: 1 execução  × (4 J × 3 sej/J) = 12 sej
        p3: 1 execução  × (2 J × 6 sej/J) = 12 sej
        Total: 44 sej; por kg da unidade funcional: 4,4 sej/kg.
        """
        processos = {
            "p1": "Produção do insumo",
            "p2": "Produção do produto",
            "p3": "Produção do segundo insumo",
        }
        saidas = {
            "s1": Saida("s1", "p1", d("2"), "kg"),
            "s2": Saida("s2", "p2", d("5"), "kg"),
            "s3": Saida("s3", "p3", d("3"), "L"),
        }
        conexoes = [
            Conexao("s1", "p2", d("1")),
            Conexao("s3", "p2", d("1.5")),
        ]
        fontes = [
            Fonte("f1", "p1", d("4"), "J", d("3")),
            Fonte("f2", "p2", d("2"), "J", d("5")),
            Fonte("f3", "p3", d("2"), "J", d("6")),
        ]

        resultado = calcular(
            processos, saidas, conexoes, fontes, "s2", d("10"), "kg"
        )

        self.assertEqual(d(resultado["emergia_total_sej"]), d("44"))
        self.assertEqual(
            d(resultado["emergia_por_unidade_funcional_sej"]), d("4.4")
        )
        self.assertEqual(
            {item["id_fonte"] for item in resultado["contribuicoes"]},
            {"f1", "f2", "f3"},
        )

    def test_duas_entradas_com_demandas_e_escalas_diferentes(self):
        """p2: 14 sej; p1: 6 sej; p3: 10 sej; total: 30 sej."""
        processos = {"p1": "Insumo A", "p2": "Produto", "p3": "Insumo B"}
        saidas = {
            "s1": Saida("s1", "p1", d("4"), "kg"),
            "s2": Saida("s2", "p2", d("4"), "kg"),
            "s3": Saida("s3", "p3", d("2"), "L"),
        }
        conexoes = [
            Conexao("s1", "p2", d("2")),
            Conexao("s3", "p2", d("1")),
        ]
        fontes = [
            Fonte("f1", "p1", d("2"), "J", d("3")),
            Fonte("f2", "p2", d("1"), "J", d("7")),
            Fonte("f3", "p3", d("2"), "J", d("5")),
        ]

        resultado = calcular(
            processos, saidas, conexoes, fontes, "s2", d("8"), "kg"
        )

        self.assertEqual(d(resultado["emergia_total_sej"]), d("30"))
        self.assertEqual(
            d(resultado["emergia_por_unidade_funcional_sej"]), d("3.75")
        )

    def test_divisao_de_fluxo_continua_nao_suportada(self):
        """A mesma saída alimenta dois processos; não pode ser somada."""
        processos = {"p1": "Origem", "p2": "Produto", "p3": "Intermediário"}
        saidas = {
            "s1": Saida("s1", "p1", d("1"), "kg"),
            "s2": Saida("s2", "p2", d("1"), "kg"),
            "s3": Saida("s3", "p3", d("1"), "kg"),
        }
        conexoes = [
            Conexao("s1", "p2", d("1")),
            Conexao("s1", "p3", d("1")),
            Conexao("s3", "p2", d("1")),
        ]
        fontes = [Fonte("f1", "p1", d("1"), "J", d("1"))]

        with self.assertRaisesRegex(ErroDados, "Divisão"):
            calcular(
                processos, saidas, conexoes, fontes, "s2", d("1"), "kg"
            )


if __name__ == "__main__":
    unittest.main()