"""Núcleo inicial da APS: cálculo emergético em cadeias simples.

Requer Python 3.10 ou superior; utiliza apenas a biblioteca padrão.

Uso:
    python aps_emergia.py --criar-exemplo exemplo
    python aps_emergia.py --dados exemplo --saida s2 --quantidade 10 \
        --unidade kg --relatorio resultado.json

Arquivos esperados no diretório de dados:

processos.csv:
    id_processo,descricao

saidas.csv:
    id_saida,id_processo,quantidade,unidade,referencia

conexoes.csv:
    id_saida,id_processo_consumidor,quantidade,unidade

fontes.csv:
    id_fonte,id_processo,quantidade,unidade,valor_emergia_por_unidade

Cada quantidade nos CSVs corresponde a uma execução de referência do
respectivo processo. Em conexoes.csv, a quantidade é consumida por execução
do processo consumidor. Em fontes.csv, o valor emergético é expresso em
sej por unidade da fonte. Não há conversão automática de unidades.
"""

from __future__ import annotations

import argparse
import csv
import json
from collections import Counter
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path


COLUNAS = {
    "processos.csv": ("id_processo", "descricao"),
    "saidas.csv": (
        "id_saida", "id_processo", "quantidade", "unidade", "referencia"
    ),
    "conexoes.csv": (
        "id_saida", "id_processo_consumidor", "quantidade", "unidade"
    ),
    "fontes.csv": (
        "id_fonte", "id_processo", "quantidade", "unidade",
        "valor_emergia_por_unidade"
    ),
}


class ErroDados(ValueError):
    """Entrada inválida ou situação não suportada pelo cálculo inicial."""


@dataclass(frozen=True)
class Saida:
    identificador: str
    processo: str
    quantidade: Decimal
    unidade: str


@dataclass(frozen=True)
class Conexao:
    saida: str
    consumidor: str
    quantidade: Decimal


@dataclass(frozen=True)
class Fonte:
    identificador: str
    processo: str
    quantidade: Decimal
    unidade: str
    valor_por_unidade: Decimal


def numero_positivo(valor: str, contexto: str) -> Decimal:
    try:
        numero = Decimal(valor)
    except (InvalidOperation, ValueError) as exc:
        raise ErroDados(f"{contexto}: número inválido: {valor!r}") from exc
    if not numero.is_finite() or numero <= 0:
        raise ErroDados(f"{contexto}: o valor deve ser finito e maior que zero")
    return numero


def ler_csv(diretorio: Path, nome: str) -> list[dict[str, str]]:
    caminho = diretorio / nome
    try:
        with caminho.open("r", encoding="utf-8-sig", newline="") as arquivo:
            leitor = csv.DictReader(arquivo)
            colunas = leitor.fieldnames
            if colunas is None or len(colunas) != len(set(colunas)):
                raise ErroDados(f"{caminho}: cabeçalho vazio ou duplicado")
            ausentes = set(COLUNAS[nome]) - set(colunas)
            if ausentes:
                raise ErroDados(
                    f"{caminho}: colunas ausentes: {', '.join(sorted(ausentes))}"
                )

            registros = []
            for linha, registro in enumerate(leitor, start=2):
                if None in registro:
                    raise ErroDados(f"{caminho}, linha {linha}: colunas extras")
                if all(not str(valor or "").strip()
                       for valor in registro.values()):
                    continue
                limpo = {}
                for coluna in COLUNAS[nome]:
                    valor = registro.get(coluna)
                    if valor is None or not valor.strip():
                        raise ErroDados(
                            f"{caminho}, linha {linha}: "
                            f"campo obrigatório vazio: {coluna}"
                        )
                    limpo[coluna] = valor.strip()
                limpo["_origem"] = f"{caminho}, linha {linha}"
                registros.append(limpo)
            return registros
    except (OSError, UnicodeError) as exc:
        raise ErroDados(f"Não foi possível ler {caminho}: {exc}") from exc


def identificadores_unicos(
    registros: list[dict[str, str]], campo: str
) -> None:
    vistos = set()
    for registro in registros:
        valor = registro[campo]
        if valor in vistos:
            raise ErroDados(
                f"{registro['_origem']}: {campo} duplicado: {valor}"
            )
        vistos.add(valor)


