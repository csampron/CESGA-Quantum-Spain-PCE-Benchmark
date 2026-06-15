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

# =====================
# CONFIGURACIÓN TSP
# =====================
Problema = ["TSP"]
Tamaño = [22]
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [3]

optimizer_params = None
maxiter = 2500
n_shots = 1

# =====================
# BARRIDO DE PARÁMETROS
# =====================
alpha_list = np.array([45.0, 50.0, 60.0])
beta_list  = np.array([0.4, 0.8])

A_1_list = np.array([15.0, 25.0])
A_2_list = np.array([5.0, 10.0])

gamma = 1.0

num_repeticiones = 3

combinaciones = casuistica_experimento(
    Problema,
    Tamaño,
    Optimiz,
    k
)

# =====================
# CARPETA BASE
# =====================
m_val = Tamaño[0]
default_run_id = datetime.now().strftime("%d_%m_%Y_%H_%M")

base_dir = Path(
    os.getenv(
        "EXP_BASE_DIR",
        f"./Experimentos/TSP_m_{m_val}/run_{default_run_id}"
    )
)

print(f"📁 Resultados en: {base_dir}")

# =====================
# GRID alpha × beta × A_1 × A_2
# =====================
grid = list(product(
    alpha_list,
    beta_list,
    A_1_list,
    A_2_list
))

total_tasks = len(grid) * num_repeticiones

print(total_tasks)

print(f"Total combinaciones: {len(grid)}")
print(f"Total tareas SLURM: {total_tasks}")

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

alpha, beta, A_1, A_2 = grid[combo_idx]

alpha = float(alpha)
beta  = float(beta)
A_1   = float(A_1)
A_2   = float(A_2)

print(
    f"\n🚀 alpha={alpha}, beta={beta} "
    f"A_1={A_1}, A_2={A_2}, gamma={gamma}, "
    f"rep {rep_idx + 1}/{num_repeticiones}"
)

#print(
    #f"\n🚀 alpha={alpha}, beta={beta}, "
    #f"A_1={A_1}, A_2={A_2}, gamma={gamma}, "
    #f"rep {rep_idx + 1}/{num_repeticiones}"
#)

# =====================
# EJECUCIÓN
# =====================
for combo in combinaciones:

    k_val = combo[3]

    exp_dir = (
        base_dir
        / f"k_{k_val}"
        / f"alpha_{alpha}_beta_{beta}_A_1_{A_1}_A_2_{A_2}"
    )

    exp_dir.mkdir(parents=True, exist_ok=True)

    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=beta,
        A_1=A_1,
        A_2=A_2,
        gamma=gamma,
        maxiter=maxiter,
        n_shots=n_shots,
        nqpus=None,
        cunqa_str="Simulation",
        family_name=None,
        output_dir=str(exp_dir)
    )

    print(f"✔ Finalizado combo={combo}")