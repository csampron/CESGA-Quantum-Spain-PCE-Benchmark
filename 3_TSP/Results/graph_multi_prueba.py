#!/usr/bin/env python3
# graph_multi_compare.py

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
DB_FILES_NO_REG = {
    2: "Comparison_k/TSP_results_2.db",
    3: "Comparison_k/TSP_results_3.db",
    4: "Comparison_k/TSP_results_4.db",
}

DB_FILES_REG = {
    2: "Comparison_reg/TSP_results_2.db",
    3: "Comparison_reg/TSP_results_3.db",
    4: "Comparison_reg/TSP_results_4.db",
}

FIG_DIR = "Images_comparison_2"
os.makedirs(FIG_DIR, exist_ok=True)

BAR_WIDTH = 0.18

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

EDGE_COLOR = "black"
LINE_WIDTH = 0.8

BENCHMARK = {
    "tsp4": 6700, "tsp5": 6786, "tsp6": 9815,
    "tsp7": 7245, "tsp8": 2794, "tsp9": 2438,
    "tsp10": 3155, "tsp15": 5268,
    "tsp22": 13005, "tsp25": 83132,
}

# ---------------------------------------------------
# CARGA DE DATOS
# ---------------------------------------------------
def cargar_datos(db_files):
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for k, db_name in db_files.items():
        if not os.path.exists(db_name):
            print(f"⚠️ No existe {db_name}")
            continue

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute("""
        SELECT instance, optimizer,
               mejora_initial, mejora_refined,
               mean_initial, std_initial,
               refined_for_best_initial
        FROM TSP_results
        """)

        for inst, opt, mi, mr, mean_i, std_i, refined_best in c.fetchall():
            data[opt][inst][k] = {
                "mejora_initial": mi,
                "mejora_refined": mr,
                "mean_initial": mean_i,
                "std_initial": std_i,
                "refined_best": refined_best,
            }

        conn.close()

    return data


data_no = cargar_datos(DB_FILES_NO_REG)
data_reg = cargar_datos(DB_FILES_REG)

# ---------------------------------------------------
# FUNCIONES AUXILIARES
# ---------------------------------------------------
def limpiar_leyenda():
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(
        by_label.values(),
        by_label.keys(),
        loc='center left',
        bbox_to_anchor=(1, 0.5),
        frameon=True
    )

def get_offset(idx, group_width):
    return -group_width/2 + idx * BAR_WIDTH