def carregar(diretorio: Path) -> tuple[
    dict[str, str], dict[str, Saida], list[Conexao], list[Fonte]
]:
    tabelas = {nome: ler_csv(diretorio, nome) for nome in COLUNAS}
    processos_brutos = tabelas["processos.csv"]
    saidas_brutas = tabelas["saidas.csv"]
    conexoes_brutas = tabelas["conexoes.csv"]
    fontes_brutas = tabelas["fontes.csv"]

    for registros, campo in (
        (processos_brutos, "id_processo"),
        (saidas_brutas, "id_saida"),
        (fontes_brutas, "id_fonte"),
    ):
        identificadores_unicos(registros, campo)

    processos = {
        r["id_processo"]: r["descricao"] for r in processos_brutos
    }
    saidas = {}
    for r in saidas_brutas:
        if r["id_processo"] not in processos:
            raise ErroDados(
                f"{r['_origem']}: processo inexistente: {r['id_processo']}"
            )
        if r["referencia"].lower() not in ("sim", "nao"):
            raise ErroDados(
                f"{r['_origem']}: referencia deve ser 'sim' ou 'nao'"
            )
        saidas[r["id_saida"]] = Saida(
            r["id_saida"],
            r["id_processo"],
            numero_positivo(r["quantidade"], r["_origem"]),
            r["unidade"],
        )

    conexoes = []
    for r in conexoes_brutas:
        saida = saidas.get(r["id_saida"])
        if saida is None:
            raise ErroDados(
                f"{r['_origem']}: saída inexistente: {r['id_saida']}"
            )
        if r["id_processo_consumidor"] not in processos:
            raise ErroDados(
                f"{r['_origem']}: processo consumidor inexistente: "
                f"{r['id_processo_consumidor']}"
            )
        if r["unidade"] != saida.unidade:
            raise ErroDados(
                f"{r['_origem']}: unidade {r['unidade']!r} incompatível "
                f"com a saída {saida.identificador} ({saida.unidade})"
            )
        conexoes.append(Conexao(
            saida.identificador,
            r["id_processo_consumidor"],
            numero_positivo(r["quantidade"], r["_origem"]),
        ))

    fontes = []
    for r in fontes_brutas:
        if r["id_processo"] not in processos:
            raise ErroDados(
                f"{r['_origem']}: processo inexistente: {r['id_processo']}"
            )
        fontes.append(Fonte(
            r["id_fonte"],
            r["id_processo"],
            numero_positivo(r["quantidade"], r["_origem"]),
            r["unidade"],
            numero_positivo(
                r["valor_emergia_por_unidade"], r["_origem"]
            ),
        ))

    return processos, saidas, conexoes, fontes


def calcular(
    processos: dict[str, str],
    saidas: dict[str, Saida],
    conexoes: list[Conexao],
    fontes: list[Fonte],
    id_saida: str,
    quantidade: Decimal,
    unidade: str,
) -> dict:
    alvo = saidas.get(id_saida)
    if alvo is None:
        raise ErroDados(f"Saída selecionada inexistente: {id_saida}")
    if unidade != alvo.unidade:
        raise ErroDados(
            f"Unidade funcional incompatível: {unidade!r}; "
            f"esperada: {alvo.unidade!r}"
        )

    saidas_por_processo: dict[str, list[Saida]] = {}
    for saida in saidas.values():
        saidas_por_processo.setdefault(saida.processo, []).append(saida)

    entradas_por_processo: dict[str, list[Conexao]] = {}
    consumidores_por_saida = Counter()
    for conexao in conexoes:
        entradas_por_processo.setdefault(conexao.consumidor, []).append(
            conexao
        )
        consumidores_por_saida[conexao.saida] += 1

    fontes_por_processo: dict[str, list[Fonte]] = {}
    for fonte in fontes:
        fontes_por_processo.setdefault(fonte.processo, []).append(fonte)

    contribuicoes = []
    processos_ativos = set()
    processos_visitados = set()

    def percorrer(saida: Saida, demanda: Decimal) -> None:
        processo = saida.processo
        if processo in processos_ativos:
            raise ErroDados(
                f"Realimentação detectada em {processo}: "
                "cálculo ainda não implementado"
            )
        if processo in processos_visitados:
            raise ErroDados(
                f"Processo {processo} alcançado mais de uma vez: "
                "possível reconvergência; cálculo ainda não implementado"
            )
        if len(saidas_por_processo[processo]) != 1:
            raise ErroDados(
                f"Coprodutos no processo {processo}: "
                "cálculo ainda não implementado"
            )
        if consumidores_por_saida[saida.identificador] > 1:
            raise ErroDados(
                f"Divisão da saída {saida.identificador}: "
                "cálculo ainda não implementado"
            )

        entradas = entradas_por_processo.get(processo, [])
        processos_ativos.add(processo)
        processos_visitados.add(processo)
        execucoes = demanda / saida.quantidade

        for fonte in fontes_por_processo.get(processo, []):
            quantidade_fonte = fonte.quantidade * execucoes
            emergia = quantidade_fonte * fonte.valor_por_unidade
            contribuicoes.append({
                "id_fonte": fonte.identificador,
                "id_processo": processo,
                "quantidade_utilizada": str(quantidade_fonte),
                "unidade_fonte": fonte.unidade,
                "valor_emergia_por_unidade": str(fonte.valor_por_unidade),
                "emergia_sej": str(emergia),
            })

        for entrada in entradas:
            percorrer(
                saidas[entrada.saida],
                entrada.quantidade * execucoes,
            )

        processos_ativos.remove(processo)

    percorrer(alvo, quantidade)
    total = sum(
        (Decimal(item["emergia_sej"]) for item in contribuicoes),
        Decimal("0"),
    )
    return {
        "escopo": "cadeia simples, sem coprodutos, divisão ou realimentação",
        "saida": id_saida,
        "processo": alvo.processo,
        "descricao_processo": processos[alvo.processo],
        "unidade_funcional": {
            "quantidade": str(quantidade),
            "unidade": unidade,
        },
        "contribuicoes": contribuicoes,
        "emergia_total_sej": str(total),
        "emergia_por_unidade_funcional_sej": str(total / quantidade),
    }


