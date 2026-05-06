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
C = 1.0  # siempre fijo

# Valores de barrido razonables según discusión
# Barrido “raro” para probar penalizaciones
A_list = np.array([100.0, 250.0, 500.0])       # valores grandes
B_list = np.array([10.0, 50.0])         # valores pequeños
D_list = np.array([200.0, 400.0, 600.0])       # valores grandes
alpha_list = np.array([1.0, 3.0, 6.0, 9.0, 12.0])  # rangos típicos de alpha

num_repeticiones = 1

combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)

# =====================
# CREAR CARPETA EXPERIMENTOS
# =====================
m_val = Tamaño[0]
fecha_hora = datetime.now().strftime("%d_%m_%Y_%H_%M")
base_dir = Path(f"./Experimentos/m_{m_val}/{fecha_hora}")
base_dir.mkdir(parents=True, exist_ok=True)
print(f"Resultados se guardarán en: {base_dir}")

# =====================
# GRID DE α × A × B × D + REPETICIONES
# =====================
grid = list(product(alpha_list, A_list, B_list, D_list))
total_tasks = len(grid) * num_repeticiones

# =====================
# ID de job array SLURM
# =====================
idx = int(os.getenv("SLURM_ARRAY_TASK_ID", -1))
if idx < 0:
    raise RuntimeError("Este script debe ejecutarse mediante un job array de SLURM.")

if idx >= total_tasks:
    print(f"Tarea {idx} fuera del rango total ({total_tasks})")
    sys.exit(0)

# Determinar combinación y repetición
combo_idx = idx // num_repeticiones
rep_idx   = idx % num_repeticiones
alpha, A, B, D = grid[combo_idx]

alpha = float(alpha)
A = float(A)
B = float(B)
D = float(D)

print(f"\n🚀 Ejecutando alpha={alpha}, A={A}, B={B}, D={D}, repetición {rep_idx+1}/{num_repeticiones}")

# =====================
# EJECUTAR PARA TODAS LAS COMBINACIONES (Problema, Tamaño, Optimiz, k)
# =====================
for combo in combinaciones:
    k_val = combo[3]
    m_val = combo[1]

    # Carpeta destino por combinación
    k_dir = base_dir / f"k_{k_val}"
    ab_dir = k_dir / f"alpha_{alpha}_A_{A}_B_{B}_D_{D}"
    ab_dir.mkdir(parents=True, exist_ok=True)

    # Ejecutar experimento
    ruta_csv, ruta_csv_iter = ejecutar_experimentos(
        exp_list=combo,
        optimizer_params=optimizer_params,
        alpha=alpha,
        beta=1.0,   # mantenemos beta fijo, se puede ignorar
        A=A,
        B=B,
        D=D,
        maxiter=maxiter,
        n_shots=n_shots,
        nqpus=None,
        cunqa_str="Simulation",
        family_name=None,
        output_dir=str(ab_dir)
    )

    graficar_coste(ruta_csv_iter)

    print(f"✔ Finalizado combo={combo} para alpha={alpha}, A={A}, B={B}, D={D}, repetición {rep_idx+1}")
