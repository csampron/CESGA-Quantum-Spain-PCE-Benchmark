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
# CONFIGURACIÓN TSP
# =====================
Problema = ["TSP"]
Tamaño = [15]                         # número de ciudades
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [2]

optimizer_params = None
maxiter = 1000
n_shots = 1

# =====================
# BARRIDO DE PARÁMETROS
# =====================
alpha_list = np.arange(1, 21, 1)
beta_list  = np.array([1.0])              # fijo o barrido suave
A_list     = np.array([10.0, 50.0, 100.0, 500.0])
B_list     = np.array([1.0])

num_repeticiones = 1

combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)

# =====================
# CARPETA BASE
# =====================
m_val = Tamaño[0]
fecha_hora = datetime.now().strftime("%d_%m_%Y_%H_%M")
base_dir = Path(f"./Experimentos/TSP_m_{m_val}/{fecha_hora}")
base_dir.mkdir(parents=True, exist_ok=True)

print(f"📁 Resultados en: {base_dir}")

# =====================
# GRID α × β × A × B
# =====================
#grid = list(product(alpha_list, beta_list, A_list, B_list))

grid = list(product(alpha_list, A_list))

total_tasks = len(grid) * num_repeticiones

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

alpha, A = grid[combo_idx]

alpha = float(alpha)
beta  = float(beta_list[0])
A     = float(A)
B     = float(B_list[0])

print(f"\n🚀 alpha={alpha}, beta={beta}, A={A}, B={B}, rep {rep_idx+1}/{num_repeticiones}")

# =====================
# EJECUCIÓN
# =====================
for combo in combinaciones:
    k_val = combo[3]

    exp_dir = (
        base_dir
        / f"k_{k_val}"
        / f"alpha_{alpha}_A_{A}"
        #/ f"alpha_{alpha}_beta_{beta}_A_{A}_B_{B}"
    )
    exp_dir.mkdir(parents=True, exist_ok=True)

    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=beta,
        A=A,
        B=B,
        maxiter=maxiter,
        n_shots=n_shots,
        nqpus=None,
        cunqa_str="Simulation",
        family_name=None,
        output_dir=str(exp_dir)
    )

    if ruta_csv_iter is not None:
        graficar_coste(ruta_csv_iter)

    print(f"✔ Finalizado combo={combo}")