def criar_exemplo(diretorio: Path) -> None:
    exemplo = {
        "processos.csv": [
            ["id_processo", "descricao"],
            ["p1", "Produção do insumo"],
            ["p2", "Produção do produto"],
        ],
        "saidas.csv": [
            ["id_saida", "id_processo", "quantidade", "unidade",
             "referencia"],
            ["s1", "p1", "2", "kg", "sim"],
            ["s2", "p2", "5", "kg", "sim"],
        ],
        "conexoes.csv": [
            ["id_saida", "id_processo_consumidor", "quantidade",
             "unidade"],
            ["s1", "p2", "1", "kg"],
        ],
        "fontes.csv": [
            ["id_fonte", "id_processo", "quantidade", "unidade",
             "valor_emergia_por_unidade"],
            ["f1", "p1", "4", "J", "3"],
            ["f2", "p2", "2", "J", "5"],
        ],
    }
    diretorio.mkdir(parents=True, exist_ok=True)
    for nome, linhas in exemplo.items():
        caminho = diretorio / nome
        if caminho.exists():
            raise ErroDados(
                f"{caminho} já existe; escolha outro diretório "
                "para não sobrescrever dados"
            )
    for nome, linhas in exemplo.items():
        with (diretorio / nome).open(
            "w", encoding="utf-8", newline=""
        ) as arquivo:
            csv.writer(arquivo).writerows(linhas)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    grupo = parser.add_mutually_exclusive_group(required=True)
    grupo.add_argument(
        "--criar-exemplo", type=Path, metavar="DIRETORIO"
    )
    grupo.add_argument("--dados", type=Path, metavar="DIRETORIO")
    parser.add_argument("--saida", help="Identificador da saída analisada")
    parser.add_argument(
        "--quantidade", help="Quantidade da unidade funcional"
    )
    parser.add_argument("--unidade", help="Unidade da saída analisada")
    parser.add_argument(
        "--relatorio", type=Path, help="Destino opcional do relatório JSON"
    )
    args = parser.parse_args()

    try:
        if args.criar_exemplo is not None:
            criar_exemplo(args.criar_exemplo)
            print(f"Exemplo criado em: {args.criar_exemplo}")
            return

        if not all((args.saida, args.quantidade, args.unidade)):
            parser.error(
                "com --dados, informe --saida, --quantidade e --unidade"
            )

        resultado = calcular(
            *carregar(args.dados),
            args.saida,
            numero_positivo(
                args.quantidade, "quantidade da unidade funcional"
            ),
            args.unidade,
        )
        texto = json.dumps(resultado, ensure_ascii=False, indent=2)
        print(texto)
        if args.relatorio is not None:
            try:
                args.relatorio.write_text(
                    texto + "\n", encoding="utf-8"
                )
            except OSError as exc:
                raise ErroDados(
                    f"Não foi possível gravar {args.relatorio}: {exc}"
                ) from exc
    except ErroDados as exc:
        parser.exit(1, f"Erro: {exc}\n")


if __name__ == "__main__":
    main()