# ---------------------------------------------------
# GENERACIÓN DE GRÁFICAS
# ---------------------------------------------------
for opt in sorted(set(data_no) & set(data_reg)):

    print(f"📊 {opt}")

    instancias = sorted(
        set(data_no[opt]) | set(data_reg[opt]),
        key=lambda x: int(x.replace("tsp", ""))
    )

    n_k = len(DB_FILES_NO_REG)
    n_barras = n_k * 2 + 1
    GROUP_WIDTH = n_barras * BAR_WIDTH

    x = np.arange(len(instancias)) * (GROUP_WIDTH + 0.5)

    # =================================================
    # 1. MEJORA INITIAL
    # =================================================
    plt.figure(figsize=(12, 4))

    for i, k in enumerate(DB_FILES_NO_REG):
        base = i * 2

        vals_no = [data_no[opt][inst].get(k, {}).get("mejora_initial", np.nan) for inst in instancias]
        vals_reg = [data_reg[opt][inst].get(k, {}).get("mejora_initial", np.nan) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k],
                label=f"k={k} (No reg)")

        plt.bar(
            x + get_offset(base + 1, GROUP_WIDTH),
            vals_reg,
            width=BAR_WIDTH,
            color=COLORS_K[k],
            hatch="//",
            alpha=0.8,
            edgecolor=EDGE_COLOR,
            linewidth=LINE_WIDTH,
            label=f"k={k} (Reg)"
        )

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Initial improvement")
    plt.ylabel("%")
    plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

    limpiar_leyenda()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.savefig(f"{FIG_DIR}/compare_mejora_initial.png",
                bbox_inches='tight', dpi=200)
    plt.close()

    # =================================================
    # 2. MEJORA REFINED
    # =================================================
    plt.figure(figsize=(12, 4))

    for i, k in enumerate(DB_FILES_NO_REG):
        base = i * 2

        vals_no = [data_no[opt][inst].get(k, {}).get("mejora_refined", np.nan) for inst in instancias]
        vals_reg = [data_reg[opt][inst].get(k, {}).get("mejora_refined", np.nan) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k],
                label=f"k={k} (No reg)")

        plt.bar(
            x + get_offset(base + 1, GROUP_WIDTH),
            vals_reg,
            width=BAR_WIDTH,
            color=COLORS_K[k],
            hatch="//",
            alpha=0.8,
            edgecolor=EDGE_COLOR,
            linewidth=LINE_WIDTH,
            label=f"k={k} (Reg)"
        )

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Refined improvement")
    plt.ylabel("%")
    plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

    limpiar_leyenda()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.savefig(f"{FIG_DIR}/compare_mejora_refined.png",
                bbox_inches='tight', dpi=200)
    plt.close()

    # =================================================
    # 3. MEDIA + STD
    # =================================================
    plt.figure(figsize=(12, 4))

    benchmark_vals = [BENCHMARK.get(inst, np.nan) for inst in instancias]

    plt.bar(x + get_offset(0, GROUP_WIDTH), benchmark_vals,
            width=BAR_WIDTH, color="grey", label="Benchmark")

    for i, k in enumerate(DB_FILES_NO_REG):
        base = 1 + i * 2

        medias_no = [data_no[opt][inst].get(k, {}).get("mean_initial", np.nan) for inst in instancias]
        medias_reg = [data_reg[opt][inst].get(k, {}).get("mean_initial", np.nan) for inst in instancias]

        stds_no = [data_no[opt][inst].get(k, {}).get("std_initial", np.nan) for inst in instancias]
        stds_reg = [data_reg[opt][inst].get(k, {}).get("std_initial", np.nan) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), medias_no,
                width=BAR_WIDTH, color=COLORS_K[k],
                yerr=stds_no, capsize=5,
                error_kw={"elinewidth": 0.8, "ecolor": "black"},
                label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), medias_reg,
                width=BAR_WIDTH, color=COLORS_K[k],
                yerr=stds_reg, capsize=5,
                error_kw={"elinewidth": 0.8, "ecolor": "black"},
                hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR,
                linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Mean initial distance")
    plt.ylabel("Distance")
    plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

    limpiar_leyenda()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.savefig(f"{FIG_DIR}/compare_media_std.png",
                bbox_inches='tight', dpi=200)
    plt.close()

    # =================================================
    # 4. BEST VS BENCHMARK
    # =================================================
    plt.figure(figsize=(12, 4))

    plt.bar(x + get_offset(0, GROUP_WIDTH), benchmark_vals,
            width=BAR_WIDTH, color="grey", label="Benchmark")

    for i, k in enumerate(DB_FILES_NO_REG):
        base = 1 + i * 2

        vals_no = [data_no[opt][inst].get(k, {}).get("refined_best", np.nan) for inst in instancias]
        vals_reg = [data_reg[opt][inst].get(k, {}).get("refined_best", np.nan) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k],
                label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg,
                width=BAR_WIDTH, color=COLORS_K[k],
                hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR,
                linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Best refined vs benchmark")
    plt.ylabel("Distance")
    plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

    limpiar_leyenda()
    plt.grid(True, linestyle="--", alpha=0.5)

    plt.savefig(f"{FIG_DIR}/compare_refined_best.png",
                bbox_inches='tight', dpi=200)
    plt.close()

print("✅ Comparación completada")