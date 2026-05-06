#!/usr/bin/env python3
# graph_multi.py
# Genera gráficas TSP comparando múltiples k y benchmark

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
DB_FILES = {
    2: "TSP_results_2.db",
    3: "TSP_results_3.db",
    4: "TSP_results_4.db",
}

FIG_DIR = "Images"
os.makedirs(FIG_DIR, exist_ok=True)

BAR_WIDTH = 0.2

COLORS_K = {
    2: "steelblue",
    3: "seagreen",
    4: "indianred",
}

# ---------------------------------------------------
# BENCHMARK (óptimo conocido)
# ---------------------------------------------------
BENCHMARK = {
    "tsp4": 6700,
    "tsp5": 6786,
    "tsp6": 9815,
    "tsp7": 7245,
    "tsp8": 2794,
    "tsp9": 2438,
    "tsp10": 3155,
    "tsp15": 5268,
    "tsp22": 13005,
    "tsp25": 83132,
}

# ---------------------------------------------------
# LEER DATOS DE TODAS LAS BDs
# ---------------------------------------------------
data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

for k, db_name in DB_FILES.items():
    if not os.path.exists(db_name):
        print(f"⚠️ No existe {db_name}, se ignora")
        continue

    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("""
    SELECT
        instance,
        optimizer,
        mejora_initial,
        mejora_refined,
        mean_initial,
        std_initial,
        refined_for_best_initial
    FROM TSP_results
    ORDER BY optimizer, CAST(SUBSTR(instance, 4) AS INTEGER)
    """)

    rows = c.fetchall()
    conn.close()

    for inst, opt, mi, mr, mean_i, std_i, refined_best in rows:
        data[opt][inst][k] = {
            "mejora_initial": mi,
            "mejora_refined": mr,
            "mean_initial": mean_i,
            "std_initial": std_i,
            "refined_best": refined_best,
        }

if not data:
    print("❌ No se encontraron datos")
    exit(1)

# ---------------------------------------------------
# FUNCIONES DE GRAFICADO
# ---------------------------------------------------
def graficar_mejoras(instances, valores_por_k, titulo, nombre_figura):
    plt.figure(figsize=(11, 5))
    x = np.arange(len(instances))

    for i, k in enumerate(DB_FILES.keys()):
        valores = [valores_por_k[inst].get(k, np.nan) for inst in instances]

        plt.bar(
            x + i * BAR_WIDTH,
            valores,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=COLORS_K[k],
        )

    plt.ylabel("Percentage increase (%)")
    plt.title(titulo)
    plt.xticks(
        x + BAR_WIDTH,
        [i.replace("tsp", "") for i in instances],
        rotation=45,
    )
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()


def graficar_media_std(instances, medias_por_k, stds_por_k,
                       titulo, nombre_figura):
    plt.figure(figsize=(11, 5))
    x = np.arange(len(instances))

    for i, k in enumerate(DB_FILES.keys()):
        medias = [medias_por_k[inst].get(k, np.nan) for inst in instances]
        stds = [stds_por_k[inst].get(k, np.nan) for inst in instances]

        plt.bar(
            x + i * BAR_WIDTH,
            medias,
            yerr=stds,
            capsize=4,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=COLORS_K[k],
        )

    benchmark_vals = [BENCHMARK.get(inst, np.nan) for inst in instances]

    plt.bar(
        x + len(DB_FILES) * BAR_WIDTH,
        benchmark_vals,
        width=BAR_WIDTH,
        label="Benchmark",
        color="grey",
    )

    plt.ylabel("Distance")
    plt.title(titulo)
    plt.xticks(
        x + BAR_WIDTH * (len(DB_FILES) / 2),
        [i.replace("tsp", "") for i in instances],
        rotation=45,
    )
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()


def graficar_refined_best_vs_benchmark(instances, refined_por_k,
                                       titulo, nombre_figura):
    plt.figure(figsize=(11, 5))
    x = np.arange(len(instances))

    for i, k in enumerate(DB_FILES.keys()):
        valores = [refined_por_k[inst].get(k, np.nan) for inst in instances]

        plt.bar(
            x + i * BAR_WIDTH,
            valores,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=COLORS_K[k],
        )

    benchmark_vals = [BENCHMARK.get(inst, np.nan) for inst in instances]

    plt.bar(
        x + len(DB_FILES) * BAR_WIDTH,
        benchmark_vals,
        width=BAR_WIDTH,
        label="Benchmark",
        color="grey",
    )

    plt.ylabel("Distance")
    plt.title(titulo)
    plt.xticks(
        x + BAR_WIDTH * (len(DB_FILES) / 2),
        [i.replace("tsp", "") for i in instances],
        rotation=45,
    )
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()

# ---------------------------------------------------
# GENERAR GRÁFICAS
# ---------------------------------------------------
for opt, inst_data in data.items():
    print(f"📊 Generando gráficas para {opt}")

    instances = sorted(
        inst_data.keys(),
        key=lambda x: int(x.replace("tsp", ""))
    )

    mejoras_initial = {
        inst: {k: inst_data[inst][k]["mejora_initial"] for k in inst_data[inst]}
        for inst in instances
    }

    mejoras_refined = {
        inst: {k: inst_data[inst][k]["mejora_refined"] for k in inst_data[inst]}
        for inst in instances
    }

    medias = {
        inst: {k: inst_data[inst][k]["mean_initial"] for k in inst_data[inst]}
        for inst in instances
    }

    stds = {
        inst: {k: inst_data[inst][k]["std_initial"] for k in inst_data[inst]}
        for inst in instances
    }

    refined_best = {
        inst: {k: inst_data[inst][k]["refined_best"] for k in inst_data[inst]}
        for inst in instances
    }

    graficar_mejoras(
        instances,
        mejoras_initial,
        f"Simulation | Optimizer: {opt} | Initial percentage increase",
        "TSP_reg_mejora_initial_multi_k.png",
    )

    graficar_mejoras(
        instances,
        mejoras_refined,
        f"Simulation | Optimizer: {opt} | Refined percentage increase",
        "TSP_reg_mejora_refined_multi_k.png",
    )

    graficar_media_std(
        instances,
        medias,
        stds,
        f"Simulation | Optimizer: {opt} | Mean initial distance ",
        "TSP_reg_media_std_initial_multi_k.png",
    )

    graficar_refined_best_vs_benchmark(
        instances,
        refined_best,
        f"Simulation | Optimizer: {opt} | Best refined distance",
        "TSP_reg_refined_best_vs_benchmark_multi_k.png",
    )

print("✅ Todas las gráficas generadas correctamente")
