"""Testes de integração da importação CSV e da execução pela linha de comando.

Execute na pasta do projeto:
    python -m unittest discover -s . -p "test_*.py" -v
"""

import csv
import json
import os
import subprocess
import sys
import tempfile
import unittest
from decimal import Decimal
from pathlib import Path

from aps_emergia import ErroDados, calcular, carregar


class TestIntegracaoCSV(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.diretorio = Path(self.temporario.name)

        self.escrever_csv(
            "processos.csv",
            ["id_processo", "descricao"],
            [
                ["p1", "Produção do insumo A"],
                ["p2", "Produção do produto"],
                ["p3", "Produção do insumo B"],
            ],
        )
        self.escrever_csv(
            "saidas.csv",
            ["id_saida", "id_processo", "quantidade", "unidade", "referencia"],
            [
                ["s1", "p1", "2", "kg", "sim"],
                ["s2", "p2", "5", "kg", "sim"],
                ["s3", "p3", "1", "kg", "sim"],
            ],
        )
        self.escrever_csv(
            "conexoes.csv",
            ["id_saida", "id_processo_consumidor", "quantidade", "unidade"],
            [
                ["s1", "p2", "1", "kg"],
                ["s3", "p2", "1", "kg"],
            ],
        )
        self.escrever_csv(
            "fontes.csv",
            [
                "id_fonte",
                "id_processo",
                "quantidade",
                "unidade",
                "valor_emergia_por_unidade",
            ],
            [
                ["f1", "p1", "4", "J", "3"],
                ["f2", "p2", "2", "J", "5"],
                ["f3", "p3", "3", "J", "2"],
            ],
        )

    def escrever_csv(self, nome, cabecalho, linhas):
        with (self.diretorio / nome).open(
            "w", encoding="utf-8", newline=""
        ) as arquivo:
            escritor = csv.writer(arquivo)
            escritor.writerow(cabecalho)
            escritor.writerows(linhas)

    def test_importacao_e_calculo_de_duas_entradas(self):
        dados = carregar(self.diretorio)
        resultado = calcular(*dados, "s2", Decimal("10"), "kg")

        # Para 10 kg de s2: p2 = 20 sej; p1 = 12 sej; p3 = 12 sej.
        self.assertEqual(
            Decimal(resultado["emergia_total_sej"]), Decimal("44")
        )
        self.assertEqual(
            Decimal(resultado["emergia_por_unidade_funcional_sej"]),
            Decimal("4.4"),
        )

        contribuicoes = {
            item["id_fonte"]: Decimal(item["emergia_sej"])
            for item in resultado["contribuicoes"]
        }
        self.assertEqual(
            contribuicoes,
            {
                "f1": Decimal("12"),
                "f2": Decimal("20"),
                "f3": Decimal("12"),
            },
        )

    def test_linha_de_comando_gera_relatorio_json(self):
        relatorio = self.diretorio / "resultado.json"
        programa = Path(__file__).resolve().parent / "aps_emergia.py"
        ambiente = os.environ.copy()
        ambiente["PYTHONIOENCODING"] = "utf-8"

        execucao = subprocess.run(
            [
                sys.executable,
                str(programa),
                "--dados",
                str(self.diretorio),
                "--saida",
                "s2",
                "--quantidade",
                "10",
                "--unidade",
                "kg",
                "--relatorio",
                str(relatorio),
            ],
            capture_output=True,
            text=True,
            encoding="utf-8",
            env=ambiente,
            check=False,
        )

        self.assertEqual(execucao.returncode, 0, execucao.stderr)
        self.assertTrue(relatorio.is_file())

        resultado_terminal = json.loads(execucao.stdout)
        resultado_arquivo = json.loads(
            relatorio.read_text(encoding="utf-8")
        )
        self.assertEqual(resultado_terminal, resultado_arquivo)
        self.assertEqual(
            Decimal(resultado_arquivo["emergia_total_sej"]),
            Decimal("44"),
        )

    def test_importacao_rejeita_unidade_incompativel(self):
        self.escrever_csv(
            "conexoes.csv",
            ["id_saida", "id_processo_consumidor", "quantidade", "unidade"],
            [
                ["s1", "p2", "1", "L"],
                ["s3", "p2", "1", "kg"],
            ],
        )

        with self.assertRaisesRegex(ErroDados, "incompatível"):
            carregar(self.diretorio)

    def test_divisao_de_fluxo_continua_rejeitada(self):
        # s1 passa a alimentar p2 e p3. O sistema ainda não deve
        # tratar esse caso como se fossem duas contribuições independentes.
        self.escrever_csv(
            "conexoes.csv",
            ["id_saida", "id_processo_consumidor", "quantidade", "unidade"],
            [
                ["s1", "p2", "1", "kg"],
                ["s1", "p3", "1", "kg"],
                ["s3", "p2", "1", "kg"],
            ],
        )

        with self.assertRaisesRegex(ErroDados, "Divisão"):
            calcular(
                *carregar(self.diretorio),
                "s2",
                Decimal("10"),
                "kg",
            )


if __name__ == "__main__":
    unittest.main()