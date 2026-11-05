# APS_ENG — Cálculo de emergia em cadeias de processos

Projeto acadêmico desenvolvido em Python para importar dados tabulares de processos e calcular a emergia associada a uma unidade funcional. A proposta é inspirada no software SCALE e integra uma APS de Engenharia de Software.

> **Estado atual:** o núcleo calcula cadeias simples e redes com múltiplas entradas independentes. Divisão de fluxos, coprodutos, reconvergência e realimentação são detectados, mas ainda não são calculados. O projeto não deve ser apresentado como uma implementação completa do SCALE.

## Requisitos

- Python 3.10 ou superior.
- Nenhuma dependência externa: o núcleo utiliza apenas a biblioteca padrão do Python.

## Arquivos principais

| Caminho | Finalidade |
|---|---|
| `aps_emergia.py` | Importação, validação, cálculo e interface de linha de comando. |
| `test_aps_emergia.py` | Testes automatizados do núcleo inicial. |
| `exemplo/` | Dados de exemplo em CSV. |
| `resultado.json` | Exemplo de relatório gerado pela aplicação. |

## Como usar

Abra um terminal na pasta do projeto e execute `aps_emergia.py` com Python. Há duas operações:

1. **Criar dados de exemplo:** use a opção `--criar-exemplo` seguida de uma pasta de destino que ainda não contenha os arquivos CSV.
2. **Calcular a emergia:** use `--dados` com o caminho da pasta que contém os CSVs e informe `--saida`, `--quantidade` e `--unidade`. A opção `--relatorio` permite gravar o resultado em um arquivo JSON.

Para consultar a descrição das opções no terminal, use a opção `--help`. No conjunto de exemplo criado pelo programa, a saída analisável é `s2`, cuja unidade é `kg`.

O programa exibe o relatório JSON no terminal. Quando `--relatorio` é informado, também grava esse conteúdo no caminho indicado.

### Dados de entrada

A pasta indicada em `--dados` deve conter quatro arquivos:

| Arquivo | Colunas obrigatórias | O que representa |
|---|---|---|
| `processos.csv` | `id_processo`, `descricao` | Identificação dos processos. |
| `saidas.csv` | `id_saida`, `id_processo`, `quantidade`, `unidade`, `referencia` | Saídas produzidas por execução de referência de cada processo. |
| `conexoes.csv` | `id_saida`, `id_processo_consumidor`, `quantidade`, `unidade` | Quantidade de uma saída consumida por execução do processo consumidor. |
| `fontes.csv` | `id_fonte`, `id_processo`, `quantidade`, `unidade`, `valor_emergia_por_unidade` | Fontes atribuídas a cada processo e seu valor emergético por unidade. |

O campo `referencia` aceita `sim` ou `nao`. O valor emergético das fontes é expresso em **sej por unidade da fonte**. As quantidades dos arquivos correspondem a uma execução de referência do respectivo processo.

**Não há conversão automática de unidades.** A unidade de uma conexão deve coincidir com a da saída que ela consome, e a unidade funcional informada deve coincidir com a da saída selecionada.

## Como executar os testes

Na raiz do projeto, execute o módulo `unittest` do Python com descoberta de testes na pasta atual e o padrão de arquivo `test_aps_emergia.py`, em modo detalhado. Ao final, o terminal deve informar `OK` se todos os testes passarem.

A execução registrada nesta etapa passou em **12 testes**. Eles verificam resultados de cadeias simples, escala da unidade funcional, múltiplas entradas independentes e rejeição de entradas inválidas ou de estruturas ainda não suportadas.

## Escopo e limitações

O cálculo percorre os processos a partir da saída selecionada, aceita múltiplas entradas independentes, ajusta as quantidades à unidade funcional e soma as contribuições das fontes. O relatório apresenta as contribuições individuais, a emergia total e a emergia por unidade funcional.

Para evitar resultados incorretos, a implementação atual interrompe o cálculo quando encontra:

- coprodutos;
- divisão de uma saída entre múltiplos consumidores;
- entradas que provocam reconvergência e possível dupla contagem;
- reconvergência de caminhos em um processo;
- realimentação.

Esses casos exigem regras adicionais de álgebra emergética e **não são contabilizados silenciosamente**. Uma próxima etapa do projeto é implementar e testar essas regras antes de ampliar o escopo declarado.

## Referência

MARVUGLIA, Antonino; BENETTO, Enrico; RIOS, Gordon; RUGANI, Benedetto. SCALE: Software for CALculating Emergy based on life cycle inventories. *Ecological Modelling*, v. 248, p. 80–91, 2013. DOI: https://doi.org/10.1016/j.ecolmodel.2012.09.013.