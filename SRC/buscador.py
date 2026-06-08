# -*- coding: utf-8 -*-
"""
buscador.py  (Modulo 4)
-----------------------
Executa um conjunto de consultas sobre o modelo vetorial salvo e produz o
ranking de documentos para cada consulta.

Arquivo de configuracao: BUSCA.CFG
    MODELO=<arquivo do modelo>          (gerado pelo Indexador)
    CONSULTAS=<arquivo csv de consultas>(gerado pelo Processador de Consultas)
    RESULTADOS=<arquivo csv de saida>

Modelo de busca: vetorial, com similaridade do cosseno.
Cada palavra da consulta tem peso 1 (vetor de consulta binario).

Saida (CSV, separador ';'):
    id_da_consulta ; lista Python de trincas (posicao_no_ranking, id_documento, distancia)
    Ex.: 1 ; [(1, 139, 0.5123), (2, 151, 0.4810), ...]
"""

import csv
import math
import pickle
from collections import defaultdict

from utils import (
    configurar_logging,
    ler_config,
    tokenizar,
    garantir_pasta_do_arquivo,
    cronometro,
)

NOME_MODULO = "buscador"

csv.field_size_limit(10 ** 7)


def carregar_modelo(caminho, logger):
    logger.info("Lendo modelo: %s", caminho)
    with open(caminho, "rb") as f:
        modelo = pickle.load(f)
    logger.info("Modelo carregado: %d termos, %d documentos",
                len(modelo["termos"]), len(modelo["documentos"]))
    return modelo


def buscar_uma(consulta_tokens, modelo):
    """Calcula a similaridade do cosseno entre a consulta e cada documento.

    Vetor de consulta: peso 1 por palavra (binario sobre os termos distintos).
    Vetor de documento: pesos tf/idf armazenados no modelo.
    """
    pesos = modelo["pesos"]
    normas = modelo["normas"]

    # termos distintos da consulta presentes no vocabulario, peso 1
    termos_consulta = set(t for t in consulta_tokens if t in pesos)
    if not termos_consulta:
        return []

    # norma da consulta: vetor binario -> sqrt(numero de termos distintos)
    norma_q = math.sqrt(len(termos_consulta))

    # produto interno consulta . documento
    acumulado = defaultdict(float)
    for termo in termos_consulta:
        for docid, w_doc in pesos[termo].items():
            acumulado[docid] += 1.0 * w_doc   # peso 1 da consulta

    # cosseno = (q . d) / (||q|| * ||d||)
    similaridades = []
    for docid, produto in acumulado.items():
        norma_d = normas.get(docid, 0.0)
        if norma_d > 0.0 and norma_q > 0.0:
            sim = produto / (norma_q * norma_d)
            similaridades.append((docid, sim))

    # ordena por similaridade decrescente (desempate por id de documento)
    similaridades.sort(key=lambda x: (-x[1], x[0]))
    return similaridades


def buscar(caminho_config="BUSCA.CFG"):
    logger = configurar_logging(NOME_MODULO)
    t_inicio = cronometro()
    logger.info("=== INICIO do Buscador (Modelo Vetorial) ===")

    # ---- Configuracao ----------------------------------------------------
    instrucoes = ler_config(caminho_config, logger)
    cfg = {}
    for k, v in instrucoes:
        cfg[k] = v
    for obrig in ("MODELO", "CONSULTAS", "RESULTADOS"):
        if obrig not in cfg:
            logger.error("Instrucao obrigatoria ausente em %s: %s", caminho_config, obrig)
            raise ValueError("Instrucao obrigatoria ausente: %s" % obrig)

    arq_modelo = cfg["MODELO"]
    arq_consultas = cfg["CONSULTAS"]
    arq_resultados = cfg["RESULTADOS"]

    # ---- Leitura do modelo e das consultas ------------------------------
    modelo = carregar_modelo(arq_modelo, logger)

    logger.info("Lendo consultas: %s", arq_consultas)
    consultas = []
    with open(arq_consultas, "r", encoding="utf-8", newline="") as f:
        leitor = csv.reader(f, delimiter=";")
        next(leitor, None)  # cabecalho
        for linha in leitor:
            if len(linha) < 2:
                continue
            consultas.append((linha[0].strip(), linha[1]))
    logger.info("Consultas lidas: %d", len(consultas))

    # ---- Processamento das buscas ---------------------------------------
    garantir_pasta_do_arquivo(arq_resultados)
    tempo_total = 0.0
    n_consultas = 0

    with open(arq_resultados, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["QueryNumber", "Resultados"])

        for qid, texto in consultas:
            t_q = cronometro()
            tokens = tokenizar(texto, min_letras=2)
            ranking = buscar_uma(tokens, modelo)

            # trincas: (posicao_no_ranking, id_documento, distancia/similaridade)
            trincas = [
                (pos, docid, round(sim, 6))
                for pos, (docid, sim) in enumerate(ranking, start=1)
            ]
            w.writerow([qid, str(trincas)])

            tempo_total += cronometro() - t_q
            n_consultas += 1

    # ---- Estatisticas / LOG ---------------------------------------------
    logger.info("Resultados gravados em: %s", arq_resultados)
    logger.info("Consultas processadas: %d", n_consultas)
    if n_consultas:
        logger.info("Tempo medio de processamento por consulta: %.5fs",
                    tempo_total / n_consultas)
    logger.info("=== FIM do Buscador em %.3fs ===", cronometro() - t_inicio)
    return n_consultas


if __name__ == "__main__":
    import sys
    config = sys.argv[1] if len(sys.argv) > 1 else "BUSCA.CFG"
    buscar(config)
