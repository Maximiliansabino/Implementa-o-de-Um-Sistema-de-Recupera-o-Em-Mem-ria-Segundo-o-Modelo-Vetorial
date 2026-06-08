# -*- coding: utf-8 -*-
"""
processador_consultas.py  (Modulo 1)
------------------------------------
Transforma o arquivo de consultas (cfquery.xml) para o padrao de palavras
utilizado pelo sistema e gera os arquivos de consultas processadas e de
resultados esperados.

Arquivo de configuracao: PC.CFG
    LEIA=<arquivo xml de consultas>      (obrigatoria, 1x)
    CONSULTAS=<arquivo csv de saida>     (obrigatoria, 1x)
    ESPERADOS=<arquivo csv de saida>     (obrigatoria, 1x)
As instrucoes sao obrigatorias, aparecem uma unica vez e nessa ordem.

Saidas (CSV com separador ';' e cabecalho na 1a linha):
    CONSULTAS -> QueryNumber ; QueryText
    ESPERADOS -> QueryNumber ; DocNumber ; DocVotes

DocVotes: a partir do atributo Score de cada Item, conta-se como voto
qualquer digito diferente de zero (cada avaliador deu uma nota 0-2).
"""

import os
import csv
import xml.etree.ElementTree as ET

from utils import (
    configurar_logging,
    ler_config,
    normalizar_texto,
    garantir_pasta_do_arquivo,
    cronometro,
)

NOME_MODULO = "processador_consultas"


def _parse_xml_tolerante(caminho):
    """Le um XML possivelmente sem raiz unica / com DOCTYPE.

    Remove declaracoes <?xml?> e <!DOCTYPE?> e envolve o conteudo numa raiz
    sintetica para garantir um documento bem formado.
    """
    with open(caminho, "r", encoding="latin-1") as f:
        conteudo = f.read()
    import re

    conteudo = re.sub(r"<\?xml.*?\?>", "", conteudo, flags=re.DOTALL)
    conteudo = re.sub(r"<!DOCTYPE.*?>", "", conteudo, flags=re.DOTALL)
    return ET.fromstring("<ROOT>" + conteudo + "</ROOT>")


def _texto(elem):
    return elem.text if (elem is not None and elem.text) else ""


def _contar_votos(score):
    """Conta votos no atributo Score: qualquer digito diferente de zero conta.

    Ex.: '2000' -> 1 ; '1010' -> 2 ; '2221' -> 4 ; '0000' -> 0
    """
    if not score:
        return 0
    return sum(1 for c in str(score).strip() if c.isdigit() and c != "0")


def processar(caminho_config="PC.CFG"):
    logger = configurar_logging(NOME_MODULO)
    t_inicio = cronometro()
    logger.info("=== INICIO do Processador de Consultas ===")

    # ---- 1. Configuracao -------------------------------------------------
    instrucoes = ler_config(caminho_config, logger)
    cfg = {}
    for chave, valor in instrucoes:
        cfg[chave] = valor
    for obrig in ("LEIA", "CONSULTAS", "ESPERADOS"):
        if obrig not in cfg:
            logger.error("Instrucao obrigatoria ausente no %s: %s", caminho_config, obrig)
            raise ValueError("Instrucao obrigatoria ausente: %s" % obrig)

    arq_entrada = cfg["LEIA"]
    arq_consultas = cfg["CONSULTAS"]
    arq_esperados = cfg["ESPERADOS"]

    # ---- 2. Leitura dos dados -------------------------------------------
    logger.info("Lendo arquivo de consultas (XML): %s", arq_entrada)
    t_leitura = cronometro()
    raiz = _parse_xml_tolerante(arq_entrada)
    queries = list(raiz.iter("QUERY"))
    logger.info("Dados lidos: %d consulta(s) em %.3fs",
                len(queries), cronometro() - t_leitura)

    # ---- 3. Processamento ------------------------------------------------
    garantir_pasta_do_arquivo(arq_consultas)
    garantir_pasta_do_arquivo(arq_esperados)

    n_consultas = 0
    n_esperados = 0
    tempo_total_consulta = 0.0

    with open(arq_consultas, "w", encoding="utf-8", newline="") as f_cons, \
         open(arq_esperados, "w", encoding="utf-8", newline="") as f_esp:

        w_cons = csv.writer(f_cons, delimiter=";")
        w_esp = csv.writer(f_esp, delimiter=";")
        w_cons.writerow(["QueryNumber", "QueryText"])
        w_esp.writerow(["QueryNumber", "DocNumber", "DocVotes"])

        for q in queries:
            t_q = cronometro()

            num = _texto(q.find("QueryNumber")).strip()
            try:
                num = str(int(num))  # remove zeros a esquerda (00001 -> 1)
            except ValueError:
                pass

            texto = normalizar_texto(_texto(q.find("QueryText")))
            # remove qualquer ';' residual (a normalizacao ja garante so A-Z)
            texto = texto.replace(";", " ")
            w_cons.writerow([num, texto])
            n_consultas += 1

            # Resultados esperados: Records / Item (atributo score)
            registros = q.find("Records")
            if registros is not None:
                for item in registros.findall("Item"):
                    doc = _texto(item).strip()
                    try:
                        doc = str(int(doc))
                    except ValueError:
                        pass
                    score = item.get("score") or item.get("Score") or ""
                    votos = _contar_votos(score)
                    if votos > 0:  # qualquer coisa diferente de zero e' um voto
                        w_esp.writerow([num, doc, votos])
                        n_esperados += 1

            tempo_total_consulta += cronometro() - t_q

    # ---- Estatisticas / LOG ---------------------------------------------
    logger.info("Arquivo CONSULTAS gerado: %s (%d consultas)", arq_consultas, n_consultas)
    logger.info("Arquivo ESPERADOS gerado: %s (%d pares consulta-documento)",
                arq_esperados, n_esperados)
    if n_consultas:
        logger.info("Tempo medio de processamento por consulta: %.5fs",
                    tempo_total_consulta / n_consultas)
    logger.info("=== FIM do Processador de Consultas em %.3fs ===",
                cronometro() - t_inicio)
    return n_consultas, n_esperados


if __name__ == "__main__":
    import sys
    config = sys.argv[1] if len(sys.argv) > 1 else "PC.CFG"
    processar(config)
