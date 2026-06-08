# Sistema de Recuperação em Memória — Modelo Vetorial

Implementação de um Sistema de Recuperação da Informação (SRI) segundo o
**Modelo Vetorial** com ponderação **tf/idf** e ranqueamento por **similaridade
do cosseno**. Trabalho da disciplina **Busca e Mineração de Texto (BMT)** —
base de teste **CysticFibrosis2**.

O sistema é dividido em quatro módulos independentes que se comunicam por
arquivos e seguem o princípio de processamento em *batch*
(ler tudo → processar tudo → salvar tudo). Todos os módulos produzem **LOG**
(módulo `logging` do Python) na pasta `logs/`.

```
        cfquery.xml ──▶ [1] Processador de Consultas ──▶ consultas.csv
                                                     └──▶ esperados.csv

   cf74..cf79.xml ──▶ [2] Gerador Lista Invertida ──▶ lista_invertida.csv

 lista_invertida.csv ──▶ [3] Indexador (tf/idf) ──▶ modelo.pkl

 modelo.pkl + consultas.csv ──▶ [4] Buscador ──▶ RESULTADOS.csv
```

## Estrutura do repositório

```
.
├── SRC/                         # todo o código-fonte
│   ├── utils.py                 # log, normalização de texto, leitura de .CFG
│   ├── processador_consultas.py # Módulo 1
│   ├── gerador_lista_invertida.py# Módulo 2
│   ├── indexador.py             # Módulo 3
│   ├── buscador.py              # Módulo 4
│   ├── run_all.py               # executa o pipeline completo
│   ├── PC.CFG  GLI.CFG  INDEX.CFG  BUSCA.CFG   # arquivos de configuração
├── data/                        # arquivos da base CysticFibrosis2 (você coloca)
├── RESULT/                      # arquivos gerados (inclui RESULTADOS.csv)
├── logs/                        # logs de cada módulo
├── exemplo/                     # mini-base sintética para teste rápido
├── MODELO.TXT                   # descrição do formato do modelo
├── requirements.txt
└── README.MD
```

## Requisitos

* Python 3.8+
* NLTK (`pip install -r requirements.txt`). Na primeira execução o NLTK baixa o
  recurso `punkt`. Caso não haja rede, o sistema usa automaticamente um
  tokenizador de reserva (regex de letras) que produz o mesmo resultado.

```bash
pip install -r requirements.txt
```

## Como executar

1. Coloque os arquivos da base **CysticFibrosis2** em `data/`:
   `cfquery.xml`, `cf74.xml`, `cf75.xml`, … , `cf79.xml`.
2. A partir da **raiz do repositório**, rode o pipeline completo:

```bash
python SRC/run_all.py
```

Ou execute módulo a módulo (a ordem importa):

```bash
python SRC/processador_consultas.py   SRC/PC.CFG
python SRC/gerador_lista_invertida.py SRC/GLI.CFG
python SRC/indexador.py               SRC/INDEX.CFG
python SRC/buscador.py                SRC/BUSCA.CFG
```

### Teste rápido (sem a base real)

Há uma mini-base sintética em `exemplo/`. Para validar a instalação e a lógica:

```bash
python exemplo/run_exemplo.py
```

Os resultados do exemplo são gravados em `exemplo/RESULT/`.

## Os módulos

### 1. Processador de Consultas — `PC.CFG`
Lê `cfquery.xml` (formato `cfc2-query.dtd`) e gera dois CSV (separador `;`,
cabeçalho na 1ª linha):

* **CONSULTAS** — `QueryNumber ; QueryText` (consulta em maiúsculas, sem acento
  nem pontuação).
* **ESPERADOS** — `QueryNumber ; DocNumber ; DocVotes`. `DocVotes` é o número
  de votos do documento: a partir do atributo `Score` de cada `Item`, conta-se
  como voto **qualquer dígito diferente de zero** (cada avaliador deu nota 0–2).

Instruções obrigatórias, uma única vez e nessa ordem: `LEIA`, `CONSULTAS`,
`ESPERADOS`.

### 2. Gerador de Lista Invertida — `GLI.CFG`
Lê um ou mais XML (`cfc2.dtd`) usando os campos `RECORDNUM` e
`ABSTRACT`/`EXTRACT`, e grava a lista invertida simples em CSV:

```
Palavra ; lista de documentos (com repetição)
FIBROSIS ; [1, 2, 2, 3, 4, 5, 10, 15, 21, 21, 21]
```

Instruções: uma ou mais `LEIA`, seguidas de uma `ESCREVA`.

### 3. Indexador — `INDEX.CFG`
Constrói o **modelo vetorial** (matriz termo-documento em memória) com pesos
**tf/idf** a partir da lista invertida e salva o modelo (`modelo.pkl`).
Considera apenas palavras com **2 letras ou mais**, **somente letras**,
convertidas para **maiúsculas ASCII (A–Z)**.

A medida de `tf` é trocável de forma simples pela instrução opcional
`ESQUEMA_TF=log|raw|bin` (padrão `log`). Detalhes do formato em `MODELO.TXT`.

Instruções: `LEIA` (lista invertida) e `ESCREVA` (modelo).

### 4. Buscador — `BUSCA.CFG`
Carrega o modelo salvo e executa as consultas, ranqueando por **similaridade do
cosseno**. Cada palavra da consulta tem **peso 1** (vetor de consulta binário).
Gera o `RESULTADOS.csv` (separador `;`):

```
id_consulta ; [(posição_no_ranking, id_documento, distância), ...]
1 ; [(1, 139, 0.5123), (2, 151, 0.4810), ...]
```

Instruções: `MODELO`, `CONSULTAS`, `RESULTADOS`.

## LOG

Cada módulo registra em `logs/<modulo>.log` e no console: início das operações,
início de cada etapa, leitura dos arquivos de configuração e de dados,
quantidade de dados lidos, fim do processamento, tempos médios (por consulta,
documento e palavra) e erros, se houver.

## Entrega

* `SRC/` — todo o código-fonte
* `README.MD` — este arquivo
* `MODELO.TXT` — descrição do formato do modelo
* `RESULT/` — arquivos gerados, incluindo `RESULTADOS.csv`
