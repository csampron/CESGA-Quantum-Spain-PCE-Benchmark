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
Problema = ["VRP"]
Tamaño = [7]
Instancia = [1]
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [2]


optimizer_params = None
maxiter = 1000
n_shots = 1

# =====================
# BARRIDO DE PARÁMETROS
# =====================
alpha_list = np.arange(1, 3, 1)
#alpha_list = np.arange(3, 5, 1)
#alpha_list = np.arange(5, 7, 1)
#alpha_list = np.arange(7, 9, 1)
#alpha_list = np.arange(9, 11, 1)

beta_list  = np.array([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])              # fijo o barrido suave


num_repeticiones = 3

combinaciones = casuistica_experimento(Problema, Tamaño, Instancia, Optimiz, k)

# =====================
# CARPETA BASE
# =====================
m_val = Tamaño[0]
inst_val = Instancia[0]

fecha_hora = datetime.now().strftime("%d_%m_%Y_%H_%M")
base_dir = Path(f"./Experimentos/VRP_m_{m_val}_inst_{inst_val}/{fecha_hora}")
base_dir.mkdir(parents=True, exist_ok=True)

print(f"📁 Resultados en: {base_dir}")

# =====================
# GRID α × β × A × B
# =====================
grid = list(product(alpha_list, beta_list))

#grid = list(product(alpha_list, A_list))

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

alpha, beta = grid[combo_idx]

alpha = float(alpha)
beta  = float(beta)

print(f"\n🚀 alpha={alpha}, beta={beta}, rep {rep_idx+1}/{num_repeticiones}")

# =====================
# EJECUCIÓN
# =====================
for combo in combinaciones:
    k_val = combo[4]

    exp_dir = (
        base_dir
        / f"k_{k_val}"
        / f"alpha_{alpha}_beta_{beta}"
        #/ f"alpha_{alpha}_beta_{beta}_A_{A}_B_{B}"
    )
    exp_dir.mkdir(parents=True, exist_ok=True)

    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=beta,
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
