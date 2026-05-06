#!/usr/bin/env python3
# Barrido de alpha y beta para VRP
import os
import sys
from pathlib import Path
from itertools import product
import numpy as np
from datetime import datetime

# =====================
# PATHS
# =====================
sys.path.append(os.getenv("HOME"))

from cunqa.qutils import qraise, qdrop
from src.exe_experiments import casuistica_experimento, ejecutar_experimentos
from src.grafica_csv import graficar_coste

# =====================
# CONFIGURACIÓN VRP
# =====================
Problema = ["VRP"]
Tamaño = [8]                 # número de vértices / clientes
Instancia = [2]
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [2]

optimizer_params = None
maxiter = 1000
n_shots = 1

# =====================
# BARRIDO DE α y β
# =====================
alpha_list = np.arange(1.0, 21.0, 1.0)    # α = 1,2,...,20
beta_list  = np.arange(0.2, 1.2, 0.2)     # β = 0.2,0.4,...,1.0

num_repeticiones = 1  # por si quieres repetir cada experimento

# =====================
# GENERAR COMBINACIONES DE EXPERIMENTOS VRP
# =====================
combinaciones_vrp = casuistica_experimento(Problema, Tamaño, Instancia, Optimiz, k)

# =====================
# CARPETA BASE
# =====================
fecha_hora = datetime.now().strftime("%d_%m_%Y_%H_%M")
base_dir = Path(f"./Experimentos/VRP_m_{Tamaño[0]}/inst_{Instancia[0]}/{fecha_hora}")
base_dir.mkdir(parents=True, exist_ok=True)
print(f"📁 Resultados en: {base_dir}")

# =====================
# GRID α × β
# =====================
grid_alpha_beta = list(product(alpha_list, beta_list))
total_tasks = len(grid_alpha_beta) * num_repeticiones

# =====================
# SLURM ARRAY
# =====================
idx = int(os.getenv("SLURM_ARRAY_TASK_ID", -1))
if idx < 0:
    raise RuntimeError("Este script debe ejecutarse con SLURM array.")
if idx >= total_tasks:
    print(f"Tarea {idx} fuera de rango ({total_tasks})")
    sys.exit(0)

combo_idx = idx // num_repeticiones
rep_idx   = idx % num_repeticiones

alpha, beta = grid_alpha_beta[combo_idx]

print(f"\n🚀 SLURM_TASK_ID={idx}: α={alpha}, β={beta}, rep {rep_idx+1}/{num_repeticiones}")

# =====================
# EJECUCIÓN DE EXPERIMENTOS
# =====================
for combo in combinaciones_vrp:
    problema, tamaño, instancia, optimizer, k_val = combo

    # Carpeta específica para este experimento
    exp_dir = base_dir / f"k_{k_val}" / f"alpha_{alpha}_beta_{beta}"
    exp_dir.mkdir(parents=True, exist_ok=True)

    print(f"\n⚡ Ejecutando combo={combo} en {exp_dir}")

    cluster_csv_paths, cluster_csv_iter_paths = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=float(alpha),
        beta=float(beta),
        maxiter=maxiter,
        n_shots=n_shots,
        nqpus=None,
        cunqa_str="Simulation",
        family_name=None,
        output_dir=str(exp_dir)  # aquí se propaga output_dir para JSON y CSV
    )

    # Graficar resultados iterativos por cluster
    for csv_iter in cluster_csv_iter_paths:
        graficar_coste(csv_iter)

    print(f"✔ Finalizado combo={combo}")
