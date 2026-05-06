import os
import sys
from pathlib import Path
from itertools import product
import numpy as np
from datetime import datetime

# Añadir el path a tu carpeta HOME donde están tus módulos
sys.path.append(os.getenv("HOME"))

# Importación de funciones principales de Cunqa
from cunqa.qutils import qraise, qdrop
from src.exe_experiments import casuistica_experimento, ejecutar_experimentos
from src.auxiliar import num_qubits
from src.grafica_csv import graficar_coste

# =====================
# CONFIGURACIÓN DE EXPERIMENTOS
# =====================
Problema = ["BPP"]
Tamaño = [6]
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [2]

optimizer_params = None
maxiter = 1000
n_shots = 1

# =====================
# PARÁMETROS DEL BARRIDO
# =====================
#alpha_list = np.arange(1, 5, 1).astype(float)   # 1,2,3,4
#alpha_list = np.arange(5, 9, 1).astype(float)   # 5,6,7,9
alpha_list = np.arange(9, 13, 1).astype(float)  # 9,10,11,12

beta_list  = np.array([0.2, 0.4, 0.6, 0.8, 1.0]) 

B_FIJO = 8000.0          # ← B se queda fijo
num_repeticiones = 3

combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)

# =====================
# CREAR CARPETA EXPERIMENTOS
# =====================
m_val = Tamaño[0]
fecha_hora = datetime.now().strftime("%d_%m_%Y_%H_%M")

base_dir = Path(f"./Experimentos/m_{m_val}/{fecha_hora}")
base_dir.mkdir(parents=True, exist_ok=True)
print(f"📂 Resultados se guardarán en: {base_dir}")

# =====================
# JOB ARRAY SLURM
# =====================
idx = int(os.getenv("SLURM_ARRAY_TASK_ID", -1))
if idx < 0:
    raise RuntimeError("Este script debe ejecutarse mediante un job array de SLURM.")

# =====================
# GRID α × β + REPETICIONES
# =====================
grid = list(product(alpha_list, beta_list))
total_tasks = len(grid) * num_repeticiones

if idx >= total_tasks:
    print(f"Tarea {idx} fuera del rango total ({total_tasks})")
    sys.exit(0)

combo_idx = idx // num_repeticiones
rep_idx   = idx % num_repeticiones

alpha, beta = grid[combo_idx]

print(
    f"\n🚀 Ejecutando alpha={alpha}, beta={beta}, "
    f"B={B_FIJO}, repetición {rep_idx+1}/{num_repeticiones}"
)

# =====================
# EJECUTAR EXPERIMENTOS
# =====================
for combo in combinaciones:
    k_val = combo[3]
    m_val = combo[1]

    # Carpeta destino
    k_dir = base_dir / f"k_{k_val}"
    ab_dir = k_dir / f"alpha_{alpha}_beta_{beta}"
    ab_dir.mkdir(parents=True, exist_ok=True)

    # Ejecutar experimento
    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=beta,          # ← AHORA BARRIDO REAL
        maxiter=maxiter,
        n_shots=n_shots,
        nqpus=None,
        cunqa_str="Simulation",
        family_name=None,
        output_dir=str(ab_dir)
    )

    graficar_coste(ruta_csv_iter)

    print(
        f"✔ Finalizado combo={combo} "
        f"para alpha={alpha}, beta={beta}, rep {rep_idx+1}"
    )

