#!/usr/bin/env python3

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ----------------------------
# Configuración
# ----------------------------
DB_FILES = {
    2: "VRP_results_2.db",
    3: "VRP_results_3.db",
    4: "VRP_results_4.db",
}

FIG_DIR = "Images"
os.makedirs(FIG_DIR, exist_ok=True)

BAR_WIDTH = 0.2
COLORS_K = {
    2: "steelblue",
    3: "seagreen",
    4: "indianred",
}

# ----------------------------
# Benchmark VRP
# ----------------------------
benchmark_data = {
    "4_1": {"cost": 97},
    "4_2": {"cost": 121},
    "5_1": {"cost": 94},
    "5_2": {"cost": 295},
    "6_1": {"cost": 118},
    "6_2": {"cost": 122},
    "7_1": {"cost": 119},
    "7_2": {"cost": 164},
    "8_1": {"cost": 153},
    "8_2": {"cost": 269},
}

# ----------------------------
# MÉTRICAS
# ----------------------------
def metricas(best, bench, bench_over, penalty=10):

    bench_pen = bench + penalty * bench_over

    mejora = (bench - best) / bench * 100
    delta = (best - bench_pen) / bench_pen * 100

    return mejora, delta

# ----------------------------
# DATA STRUCTURE
# ----------------------------
data = defaultdict(lambda: defaultdict(dict))

# ----------------------------
# LOAD DATA
# ----------------------------
for k, db_name in DB_FILES.items():

    if not os.path.exists(db_name):
        print(f"⚠️ {db_name} no existe")
        continue

    conn = sqlite3.connect(db_name)
    c = conn.cursor()

    c.execute("""
        SELECT
            instance,
            optimizer,
            best_total_cost,
            benchmark_over_capacity,
            mean_total_cost,
            std_total_cost
        FROM VRP_results
    """)

    for inst, opt, best_total, bench_over, mean_total, std_total in c.fetchall():

        if inst not in benchmark_data:
            continue

        bench = benchmark_data[inst]["cost"]

        mejora, delta = metricas(best_total, bench, bench_over)

        d = data[opt][inst]

        d[k] = {
            "mejora": mejora,
            "delta": delta,
            "mean": mean_total,
            "std": std_total,
            "best_total": best_total,
            "bench_over": bench_over
        }

        d["benchmark"] = bench

    conn.close()

# ----------------------------
# FILTRADO FACTIBLE / INFACTIBLE
# ----------------------------
def instances_factibles(inst_data):
    out = []
    for inst in inst_data:
        ks = [k for k in inst_data[inst] if isinstance(k, int)]
        if any(inst_data[inst][k]["bench_over"] == 0 for k in ks):
            out.append(inst)
    return sorted(out)

def instances_infactibles(inst_data):
    out = []
    for inst in inst_data:
        ks = [k for k in inst_data[inst] if isinstance(k, int)]
        if any(inst_data[inst][k]["bench_over"] > 0 for k in ks):
            out.append(inst)
    return sorted(out)

# ----------------------------
# PLOTS
# ----------------------------
def graficar_barras(instances, valores_por_k, titulo, nombre_figura, color_map, campo):

    plt.figure(figsize=(12, 5))
    x = np.arange(len(instances))

    ks = sorted({k for inst in instances for k in valores_por_k[inst] if isinstance(k, int)})

    for i, k in enumerate(ks):

        vals = []

        for inst in instances:

            fila = valores_por_k[inst].get(k, None)

            if fila is None:
                vals.append(np.nan)
                continue

            # mejora solo factibles
            if campo == "mejora" and fila["bench_over"] != 0:
                vals.append(np.nan)

            # delta solo infactibles
            elif campo == "delta" and fila["bench_over"] == 0:
                vals.append(np.nan)

            else:
                vals.append(fila[campo])

        plt.bar(
            x + i * BAR_WIDTH,
            vals,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=color_map.get(k, "gray")
        )

    plt.axhline(0, color="black", linestyle="--", linewidth=1)

    plt.xticks(x + BAR_WIDTH * (len(ks)-1)/2, instances, rotation=45)
    plt.ylabel("%")
    plt.title(titulo)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()

def graficar_media_std(instances, valores_por_k, titulo, nombre_figura, color_map):

    plt.figure(figsize=(12, 5))
    x = np.arange(len(instances))

    ks = sorted({k for inst in instances for k in valores_por_k[inst] if isinstance(k, int)})

    for i, k in enumerate(ks):

        medias = [valores_por_k[inst].get(k, {}).get("mean", np.nan) for inst in instances]
        stds   = [valores_por_k[inst].get(k, {}).get("std", 0.0) for inst in instances]

        plt.bar(
            x + i * BAR_WIDTH,
            medias,
            yerr=stds,
            capsize=4,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=color_map.get(k, "gray")
        )

    bench_vals = [valores_por_k[inst]["benchmark"] for inst in instances]

    plt.bar(
        x + len(ks)*BAR_WIDTH,
        bench_vals,
        width=BAR_WIDTH,
        label="Benchmark",
        color="grey"
    )

    plt.xticks(x + BAR_WIDTH * len(ks)/2, instances, rotation=45)
    plt.ylabel("Coste total")
    plt.title(titulo)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()

def graficar_best_total_vs_benchmark(instances, valores_por_k, titulo, nombre_figura, color_map):

    plt.figure(figsize=(12, 5))
    x = np.arange(len(instances))

    ks = sorted({k for inst in instances for k in valores_por_k[inst] if isinstance(k, int)})

    for i, k in enumerate(ks):

        vals = [valores_por_k[inst].get(k, {}).get("best_total", np.nan) for inst in instances]

        plt.bar(
            x + i * BAR_WIDTH,
            vals,
            width=BAR_WIDTH,
            label=f"k={k}",
            color=color_map.get(k, "gray")
        )

    bench_vals = [valores_por_k[inst]["benchmark"] for inst in instances]

    plt.bar(
        x + len(ks)*BAR_WIDTH,
        bench_vals,
        width=BAR_WIDTH,
        label="Benchmark",
        color="grey"
    )

    plt.xticks(x + BAR_WIDTH * len(ks)/2, instances, rotation=45)
    plt.ylabel("Coste total")
    plt.title(titulo)
    plt.legend()
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()

# ----------------------------
# EXECUTION
# ----------------------------
for opt, inst_data in data.items():

    print(f"📊 {opt}")

    factibles = instances_factibles(inst_data)
    infactibles = instances_infactibles(inst_data)
    todas = sorted(inst_data.keys())

    if factibles:
        graficar_barras(
            factibles,
            inst_data,
            f"{opt} | Percentage increase (factibles)",
            f"{opt}_mejora_factibles.png",
            COLORS_K,
            "mejora"
        )

    if infactibles:
        graficar_barras(
            infactibles,
            inst_data,
            f"{opt} | Delta cost (infactibles)",
            f"{opt}_delta_infactibles.png",
            COLORS_K,
            "delta"
        )

    graficar_media_std(
        todas,
        inst_data,
        f"{opt} | Mean and variance total cost",
        f"{opt}_media_std.png",
        COLORS_K
    )

    graficar_best_total_vs_benchmark(
        todas,
        inst_data,
        f"{opt} | Best total cost vs Benchmark",
        f"{opt}_best_vs_benchmark.png",
        COLORS_K
    )

print("✅ Corregido")