import argparse
import numpy as np
from exe_expectation_values import ejecutar_valores_esperados_shots, calcular_metricas, guardar_resultados_json

# ============================================================
# ARGPARSE
# ============================================================

parser = argparse.ArgumentParser(description="Experimento Circuits vs Simulation")
parser.add_argument("--family", type=str, required=True, help="Nombre de la familia QPU ya levantada")
parser.add_argument("--problema", type=str, required=True, default="MaxCut")
parser.add_argument("--tamaño", type=int, required=True, help="Número de nodos del grafo")
parser.add_argument("--k", type=int, required=True)
parser.add_argument("--shots", type=int, required=True)
parser.add_argument("--seed", type=int, default=33)

args = parser.parse_args()

family_name_circuits = args.family
problema = args.problema
tamaño = args.tamaño
k = args.k
n_shots = args.shots
seed = args.seed

print("\n==============================")
print(f"Problema = {problema}")
print(f"Tamaño   = {tamaño}")
print(f"k        = {k}")
print(f"Shots    = {n_shots}")
print(f"Family   = {family_name_circuits}")
print(f"Seed     = {seed}")
print("==============================\n")


# ============================================================
# EJECUCIÓN
# ============================================================

# Valores esperados con Circuits
est_circuits = ejecutar_valores_esperados_shots(
    problema=problema,
    tamaño=tamaño,
    k=k,
    n_shots=n_shots,
    seed = seed,
    CUNQA="Circuits",
    family_name=family_name_circuits
)


# Valores exactos (Simulation)
exact_sim = ejecutar_valores_esperados_shots(
    problema=problema,
    tamaño=tamaño,
    k=k,
    n_shots=1,
    seed = seed,
    CUNQA="Simulation"
)


# Convertimos los resultados a arrays
values_circ = np.array([est_circuits[i] for i in sorted(est_circuits.keys())])
values_sim  = np.array([exact_sim[i] for i in sorted(exact_sim.keys())])

# Calculamos automáticamente todas las métricas
metricas = calcular_metricas(values_circ, values_sim)

# Guardamos en JSON
guardar_resultados_json(
    tamaño=tamaño,
    k=k,
    shots=n_shots,
    seed=seed,
    result_dict=metricas
)


print("\n✔ Experimento finalizado")