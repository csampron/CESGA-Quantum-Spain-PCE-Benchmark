#!/usr/bin/env python3

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

# ----------------------------
# Configuración
# ----------------------------
DB_NAME = "VRP_results.db"
FIG_DIR = "Images"
PENALTY = 10.0

os.makedirs(FIG_DIR, exist_ok=True)

# ----------------------------
# Benchmarks
# ----------------------------
benchmark_data = {
    "4_1": {"cost": 97},
    "4_2": {"cost": 121},
    "5_1": {"cost": 94},
    "5_2": {"cost": 295},
    "6_1": {"cost": 118},
    "6_2": {"cost": 122},
    "7_1": {"cost": 129},
    "7_2": {"cost": 174},
    "8_1": {"cost": 153},
    "8_2": {"cost": 279},
}

# ----------------------------
# Métricas CORRECTAS
# ----------------------------
def metricas_vrp(best_total, bench_cost, bench_over, penalty=PENALTY):

    best_total = float(best_total)
    bench_cost = float(bench_cost)
    bench_over = float(bench_over)

    # penalización SOLO al benchmark
    bench_pen = bench_cost + penalty * bench_over

    # mejora SOLO para benchmarks factibles
    mejora = (bench_cost - best_total) / bench_cost * 100

    # delta-cost siempre contra benchmark penalizado
    delta = (best_total - bench_pen) / bench_pen * 100

    # limpieza numérica
    if abs(mejora) < 1e-10:
        mejora = 0.0
    if abs(delta) < 1e-10:
        delta = 0.0

    return mejora, delta

# ----------------------------
# Leer BD
# ----------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
SELECT
    instance,
    optimizer,
    best_total_cost,
    over_capacity,
    benchmark_over_capacity,
    mean_total_cost,
    std_total_cost
FROM VRP_results
ORDER BY optimizer, instance
""")

rows = c.fetchall()
conn.close()

# ----------------------------
# Agrupar
# ----------------------------
data = defaultdict(lambda: {
    "factibles": {"instances": [], "mejora": []},
    "infactibles": {"instances": [], "delta": []},
    "stats": {"instances": [], "mean": [], "std": []}
})

for inst, opt, best_total, over_sol, bench_over, mean_total, std_total in rows:

    if inst not in benchmark_data:
        continue

    bench_cost = benchmark_data[inst]["cost"]

    # 🔴 FIX CLAVE: usar bench_over (NO over_sol)
    mejora, delta = metricas_vrp(
        best_total,
        bench_cost,
        bench_over
    )

    d = data[opt]

    # decisión de métrica SOLO por benchmark
    if bench_over == 0:
        d["factibles"]["instances"].append(inst)
        d["factibles"]["mejora"].append(mejora)
    else:
        d["infactibles"]["instances"].append(inst)
        d["infactibles"]["delta"].append(delta)

    # stats
    if mean_total is not None:
        d["stats"]["instances"].append(inst)
        d["stats"]["mean"].append(mean_total)
        d["stats"]["std"].append(std_total or 0.0)

# ----------------------------
# Plot
# ----------------------------
def graficar(instances, values, title, filename, color):
    plt.figure(figsize=(10, 5))
    x = np.arange(len(instances))

    plt.bar(x, values, color=color)
    plt.axhline(0, color="black", linestyle="--", linewidth=1)

    plt.xticks(x, instances, rotation=45)
    plt.title(title)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), dpi=300)
    plt.close()

def graficar_stats(instances, mean, std, title, filename):
    plt.figure(figsize=(10, 5))
    x = np.arange(len(instances))

    plt.bar(x, mean, yerr=std, capsize=5, color="darkorange")

    plt.xticks(x, instances, rotation=45)
    plt.title(title)
    plt.grid(axis="y", linestyle="--", alpha=0.6)

    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, filename), dpi=300)
    plt.close()

# ----------------------------
# Generate figures
# ----------------------------
for opt, d in data.items():

    print(f"📊 {opt}")

    if d["factibles"]["instances"]:
        graficar(
            d["factibles"]["instances"],
            d["factibles"]["mejora"],
            f"{opt} - Mejora (%) benchmark factible (k=2)",
            f"{opt}_mejora_k2.png",
            "steelblue"
        )

    if d["infactibles"]["instances"]:
        graficar(
            d["infactibles"]["instances"],
            d["infactibles"]["delta"],
            f"{opt} - Delta-cost (%) benchmark infactible (k=2)",
            f"{opt}_delta_k2.png",
            "crimson"
        )

    if d["stats"]["instances"]:
        graficar_stats(
            d["stats"]["instances"],
            d["stats"]["mean"],
            d["stats"]["std"],
            f"{opt} - Stats clusters (k=2)",
            f"{opt}_stats_k2.png"
        )

print("✅ OK")