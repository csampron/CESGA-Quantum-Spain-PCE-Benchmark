import numpy as np
from exe_expectation_values import ejecutar_valores_esperados_shots, calcular_metricas, guardar_resultados_json


family_name_circuits = "family_circuits_MaxCut_10_shots6"
problema = "MaxCut"
tamaño = 10
k = 2
n_shots = 10000000
seed = 33

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
est_circuits, aux_circ = ejecutar_valores_esperados_shots(
    problema=problema,
    tamaño=tamaño,
    k=k,
    n_shots=n_shots,
    seed = seed,
    CUNQA="Circuits",
    family_name=family_name_circuits
)

print(f"Valores esperados simulados: {est_circuits}")

# Valores exactos (Simulation)
exact_sim, aux_sim = ejecutar_valores_esperados_shots(
    problema=problema,
    tamaño=tamaño,
    k=k,
    n_shots=1,
    seed = seed,
    CUNQA="Simulation"
)


print(f"Valores esperados exactos: {exact_sim}")

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