#!/usr/bin/env python3
# plot_bpp_best_npq_bars.py

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt

DB_NAME = "BPP_results.db"
FIG_DIR = "Images"

os.makedirs(FIG_DIR, exist_ok=True)

# ---------------------------------------------------
# LEER BD
# ---------------------------------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
SELECT n, pct_feasible, pct_initial_best,
       npq_used_best, npq_post_best,
       num_bins_used_best, num_bins_post_best,
       npq_benchmark, num_bins_benchmark
FROM BPP_results
""")

rows = c.fetchall()
conn.close()

if not rows:
    print("❌ No se encontraron datos")
    exit()

# ---------------------------------------------------
# ORGANIZAR POR n
# ---------------------------------------------------
data_by_n = {}
for row in rows:
    n = row[0]
    data_by_n[n] = {
        "pct_feasible": row[1],
        "pct_initial_best": row[2],
        "npq_used_best": row[3],
        "npq_post_best": row[4],
        "num_bins_used_best": row[5],
        "num_bins_post_best": row[6],
        "npq_benchmark": row[7],
        "num_bins_benchmark": row[8],
    }

ns = sorted(data_by_n.keys())

# ---------------------------------------------------
# SERIES
# ---------------------------------------------------
pct_fact = [data_by_n[n]["pct_feasible"] for n in ns]
pct_initial_best = [data_by_n[n]["pct_initial_best"] for n in ns]

npq_used = [data_by_n[n]["npq_used_best"] or np.nan for n in ns]
npq_post = [data_by_n[n]["npq_post_best"] or np.nan for n in ns]
npq_benchmark = [data_by_n[n]["npq_benchmark"] or np.nan for n in ns]

num_bins_used = [data_by_n[n]["num_bins_used_best"] or np.nan for n in ns]
num_bins_post = [data_by_n[n]["num_bins_post_best"] or np.nan for n in ns]
num_bins_benchmark = [data_by_n[n]["num_bins_benchmark"] or np.nan for n in ns]

# ---------------------------------------------------
# PLOT 1: % factibles vs initial best
# ---------------------------------------------------
plt.figure(figsize=(9,5))

width = 0.35
x = np.arange(len(ns))

plt.bar(x - width/2, pct_fact, width, label="% Feasible", color="skyblue")
plt.bar(x + width/2, pct_initial_best, width, label="% Best Initial", color="navy")

plt.title("Percentage of feasible solutions por JSON - k=2 ")
plt.xlabel("n")
plt.ylabel("Percentage")
plt.xticks(x, ns)
plt.ylim(0, 119)

plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, "BPP_k2_YJ_pct_factibles.png"), dpi=200)
plt.close()

# ---------------------------------------------------
# PLOT 2: NPQ
# ---------------------------------------------------
plt.figure(figsize=(9,5))

width = 0.25
x = np.arange(len(ns))

plt.bar(x - width, npq_used, width, label="NPQ used", color="lightgreen")
plt.bar(x, npq_post, width, label="NPQ post", color="yellowgreen")
plt.bar(x + width, npq_benchmark, width, label="NPQ benchmark", color="salmon")

plt.title("NPQ best solution vs Benchmark - k=2")
plt.xlabel("n")
plt.ylabel("NPQ")
plt.xticks(x, ns)
plt.ylim(0, 1.3)

plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, "BPP_k2_YJ_best_npq_used_post_vs_benchmark.png"), dpi=200)
plt.close()

# ---------------------------------------------------
# PLOT 3: Número de bins
# ---------------------------------------------------
plt.figure(figsize=(9,5))

width = 0.25
x = np.arange(len(ns))

plt.bar(x - width, num_bins_used, width, label="Bins used", color="orange")
plt.bar(x, num_bins_post, width, label="Bins post", color="gold")
plt.bar(x + width, num_bins_benchmark, width, label="Bins benchmark", color="gray")

plt.title("Number of bins vs Benchmark - k=2")
plt.xlabel("n")
plt.ylabel("Number of bins")
plt.xticks(x, ns)

plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)

plt.savefig(os.path.join(FIG_DIR, "BPP_k2_YJ_num_bins_used_post_vs_benchmark.png"), dpi=200)
plt.close()

print("✅ Gráficos generados en carpeta:", FIG_DIR)