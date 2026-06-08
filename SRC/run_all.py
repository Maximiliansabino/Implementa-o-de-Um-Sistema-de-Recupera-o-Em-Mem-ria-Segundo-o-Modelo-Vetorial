# -*- coding: utf-8 -*-
"""
run_all.py
----------
Executa o pipeline completo do Sistema de Recuperacao em Memoria segundo o
Modelo Vetorial, em ordem (processamento em batch):

    1. Processador de Consultas   (PC.CFG)
    2. Gerador de Lista Invertida (GLI.CFG)
    3. Indexador                  (INDEX.CFG)
    4. Buscador                   (BUSCA.CFG)

Uso (a partir da raiz do repositorio):
    python SRC/run_all.py

Os arquivos de dados da base CysticFibrosis2 (cfquery.xml, cf74.xml ...
cf79.xml) devem estar na pasta  data/  na raiz do repositorio.
Os resultados sao gravados na pasta  RESULT/  e os logs em  logs/.
"""

import os
import sys

# Garante que a pasta SRC esteja no path (para os imports dos modulos) e que
# o diretorio de trabalho seja a raiz do repositorio (para os caminhos
# relativos data/ e RESULT/ dos arquivos .CFG).
DIR_SRC = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(DIR_SRC)
sys.path.insert(0, DIR_SRC)
os.chdir(RAIZ)

from processador_consultas import processar
from gerador_lista_invertida import gerar
from indexador import indexar
from buscador import buscar


def cfg(nome):
    return os.path.join(DIR_SRC, nome)


def main():
    print("\n" + "=" * 70)
    print(" SISTEMA DE RECUPERACAO - MODELO VETORIAL  (pipeline completo)")
    print("=" * 70 + "\n")

    print(">>> [1/4] Processador de Consultas")
    processar(cfg("PC.CFG"))

    print("\n>>> [2/4] Gerador de Lista Invertida")
    gerar(cfg("GLI.CFG"))

    print("\n>>> [3/4] Indexador (tf/idf)")
    indexar(cfg("INDEX.CFG"))

    print("\n>>> [4/4] Buscador")
    buscar(cfg("BUSCA.CFG"))

    print("\n" + "=" * 70)
    print(" CONCLUIDO. Veja os arquivos em RESULT/ e os logs em logs/.")
    print("=" * 70 + "\n")


if __name__ == "__main__":
    main()
