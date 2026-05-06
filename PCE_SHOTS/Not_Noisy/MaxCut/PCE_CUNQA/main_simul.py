import os
import sys
import argparse
import numpy as np

# Permitir imports desde HOME
sys.path.append(os.getenv("HOME"))

from cunqa.qutils import qraise, qdrop

# === IMPORTACIÓN DE FUNCIONES PRINCIPALES ===
from src.exe_experiments import (
    casuistica_experimento,
    ejecutar_experimentos
)

from src.auxiliar import num_qubits
from src.grafica_csv import graficar_coste


# ============================================================
# ARGPARSE
# ============================================================

parser = argparse.ArgumentParser(description="Experimento completo con ejecución y gráfica")

parser.add_argument("--family", type=str, required=True,
                    help="Nombre de la familia QPU ya levantada")

parser.add_argument("--problema", type=str, required=True,
                    help="Nombre del problema (ej: MaxCut)")

parser.add_argument("--tamaño", type=int, required=True,
                    help="Número de nodos del problema")

parser.add_argument("--k", type=int, required=True,
                    help="Parámetro k del problema")

parser.add_argument("--shots", type=int, required=True,
                    help="Número de shots")

parser.add_argument("--nqpus", type=int, required=True,
                    help="Número de QPUs a usar")

parser.add_argument("--maxiter", type=int, default=10,
                    help="Número máximo de iteraciones del optimizador")

parser.add_argument("--seed", type=int, default=33,
                    help="Semilla aleatoria")

args = parser.parse_args()

family_name = args.family
problema = args.problema
tamaño = args.tamaño
k = args.k
n_shots = args.shots
num_qpus = args.nqpus
maxiter = args.maxiter
seed = args.seed



# ============================================================
# GENERACIÓN DE CASUÍSTICA
# ============================================================
Problema = [problema]
Tamaño = [tamaño]
K = [k]
Optimiz = ["DIFFERENTIALEVOLUTION"]
combo = casuistica_experimento(Problema, Tamaño, Optimiz, K)


# ============================================================
# PARÁMETROS INTERNOS
# ============================================================

alpha = 1.5 * num_qubits(tamaño, k)
beta = 0.5

optimizer_params = None

# ============================================================
# EJECUCIÓN
# ============================================================

ruta_csv, ruta_csv_iter = ejecutar_experimentos(
    exp_list=combo[0],
    optimizer_params=optimizer_params,
    alpha=alpha,
    beta=beta,
    maxiter=maxiter,
    n_shots=n_shots,
    nqpus=num_qpus,
    cunqa_str="Circuits",
    family_name=family_name
)

# ============================================================
# GRÁFICA
# ============================================================

graficar_coste(ruta_csv_iter)

print("\n✔ Experimento finalizado correctamente")
