#!/usr/bin/env python3
# plot_tsp_results.py
# Genera gráficos TSP separados por algoritmo a partir de TSP_results.db

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

DB_NAME = "TSP_results.db"
FIG_DIR = "Images"
os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------------------------------
# LEER DATOS DE LA BD
# ---------------------------------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
SELECT
    instance,
    optimizer,
    mejora_initial,
    mejora_refined,
    mean_initial,
    std_initial
FROM TSP_results
ORDER BY optimizer, CAST(SUBSTR(instance, 4) AS INTEGER)
""")

rows = c.fetchall()
conn.close()

if not rows:
    print("❌ No se encontraron datos en la base TSP_results.db")
    exit(1)

# ---------------------------------------------------
# AGRUPAR POR ALGORITMO
# ---------------------------------------------------
data_por_algoritmo = defaultdict(lambda: {
    "instances": [],
    "mejora_initial": [],
    "mejora_refined": [],
    "mean_initial": [],
    "std_initial": []
})

for inst, opt, mi, mr, mean_i, std_i in rows:
    d = data_por_algoritmo[opt]
    d["instances"].append(inst)
    d["mejora_initial"].append(mi if mi is not None else np.nan)
    d["mejora_refined"].append(mr if mr is not None else np.nan)
    d["mean_initial"].append(mean_i)
    d["std_initial"].append(std_i)

# ---------------------------------------------------
# FUNCIONES DE GRAFICADO
# ---------------------------------------------------
def graficar_mejoras(instances, mejoras, titulo, nombre_figura, color):
    plt.figure(figsize=(10, 5))

    x = np.arange(len(instances))
    labels = [i.replace("tsp", "") for i in instances]

    plt.bar(x, mejoras, color=color)
    plt.ylabel("Mejora porcentual (%)")
    plt.title(titulo)
    plt.xticks(x, labels, rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()



def graficar_media_std(instances, media, std, titulo, nombre_figura, color):
    plt.figure(figsize=(10, 5))

    x = np.arange(len(instances))
    labels = [i.replace("tsp", "") for i in instances]

    plt.bar(x, media, yerr=std, capsize=5, color=color)
    plt.ylabel("Distancia inicial promedio")
    plt.title(titulo)
    plt.xticks(x, labels, rotation=45)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()


# ---------------------------------------------------
# GENERAR GRAFICAS (UNA POR ALGORITMO)
# ---------------------------------------------------

COLOR_MEJORA_INITIAL = "steelblue"
COLOR_MEJORA_REFINED = "steelblue"
COLOR_MEDIA_STD = "darkorange"

for opt, d in data_por_algoritmo.items():

    print(f"📊 Generando gráficas para {opt}")

    graficar_mejoras(
        d["instances"],
        d["mejora_initial"],
        f"{opt} – Mejora porcentual del mejor initial_distance vs Benchmark - k=4",
        f"{opt}_mejora_best_initial.png",
        COLOR_MEJORA_INITIAL
    )

    graficar_mejoras(
        d["instances"],
        d["mejora_refined"],
        f"{opt} – Mejora porcentual del refined_distance vs Benchmark - k=4",
        f"{opt}_mejora_refined.png",
        COLOR_MEJORA_REFINED
    )

    graficar_media_std(
        d["instances"],
        d["mean_initial"],
        d["std_initial"],
        f"{opt} – Media y desviación típica de initial_distance - k=4",
        f"{opt}_media_std_initial.png",
        COLOR_MEDIA_STD
    )
