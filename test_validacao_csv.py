"""Testes de regressão da validação dos arquivos CSV.

Execute na pasta do projeto:
    python -m unittest discover -s . -p "test_*.py" -v
"""

import csv
import tempfile
import unittest
from pathlib import Path

from aps_emergia import ErroDados, carregar, criar_exemplo


class TestValidacaoCSV(unittest.TestCase):
    def setUp(self):
        self.temporario = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporario.cleanup)
        self.diretorio = Path(self.temporario.name) / "exemplo"
        criar_exemplo(self.diretorio)

    def alterar(self, nome, modificacao):
        caminho = self.diretorio / nome
        with caminho.open("r", encoding="utf-8", newline="") as arquivo:
            linhas = list(csv.reader(arquivo))
        modificacao(linhas)
        with caminho.open("w", encoding="utf-8", newline="") as arquivo:
            csv.writer(arquivo).writerows(linhas)

    def test_rejeita_cabecalho_duplicado(self):
        self.alterar(
            "processos.csv",
            lambda linhas: linhas[0].append("id_processo"),
        )
        with self.assertRaisesRegex(ErroDados, "cabeçalho vazio ou duplicado"):
            carregar(self.diretorio)

    def test_rejeita_coluna_obrigatoria_ausente(self):
        self.alterar(
            "processos.csv",
            lambda linhas: [linha.pop(1) for linha in linhas],
        )
        with self.assertRaisesRegex(ErroDados, "colunas ausentes"):
            carregar(self.diretorio)

    def test_rejeita_identificador_de_processo_duplicado(self):
        self.alterar(
            "processos.csv",
            lambda linhas: linhas.append(["p1", "Outro processo"]),
        )
        with self.assertRaisesRegex(ErroDados, "id_processo duplicado"):
            carregar(self.diretorio)

    def test_rejeita_processo_inexistente_na_saida(self):
        self.alterar(
            "saidas.csv",
            lambda linhas: linhas[1].__setitem__(1, "processo_inexistente"),
        )
        with self.assertRaisesRegex(ErroDados, "processo inexistente"):
            carregar(self.diretorio)

    def test_rejeita_unidade_incompativel_na_conexao(self):
        self.alterar(
            "conexoes.csv",
            lambda linhas: linhas[1].__setitem__(3, "L"),
        )
        with self.assertRaisesRegex(ErroDados, "unidade .* incompatível"):
            carregar(self.diretorio)

    def test_rejeita_quantidade_nao_finita(self):
        self.alterar(
            "fontes.csv",
            lambda linhas: linhas[1].__setitem__(2, "NaN"),
        )
        with self.assertRaisesRegex(ErroDados, "finito e maior que zero"):
            carregar(self.diretorio)

    def test_rejeita_referencia_invalida(self):
        self.alterar(
            "saidas.csv",
            lambda linhas: linhas[1].__setitem__(4, "talvez"),
        )
        with self.assertRaisesRegex(ErroDados, "referencia deve ser"):
            carregar(self.diretorio)


if __name__ == "__main__":
    unittest.main()
