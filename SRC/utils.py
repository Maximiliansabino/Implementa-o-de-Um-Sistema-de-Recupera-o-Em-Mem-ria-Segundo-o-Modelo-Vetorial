# -*- coding: utf-8 -*-
"""
utils.py
--------
Funcoes compartilhadas pelos modulos do Sistema de Recuperacao em Memoria
segundo o Modelo Vetorial.

Contem:
  - Configuracao padronizada de LOG (modulo logging do Python)
  - Normalizacao de texto (maiusculas, sem acento, apenas letras)
  - Tokenizacao com NLTK (com fallback caso o NLTK nao esteja disponivel)
  - Leitura dos arquivos de configuracao (.CFG)

Autor: (aluno)
Disciplina: Busca e Mineracao de Texto (BMT)
"""

import os
import re
import sys
import time
import logging
import unicodedata

# ---------------------------------------------------------------------------
# Tokenizacao via NLTK (com fallback robusto)
# ---------------------------------------------------------------------------
# O enunciado pede o uso da biblioteca NLTK. Tentamos importa-la e garantir o
# recurso 'punkt'. Caso o ambiente nao tenha o NLTK ou nao haja rede para o
# download, caimos num tokenizador simples baseado em expressao regular, que
# produz exatamente o mesmo resultado para o nosso caso (apenas letras).
try:
    import nltk

    def _garantir_punkt():
        for recurso in ("tokenizers/punkt", "tokenizers/punkt_tab"):
            try:
                nltk.data.find(recurso)
                return True
            except LookupError:
                continue
        for pacote in ("punkt", "punkt_tab"):
            try:
                nltk.download(pacote, quiet=True)
            except Exception:
                pass
        try:
            nltk.data.find("tokenizers/punkt")
            return True
        except LookupError:
            return False

    _NLTK_OK = _garantir_punkt()
except Exception:
    nltk = None
    _NLTK_OK = False


# ---------------------------------------------------------------------------
# LOG
# ---------------------------------------------------------------------------
def configurar_logging(nome_modulo, pasta_logs="logs"):
    """Cria e devolve um logger que escreve no console e em arquivo.

    O LOG permite, conforme exigido pelo enunciado:
      1. Identificar quando iniciaram as operacoes
      2. Identificar o inicio de cada parte do processamento
      3/4. Leitura do arquivo de configuracao e de dados
      5. Quantos dados foram lidos
      6. Quando terminaram os processamentos
      7. Tempos medios de processamento
      8. Erros, caso acontecam
    """
    os.makedirs(pasta_logs, exist_ok=True)
    logger = logging.getLogger(nome_modulo)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Evita handlers duplicados se o modulo for reimportado.
    if logger.handlers:
        return logger

    fmt = logging.Formatter(
        "%(asctime)s | %(name)-22s | %(levelname)-7s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    fh = logging.FileHandler(
        os.path.join(pasta_logs, nome_modulo + ".log"), mode="w", encoding="utf-8"
    )
    fh.setFormatter(fmt)
    logger.addHandler(fh)

    ch = logging.StreamHandler(sys.stdout)
    ch.setFormatter(fmt)
    logger.addHandler(ch)

    return logger


# ---------------------------------------------------------------------------
# Normalizacao de texto
# ---------------------------------------------------------------------------
def remover_acentos(texto):
    """Remove acentos preservando as letras base (ASCII)."""
    nfkd = unicodedata.normalize("NFKD", texto)
    return "".join(c for c in nfkd if not unicodedata.combining(c))


def normalizar_texto(texto):
    """Deixa o texto em MAIUSCULAS (ASCII A-Z), sem acento e sem pontuacao.

    Tudo o que nao for letra A-Z vira espaco.
    """
    if texto is None:
        return ""
    texto = remover_acentos(texto)
    texto = texto.upper()
    # mantem apenas A-Z; demais caracteres viram espaco
    texto = re.sub(r"[^A-Z]+", " ", texto)
    return texto.strip()


# regex de fallback: sequencias de letras
_RE_PALAVRAS = re.compile(r"[A-Z]+")


def tokenizar(texto, min_letras=2):
    """Devolve a lista de tokens validos de um texto.

    Regras (conforme o Indexador):
      (a) palavras com 2 letras ou mais
      (b) apenas letras
      (c) convertidas para maiusculas ASCII A-Z
    """
    normalizado = normalizar_texto(texto)
    if not normalizado:
        return []

    if _NLTK_OK and nltk is not None:
        try:
            bruto = nltk.word_tokenize(normalizado)
        except Exception:
            bruto = _RE_PALAVRAS.findall(normalizado)
    else:
        bruto = _RE_PALAVRAS.findall(normalizado)

    tokens = []
    for tok in bruto:
        # garante apenas letras (o NLTK pode devolver pontuacao residual)
        if tok.isalpha() and len(tok) >= min_letras:
            tokens.append(tok)
    return tokens


# ---------------------------------------------------------------------------
# Leitura de arquivos de configuracao (.CFG)
# ---------------------------------------------------------------------------
def ler_config(caminho, logger=None):
    """Le um arquivo .CFG e devolve uma lista ordenada de pares (CHAVE, valor).

    Cada linha tem a forma CHAVE=valor. A ordem e preservada (importa para o
    Processador de Consultas, em que as instrucoes sao obrigatorias e
    aparecem nessa ordem). Linhas em branco e comentarios (#) sao ignorados.
    """
    if logger:
        logger.info("Lendo arquivo de configuracao: %s", caminho)

    if not os.path.isfile(caminho):
        raise FileNotFoundError("Arquivo de configuracao nao encontrado: %s" % caminho)

    instrucoes = []
    with open(caminho, "r", encoding="utf-8") as f:
        for n, linha in enumerate(f, start=1):
            linha = linha.strip()
            if not linha or linha.startswith("#"):
                continue
            if "=" not in linha:
                if logger:
                    logger.warning("Linha %d ignorada (sem '='): %r", n, linha)
                continue
            chave, valor = linha.split("=", 1)
            instrucoes.append((chave.strip().upper(), valor.strip()))

    if logger:
        logger.info("Configuracao lida: %d instrucao(oes)", len(instrucoes))
    return instrucoes


# ---------------------------------------------------------------------------
# Utilitarios diversos
# ---------------------------------------------------------------------------
def garantir_pasta_do_arquivo(caminho):
    """Cria a pasta de destino de um arquivo, se necessario."""
    pasta = os.path.dirname(os.path.abspath(caminho))
    if pasta:
        os.makedirs(pasta, exist_ok=True)


def cronometro():
    """Devolve um marcador de tempo de alta resolucao."""
    return time.perf_counter()
