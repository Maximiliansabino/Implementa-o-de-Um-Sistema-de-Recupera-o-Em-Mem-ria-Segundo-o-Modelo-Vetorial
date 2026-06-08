# -*- coding: utf-8 -*-
"""
run_exemplo.py
--------------
Executa o pipeline completo sobre a mini-base sintetica de  exemplo/dados/  ,
servindo como teste rapido da instalacao e da logica (sem precisar da base
CysticFibrosis2 real).

Uso (a partir da raiz do repositorio):
    python exemplo/run_exemplo.py

Saidas em  exemplo/RESULT/  e logs em  logs/ .
"""

import os
import sys

DIR_EXEMPLO = os.path.dirname(os.path.abspath(__file__))
RAIZ = os.path.dirname(DIR_EXEMPLO)
DIR_SRC = os.path.join(RAIZ, "SRC")

sys.path.insert(0, DIR_SRC)
os.chdir(RAIZ)

from processador_consultas import processar
from gerador_lista_invertida import gerar
from indexador import indexar
from buscador import buscar


def cfg(nome):
    return os.path.join(DIR_EXEMPLO, nome)


def mostrar(caminho):
    print("\n----- %s -----" % caminho)
    with open(caminho, "r", encoding="utf-8") as f:
        print(f.read().rstrip())


def main():
    print("\n=== TESTE COM A MINI-BASE DE EXEMPLO ===\n")
    processar(cfg("PC.CFG"))
    gerar(cfg("GLI.CFG"))
    indexar(cfg("INDEX.CFG"))
    buscar(cfg("BUSCA.CFG"))

    print("\n=== ARQUIVOS GERADOS ===")
    for nome in ("consultas.csv", "esperados.csv",
                 "lista_invertida.csv", "RESULTADOS.csv"):
        caminho = os.path.join(DIR_EXEMPLO, "RESULT", nome)
        if os.path.isfile(caminho):
            mostrar(caminho)

    print("\nOK: pipeline executado com sucesso.\n")


if __name__ == "__main__":
    main()
