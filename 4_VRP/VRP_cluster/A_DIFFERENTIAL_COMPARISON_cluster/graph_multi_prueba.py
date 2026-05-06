##!/usr/bin/env python3

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ---------------------------------------------------
# CONFIGURACIÓN
# ---------------------------------------------------
DB_FILES_NO_REG = {
    2: "Comparison_k/VRP_results_2.db",
    3: "Comparison_k/VRP_results_3.db",
    4: "Comparison_k/VRP_results_4.db",
}

DB_FILES_REG = {
    2: "Comparison_reg/VRP_results_2.db",
    3: "Comparison_reg/VRP_results_3.db",
    4: "Comparison_reg/VRP_results_4.db",
}

FIG_DIR = "Images_comparison_vrp"
os.makedirs(FIG_DIR, exist_ok=True)

BAR_WIDTH = 0.18

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

EDGE_COLOR = "black"
LINE_WIDTH = 0.8

# ---------------------------------------------------
# BENCHMARK
# ---------------------------------------------------
BENCHMARK = {
    "4_1": 97, "4_2": 121,
    "5_1": 94, "5_2": 295,
    "6_1": 118, "6_2": 122,
    "7_1": 119, "7_2": 164,
    "8_1": 153, "8_2": 269,
}

# ---------------------------------------------------
# MÉTRICAS
# ---------------------------------------------------
def metricas(best, bench, bench_over, penalty=10.0):

    bench_pen = bench + penalty * bench_over

    mejora = (bench - best) / bench * 100
    delta = (best - bench_pen) / bench_pen * 100

    return mejora, delta

# ---------------------------------------------------
# CARGA DATOS
# ---------------------------------------------------
def cargar_datos(db_files):

    data = defaultdict(lambda: defaultdict(dict))

    for k, db_name in db_files.items():

        if not os.path.exists(db_name):
            continue

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        c.execute("""
        SELECT instance, optimizer,
               best_total_cost,
               benchmark_over_capacity,
               mean_total_cost,
               std_total_cost
        FROM VRP_results
        """)

        for inst, opt, best, bench_over, mean, std in c.fetchall():

            if inst not in BENCHMARK:
                continue

            bench = BENCHMARK[inst]
            mejora, delta = metricas(best, bench, bench_over)

            data[opt][inst][k] = {
                "mejora": mejora,
                "delta": delta,
                "mean": mean,
                "std": std,
                "best": best,
                "bench_over": bench_over
            }

        conn.close()

    return data

data_no = cargar_datos(DB_FILES_NO_REG)
data_reg = cargar_datos(DB_FILES_REG)

# ---------------------------------------------------
# UTILIDADES
# ---------------------------------------------------
def limpiar_leyenda(pos="upper left"):
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))
    plt.legend(by_label.values(), by_label.keys(), loc=pos, fontsize=9, frameon=True)

def get_offset(idx, group_width):
    return -group_width / 2 + idx * BAR_WIDTH

def es_factible(dic, inst, k):
    fila = dic[inst].get(k, {})
    return fila.get("bench_over", 0) == 0

def es_infactible(dic, inst, k):
    fila = dic[inst].get(k, {})
    return fila.get("bench_over", 0) > 0

