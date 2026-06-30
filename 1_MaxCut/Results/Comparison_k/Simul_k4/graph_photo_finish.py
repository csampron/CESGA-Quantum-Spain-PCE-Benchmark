import sqlite3
import matplotlib.pyplot as plt
import os
import numpy as np
from collections import defaultdict

# === CONFIGURACIÓN ===
DB_NAME = "MaxCut_results.db"
OUTPUT_DIR = "Your_route/z_MaxCut/A_DIFFERENTIAL_COMPARISON/Comparison_k/Simul_k4"

# === DIRECTORIO DE IMÁGENES ===
IMAGES_DIR = os.path.join(OUTPUT_DIR, "Images")
os.makedirs(IMAGES_DIR, exist_ok=True)

# === LEER BASE DE DATOS ===
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()
c.execute("""
    SELECT filename, r, r_media, desviacion_sol, n_ejecuciones
    FROM MaxCut_results
""")
rows = c.fetchall()
conn.close()

# === VALORES EXACTOS ===
EXACT_SOLUTIONS = {
    10: 25, 
    20: 97, 
    40: 355, 
    50: 602, 
    60: 852,
    100: 2224, 
    150: 4899, 
    200: 8717, 
    250: 13460, 
    300: 19267
}

# === ORGANIZAR DATOS ===
data_dict = defaultdict(list)

for filename, r, r_media, desviacion_sol, n_ejecuciones in rows:

    parts = filename.replace("Simulation_MaxCut_", "").replace(".json", "").split("_")
    if len(parts) != 3:
        continue

    n = int(parts[0])
    optimizador = parts[1]
    k = int(parts[2])

    if n not in EXACT_SOLUTIONS:
        continue

    sol_exact = EXACT_SOLUTIONS[n]

    # Desviación del ratio (σ / sol_exact)
    desviacion_r_media = desviacion_sol / sol_exact if sol_exact else 0

    data_dict[(optimizador, k)].append(
        (n, r, r_media, desviacion_r_media)
    )

# === GRAFICAR ===
for optimizador in ["DIFFERENTIALEVOLUTION"]:
    
    plt.figure(figsize=(9, 5))

    key = (optimizador, 4)  # k=4
    data = data_dict.get(key, [])

    if not data:
        print(f"No hay datos para {optimizador}, k=4")
        continue

    # Ordenar por número de nodos
    data.sort(key=lambda x: x[0])

    n_vals = [d[0] for d in data]
    r_vals = [d[1] for d in data]
    r_media_vals = [d[2] for d in data]
    r_media_std = [d[3] for d in data]

    # === Mejor solución (verde oscuro)
    plt.plot(
        n_vals, 
        r_vals, 
        'o', 
        linewidth=2, 
        markersize=6,
        color="#006d2c",   # verde oscuro
        label=r'$r$ (Best solution)'
    )

    # === Media con error (verde claro)
    plt.errorbar(
        n_vals, 
        r_media_vals, 
        yerr=r_media_std,
        fmt='s',
        linewidth=2,
        markersize=6,
        capsize=4,
        color="#a1d99b",   # verde claro
        label=r'$\bar{r} \pm \mathrm{std}$'
    )

    # Línea 16/17
    r_barra = 16 / 17
    plt.axhline(
        y=r_barra, 
        linestyle='--', 
        linewidth=1, 
        color='red', 
        label=r'$r_{HD} = 16/17$'
    )
    plt.axhline(
        y=1, 
        linestyle='--', 
        linewidth=1, 
        color='green'
    )

    # === Estilo
    plt.xlabel("Number of nodes")
    plt.ylabel("Solution approximation ratio")
    plt.title(f"Simulation | Optimizer: {optimizador} | k=4")
    plt.grid(True, linestyle=':')
    plt.legend()

    # Zoom
    plt.ylim(0.7, 1.1)

    plt.tight_layout()

    output_path = os.path.join(
        IMAGES_DIR, 
        f"MaxCut_grafico_r_{optimizador}_k4.png"
    )
    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"✅ Gráfico guardado: {output_path}")

print("\n📊 Gráficas generadas correctamente.")