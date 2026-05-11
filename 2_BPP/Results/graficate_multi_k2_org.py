#!/usr/bin/env python3
# plot_bpp_reg_vs_nonreg_k2.py

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt

# ---------------------------------------------------
# PARÁMETROS EXPERIMENTO
# ---------------------------------------------------
optimizador = "DIFFERENTIALEVOLTION"
k = 2

# ---------------------------------------------------
# RUTAS BD
# ---------------------------------------------------
DB_NAME_NONREG = "Your_route/z_BPP/A_DIFFERENTIAL_COMPARISON/Comparison_k/Simul_k2/Resultados/BPP_results.db"

DB_NAME_REG = "Your_route/z_BPP/A_DIFFERENTIAL_COMPARISON/Comparison_reg/Simul_k2/Resultados/BPP_results.db"

FIG_DIR = "Images"
os.makedirs(FIG_DIR, exist_ok=True)

plt.rcParams["hatch.linewidth"] = 1.2

# ---------------------------------------------------
# COLORES AZULES
# ---------------------------------------------------
COLOR_NONREG_INIT = "#1f77b4"
COLOR_NONREG_POST = "#aec7e8"
COLOR_REG_INIT = "#004c99"
COLOR_REG_POST = "#7fb3ff"
COLOR_BENCH = "gray"
HATCH = "//"

QUERY = """
SELECT n, pct_feasible, pct_initial_best,
       npq_used_best, npq_post_best,
       num_bins_used_best, num_bins_post_best,
       npq_benchmark, num_bins_benchmark
FROM BPP_results
"""

def load_data(db_path):
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute(QUERY)
    rows = c.fetchall()
    conn.close()

    data = {}
    for r in rows:
        n = r[0]
        data[n] = {
            "pct_feasible": r[1],
            "pct_initial_best": r[2],
            "npq_used_best": r[3],
            "npq_post_best": r[4],
            "num_bins_used_best": r[5],
            "num_bins_post_best": r[6],
            "npq_benchmark": r[7],
            "num_bins_benchmark": r[8],
        }
    return data


reg = load_data(DB_NAME_REG)
nonreg = load_data(DB_NAME_NONREG)
ns = sorted(set(reg.keys()) | set(nonreg.keys()))

def s(data, key):
    return [data.get(n, {}).get(key, np.nan) for n in ns]

group_gap = 1.2
x = np.arange(len(ns)) * group_gap
bar_w = 0.18

# ===================================================
# PLOT 1
# ===================================================
plt.figure(figsize=(11,5))

plt.bar(x - 1.5*bar_w, s(reg, "pct_feasible"), bar_w,
        label="% Feasible (Reg)", color=COLOR_REG_INIT)

plt.bar(x - 0.5*bar_w, s(nonreg, "pct_feasible"), bar_w,
        label="% Feasible (No reg)", color=COLOR_NONREG_INIT)

plt.bar(x + 0.5*bar_w, s(reg, "pct_initial_best"), bar_w,
        label="% Initial Best (Reg)", color=COLOR_REG_POST,
        hatch=HATCH, edgecolor="black")

plt.bar(x + 1.5*bar_w, s(nonreg, "pct_initial_best"), bar_w,
        label="% Initial Best (No reg)", color=COLOR_NONREG_POST,
        hatch=HATCH, edgecolor="black")

plt.title(f"Simulation | Optimizer: {optimizador} | k={k} | Feasible vs Initial Best")
plt.xlabel("n")
plt.ylabel("Percentage")
plt.xticks(x, ns)
plt.ylim(0, 139)
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, f"BPP_pct_reg_vs_nonreg_k{k}.png"), dpi=200)
plt.close()

# ===================================================
# PLOT 2
# ===================================================
plt.figure(figsize=(11,5))

plt.bar(x - 1.5*bar_w, s(reg, "npq_used_best"), bar_w,
        label="NPQ init (Reg)", color=COLOR_REG_INIT)

plt.bar(x - 0.5*bar_w, s(nonreg, "npq_used_best"), bar_w,
        label="NPQ init (No reg)", color=COLOR_NONREG_INIT)

plt.bar(x + 0.5*bar_w, s(reg, "npq_post_best"), bar_w,
        label="NPQ post (Reg)", color=COLOR_REG_POST,
        hatch=HATCH, edgecolor="black")

plt.bar(x + 1.5*bar_w, s(nonreg, "npq_post_best"), bar_w,
        label="NPQ post (No reg)", color=COLOR_NONREG_POST,
        hatch=HATCH, edgecolor="black")

plt.bar(x + 2.5*bar_w, s(reg, "npq_benchmark"), bar_w,
        label="Benchmark", color=COLOR_BENCH, alpha=0.6)

plt.title(f"Simulation | Optimizer: {optimizador} | k={k} | NPQ Comparison")
plt.xlabel("n")
plt.ylabel("NPQ")
plt.xticks(x, ns)
plt.ylim(0, 1.57)
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, f"BPP_npq_reg_vs_nonreg_k{k}.png"), dpi=200)
plt.close()

# ===================================================
# PLOT 3
# ===================================================
plt.figure(figsize=(11,5))

plt.bar(x - 1.5*bar_w, s(reg, "num_bins_used_best"), bar_w,
        label="Bins init (Reg)", color=COLOR_REG_INIT)

plt.bar(x - 0.5*bar_w, s(nonreg, "num_bins_used_best"), bar_w,
        label="Bins init (No reg)", color=COLOR_NONREG_INIT)

plt.bar(x + 0.5*bar_w, s(reg, "num_bins_post_best"), bar_w,
        label="Bins post (Reg)", color=COLOR_REG_POST,
        hatch=HATCH, edgecolor="black")

plt.bar(x + 1.5*bar_w, s(nonreg, "num_bins_post_best"), bar_w,
        label="Bins post (No reg)", color=COLOR_NONREG_POST,
        hatch=HATCH, edgecolor="black")

plt.bar(x + 2.5*bar_w, s(reg, "num_bins_benchmark"), bar_w,
        label="Benchmark", color=COLOR_BENCH, alpha=0.6)

plt.title(f"Simulation | Optimizer: {optimizador} | k={k} | Number of bins")
plt.xlabel("n")
plt.ylabel("Number of bins")
plt.xticks(x, ns)
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, f"BPP_bins_reg_vs_nonreg_k{k}.png"), dpi=200)
plt.close()

print("✅ Figuras generadas en:", FIG_DIR)