# ---------------------------------------------------
# GRÁFICAS
# ---------------------------------------------------
for opt in sorted(set(data_no) & set(data_reg)):

    print(f"📊 VRP {opt}")

    instancias = sorted(
        set(data_no[opt]) | set(data_reg[opt]),
        key=lambda x: (int(x.split("_")[0]), int(x.split("_")[1]))
    )

    n_k = len(DB_FILES_NO_REG)
    n_barras = n_k * 2 + 1
    GROUP_WIDTH = n_barras * BAR_WIDTH

    x = np.arange(len(instancias)) * (GROUP_WIDTH + 0.5)

    # =================================================
    # 1. MEJORA FACTIBLES
    # =================================================
    plt.figure(figsize=(12, 5))

    for i, k in enumerate(DB_FILES_NO_REG):

        base = i * 2

        vals_no = []
        vals_reg = []

        for inst in instancias:

            if es_factible(data_no[opt], inst, k):
                vals_no.append(data_no[opt][inst].get(k, {}).get("mejora", np.nan))
            else:
                vals_no.append(np.nan)

            if es_factible(data_reg[opt], inst, k):
                vals_reg.append(data_reg[opt][inst].get(k, {}).get("mejora", np.nan))
            else:
                vals_reg.append(np.nan)

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k], label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg,
                width=BAR_WIDTH, color=COLORS_K[k],
                hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Factibles improvement")
    plt.ylabel("% mejora")
    plt.xticks(x, instancias, rotation=45)
    limpiar_leyenda("upper right")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/VRP_mejora_factibles.png")
    plt.close()

    # =================================================
    # 2. DELTA INFACTIBLES
    # =================================================
    plt.figure(figsize=(12, 5))

    for i, k in enumerate(DB_FILES_NO_REG):

        base = i * 2

        vals_no = []
        vals_reg = []

        for inst in instancias:

            if es_infactible(data_no[opt], inst, k):
                vals_no.append(data_no[opt][inst].get(k, {}).get("delta", np.nan))
            else:
                vals_no.append(np.nan)

            if es_infactible(data_reg[opt], inst, k):
                vals_reg.append(data_reg[opt][inst].get(k, {}).get("delta", np.nan))
            else:
                vals_reg.append(np.nan)

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k], label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg,
                width=BAR_WIDTH, color=COLORS_K[k],
                hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Infactibles delta cost")
    plt.ylabel("Delta coste")
    plt.xticks(x, instancias, rotation=45)
    limpiar_leyenda("upper left")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/VRP_delta_infactibles.png")
    plt.close()

    # =================================================
    # 3. MEDIA + STD
    # =================================================
    plt.figure(figsize=(12, 5))

    bench_vals = [BENCHMARK.get(inst, np.nan) for inst in instancias]

    plt.bar(x + get_offset(0, GROUP_WIDTH), bench_vals,
            width=BAR_WIDTH, color="grey", label="Benchmark")

    for i, k in enumerate(DB_FILES_NO_REG):

        base = 1 + i * 2

        medias_no = [data_no[opt][inst].get(k, {}).get("mean", np.nan) for inst in instancias]
        medias_reg = [data_reg[opt][inst].get(k, {}).get("mean", np.nan) for inst in instancias]

        std_no = [data_no[opt][inst].get(k, {}).get("std", 0.0) for inst in instancias]
        std_reg = [data_reg[opt][inst].get(k, {}).get("std", 0.0) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), medias_no, yerr=std_no,
                capsize=3, width=BAR_WIDTH,
                color=COLORS_K[k], label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), medias_reg, yerr=std_reg,
                capsize=3, width=BAR_WIDTH,
                color=COLORS_K[k], hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Mean total cost")
    plt.ylabel("Coste total")
    plt.xticks(x, instancias, rotation=45)
    limpiar_leyenda("upper left")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/VRP_media_std.png")
    plt.close()

    # =================================================
    # 4. BEST VS BENCHMARK
    # =================================================
    plt.figure(figsize=(12, 5))

    plt.bar(x + get_offset(0, GROUP_WIDTH), bench_vals,
            width=BAR_WIDTH, color="grey", label="Benchmark")

    for i, k in enumerate(DB_FILES_NO_REG):

        base = 1 + i * 2

        vals_no = [data_no[opt][inst].get(k, {}).get("best", np.nan) for inst in instancias]
        vals_reg = [data_reg[opt][inst].get(k, {}).get("best", np.nan) for inst in instancias]

        plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no,
                width=BAR_WIDTH, color=COLORS_K[k], label=f"k={k} (No reg)")

        plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg,
                width=BAR_WIDTH, color=COLORS_K[k],
                hatch="//", alpha=0.8,
                edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)")

    plt.title(f"Simulation | Optimizer: {opt} | k=2,3,4 | Best solution vs Benchmark")
    plt.ylabel("Coste")
    plt.xticks(x, instancias, rotation=45)
    limpiar_leyenda("upper left")
    plt.grid(True, linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.savefig(f"{FIG_DIR}/VRP_best_vs_benchmark.png")
    plt.close()

print("✅ VRP comparison corrected")