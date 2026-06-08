# -*- coding: utf-8 -*-
"""
gerador_lista_invertida.py  (Modulo 2)
--------------------------------------
Cria as listas invertidas simples a partir dos documentos da base
(formato XML conforme cfc2.dtd).

Arquivo de configuracao: GLI.CFG
    LEIA=<arquivo xml>     (uma ou mais; podem se repetir)
    ESCREVA=<arquivo csv>  (uma unica, apos as LEIA)

Para cada documento usa-se RECORDNUM como identificador e o texto de
ABSTRACT ou EXTRACT como conteudo.

Saida (CSV, separador ';'):
    Palavra ; lista Python de identificadores de documento (com repeticao)
    Ex.: FIBROSIS ; [1, 2, 2, 3, 4, 5, 10, 15, 21, 21, 21]
"""

import re
import csv
import xml.etree.ElementTree as ET
from collections import defaultdict

from utils import (
    configurar_logging,
    ler_config,
    tokenizar,
    garantir_pasta_do_arquivo,
    cronometro,
)

NOME_MODULO = "gerador_lista_invertida"


def _parse_xml_tolerante(caminho):
    with open(caminho, "r", encoding="latin-1") as f:
        conteudo = f.read()
    conteudo = re.sub(r"<\?xml.*?\?>", "", conteudo, flags=re.DOTALL)
    conteudo = re.sub(r"<!DOCTYPE.*?>", "", conteudo, flags=re.DOTALL)
    return ET.fromstring("<ROOT>" + conteudo + "</ROOT>")


def _texto(elem):
    return elem.text if (elem is not None and elem.text) else ""


def gerar(caminho_config="GLI.CFG"):
    logger = configurar_logging(NOME_MODULO)
    t_inicio = cronometro()
    logger.info("=== INICIO do Gerador de Lista Invertida ===")

    # ---- Configuracao ----------------------------------------------------
    instrucoes = ler_config(caminho_config, logger)
    arquivos_leitura = [v for (k, v) in instrucoes if k == "LEIA"]
    escrita = [v for (k, v) in instrucoes if k == "ESCREVA"]

    if not arquivos_leitura:
        logger.error("Nenhuma instrucao LEIA encontrada em %s", caminho_config)
        raise ValueError("GLI.CFG precisa de pelo menos uma instrucao LEIA")
    if len(escrita) != 1:
        logger.error("E necessaria exatamente uma instrucao ESCREVA em %s", caminho_config)
        raise ValueError("GLI.CFG precisa de exatamente uma instrucao ESCREVA")
    arq_saida = escrita[0]

    # ---- Leitura + processamento ----------------------------------------
    # lista_invertida[palavra] = [docid, docid, ...]  (com repeticao)
    lista_invertida = defaultdict(list)

    total_docs = 0
    total_palavras = 0
    tempo_docs = 0.0

    for caminho in arquivos_leitura:
        logger.info("Lendo arquivo de dados (XML): %s", caminho)
        t_arq = cronometro()
        raiz = _parse_xml_tolerante(caminho)
        registros = list(raiz.iter("RECORD"))
        logger.info("  %d registro(s) lidos em %.3fs", len(registros), cronometro() - t_arq)

        for rec in registros:
            t_doc = cronometro()

            recordnum = _texto(rec.find("RECORDNUM")).strip()
            try:
                docid = int(recordnum)
            except ValueError:
                logger.warning("RECORDNUM invalido ignorado: %r", recordnum)
                continue

            # ABSTRACT ou EXTRACT
            corpo = rec.find("ABSTRACT")
            if corpo is None:
                corpo = rec.find("EXTRACT")
            texto = _texto(corpo)

            tokens = tokenizar(texto, min_letras=2)
            for palavra in tokens:
                lista_invertida[palavra].append(docid)

            total_docs += 1
            total_palavras += len(tokens)
            tempo_docs += cronometro() - t_doc

    # ---- Escrita ---------------------------------------------------------
    garantir_pasta_do_arquivo(arq_saida)
    logger.info("Escrevendo lista invertida em: %s", arq_saida)
    with open(arq_saida, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["Palavra", "Documentos"])
        for palavra in sorted(lista_invertida.keys()):
            docs = lista_invertida[palavra]
            docs.sort()
            w.writerow([palavra, str(docs)])

    # ---- Estatisticas / LOG ---------------------------------------------
    logger.info("Documentos processados: %d", total_docs)
    logger.info("Palavras (ocorrencias) processadas: %d", total_palavras)
    logger.info("Termos distintos na lista invertida: %d", len(lista_invertida))
    if total_docs:
        logger.info("Tempo medio por documento: %.5fs", tempo_docs / total_docs)
    if total_palavras:
        logger.info("Tempo medio por palavra: %.7fs", tempo_docs / total_palavras)
    logger.info("=== FIM do Gerador de Lista Invertida em %.3fs ===",
                cronometro() - t_inicio)
    return len(lista_invertida)


if __name__ == "__main__":
    import sys
    config = sys.argv[1] if len(sys.argv) > 1 else "GLI.CFG"
    gerar(config)
