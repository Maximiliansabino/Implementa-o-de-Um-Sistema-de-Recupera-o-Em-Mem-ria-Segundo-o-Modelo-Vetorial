# -*- coding: utf-8 -*-
"""
indexador.py  (Modulo 3)
------------------------
Cria o modelo vetorial (matriz termo-documento ponderada por tf/idf) a partir
da lista invertida simples.

Arquivo de configuracao: INDEX.CFG
    LEIA=<arquivo csv da lista invertida>   (obrigatoria)
    ESCREVA=<arquivo do modelo>             (obrigatoria)
    ESQUEMA_TF=<raw|log|bin>                (opcional, default 'log')
        -> permite alterar de forma simples a medida de tf

Regras de termo (ja garantidas pela lista invertida, reaplicadas por seguranca):
    (a) palavras com 2 letras ou mais
    (b) apenas letras
    (c) maiusculas ASCII A-Z

Modelo gerado (ver MODELO.TXT para o formato completo) e salvo com pickle:
    {
      'esquema_tf' : str,
      'termos'     : [t0, t1, ...]            # vocabulario ordenado
      'documentos' : [d0, d1, ...]            # ids de documento ordenados
      'idf'        : {termo: idf},
      'pesos'      : {termo: {docid: w_tfidf}},   # matriz esparsa termo-documento
      'normas'     : {docid: ||vetor_doc||},      # para cosseno
    }
"""

import ast
import csv
import math
import pickle
from collections import defaultdict

from utils import (
    configurar_logging,
    ler_config,
    garantir_pasta_do_arquivo,
    cronometro,
)

NOME_MODULO = "indexador"

# Permite ler listas invertidas grandes
csv.field_size_limit(10 ** 7)


def _peso_tf(tf, esquema):
    """Componente tf do peso. 'Permitir alteracao simples da medida'."""
    if tf <= 0:
        return 0.0
    if esquema == "raw":
        return float(tf)
    if esquema == "bin":
        return 1.0
    # default: log normalizado
    return 1.0 + math.log10(tf)


def _termo_valido(palavra):
    return len(palavra) >= 2 and palavra.isalpha()


def indexar(caminho_config="INDEX.CFG"):
    logger = configurar_logging(NOME_MODULO)
    t_inicio = cronometro()
    logger.info("=== INICIO do Indexador (Modelo Vetorial tf/idf) ===")

    # ---- Configuracao ----------------------------------------------------
    instrucoes = ler_config(caminho_config, logger)
    cfg = {}
    for k, v in instrucoes:
        cfg[k] = v
    for obrig in ("LEIA", "ESCREVA"):
        if obrig not in cfg:
            logger.error("Instrucao obrigatoria ausente em %s: %s", caminho_config, obrig)
            raise ValueError("Instrucao obrigatoria ausente: %s" % obrig)

    arq_entrada = cfg["LEIA"]
    arq_saida = cfg["ESCREVA"]
    esquema_tf = cfg.get("ESQUEMA_TF", "log").lower()
    logger.info("Esquema de tf escolhido: %s", esquema_tf)

    # ---- Leitura da lista invertida -------------------------------------
    logger.info("Lendo lista invertida: %s", arq_entrada)
    t_leitura = cronometro()

    # tf[termo][docid] = frequencia do termo no documento
    tf = defaultdict(lambda: defaultdict(int))
    documentos = set()
    n_linhas = 0

    with open(arq_entrada, "r", encoding="utf-8", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        cabecalho = next(leitor, None)  # descarta cabecalho
        for linha in leitor:
            if len(linha) < 2:
                continue
            palavra = linha[0].strip().upper()
            if not _termo_valido(palavra):
                continue
            try:
                docs = ast.literal_eval(linha[1])
            except (ValueError, SyntaxError):
                logger.warning("Lista de documentos invalida para o termo %r", palavra)
                continue
            for d in docs:
                tf[palavra][d] += 1
                documentos.add(d)
            n_linhas += 1

    logger.info("Lista invertida lida: %d termo(s), %d documento(s) em %.3fs",
                n_linhas, len(documentos), cronometro() - t_leitura)

    # ---- Construcao do modelo vetorial ----------------------------------
    logger.info("Calculando idf e pesos tf/idf...")
    t_proc = cronometro()
    N = len(documentos)

    idf = {}
    pesos = {}                       # matriz termo-documento esparsa
    normas = defaultdict(float)      # soma dos quadrados por documento

    tempo_por_termo = 0.0
    for termo, ocorrencias in tf.items():
        t_termo = cronometro()
        df = len(ocorrencias)              # numero de documentos com o termo
        idf_t = math.log10(N / df) if df else 0.0
        idf[termo] = idf_t

        linha_pesos = {}
        for docid, freq in ocorrencias.items():
            w = _peso_tf(freq, esquema_tf) * idf_t
            if w != 0.0:
                linha_pesos[docid] = w
                normas[docid] += w * w
        pesos[termo] = linha_pesos
        tempo_por_termo += cronometro() - t_termo

    # norma euclidiana de cada documento (para similaridade do cosseno)
    for docid in list(normas.keys()):
        normas[docid] = math.sqrt(normas[docid])

    logger.info("Modelo construido em %.3fs", cronometro() - t_proc)

    # ---- Salvar modelo ---------------------------------------------------
    modelo = {
        "esquema_tf": esquema_tf,
        "termos": sorted(tf.keys()),
        "documentos": sorted(documentos),
        "idf": idf,
        "pesos": pesos,
        "normas": dict(normas),
    }

    garantir_pasta_do_arquivo(arq_saida)
    logger.info("Salvando modelo em: %s", arq_saida)
    with open(arq_saida, "wb") as f:
        pickle.dump(modelo, f, protocol=pickle.HIGHEST_PROTOCOL)

    # ---- Estatisticas / LOG ---------------------------------------------
    logger.info("Termos (vocabulario): %d", len(modelo["termos"]))
    logger.info("Documentos no modelo: %d", N)
    if tf:
        logger.info("Tempo medio de processamento por termo/palavra: %.7fs",
                    tempo_por_termo / len(tf))
    logger.info("=== FIM do Indexador em %.3fs ===", cronometro() - t_inicio)
    return modelo


if __name__ == "__main__":
    import sys
    config = sys.argv[1] if len(sys.argv) > 1 else "INDEX.CFG"
    indexar(config)
