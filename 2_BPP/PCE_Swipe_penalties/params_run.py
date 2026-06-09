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
# CONFIGURACIÓN BPP
# =====================
Problema = ["BPP"]
Tamaño = [12]                         # número de ciudades
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [3]

optimizer_params = None
maxiter = 2500
n_shots = 1

# =====================
# BARRIDO DE PARÁMETROS
# =====================

#alpha_list = np.array([10.0])
#alpha_list = np.array([15.0])
#alpha_list = np.array([20.0])
#alpha_list = np.array([25.0])
#alpha_list = np.array([30.0])
#alpha_list = np.array([35.0])
#alpha_list = np.array([40.0])


beta_list  = np.array([0.0, 0.5])    # fijo o barrido suave


lambda_1_list   = np.array([1.0])

lambda_2_list = np.array([50.0, 100.0, 150.0])

lambda_3_list = np.array([100.0, 150.0, 250.0])

num_repeticiones = 3

combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)

# =====================
# CARPETA BASE
# =====================
m_val = Tamaño[0]

default_run_id = datetime.now().strftime("%d_%m_%Y_%H_%M")

base_dir = Path(
    os.getenv(
        "EXP_BASE_DIR",
        f"./Experimentos/BPP_m_{m_val}/run_{default_run_id}"
    )
)

base_dir.mkdir(parents=True, exist_ok=True)
print(f"📁 Resultados en: {base_dir}")

# =====================
# GRID α × β × A × B
# =====================
#grid = list(product(alpha_list, beta_list, A_list, B_list))

grid = [
    (alpha, beta, lambda_2, lambda_3)
    for alpha, beta, lambda_2, lambda_3
    in product(alpha_list, beta_list, lambda_2_list, lambda_3_list)
    if lambda_3 >= lambda_2
]


total_tasks = len(grid) * num_repeticiones

print(total_tasks)

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

alpha, beta, lambda_2, lambda_3 = grid[combo_idx]

alpha = float(alpha)
beta  = float(beta)
lambda_1   = float(lambda_1_list[0])
lambda_2   = float(lambda_2)
lambda_3   = float(lambda_3)

print(f"\n🚀 alpha={alpha}, beta={beta}, lambda_1={lambda_1}, lambda_2={lambda_2}, lambda_3={lambda_3}, rep {rep_idx+1}/{num_repeticiones}")

# =====================
# EJECUCIÓN
# =====================
for combo in combinaciones:
    k_val = combo[3]

    exp_dir = (
        base_dir
        / f"k_{k_val}"
        / f"alpha_{alpha}_beta_{beta}_lambda_2_{lambda_2}_lambda_3_{lambda_3}"
    )
    exp_dir.mkdir(parents=True, exist_ok=True)

    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=beta,
        lambda_1=lambda_1,
        lambda_2=lambda_2,
        lambda_3=lambda_3,
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
