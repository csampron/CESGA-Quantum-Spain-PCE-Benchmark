#!/usr/bin/env python3
# plot_bpp_best_npq_bars.py
#
# Script para graficar:
# - % de soluciones factibles vs n
# - Mejor NPQ factible usado/post vs NPQ benchmark
# - Número de bins de la mejor solución (used/post) vs Benchmark

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
SELECT n, pct_feasible, npq_used_best, npq_post_best,
       num_bins_used_best, num_bins_post_best,
       npq_benchmark, num_bins_benchmark
FROM BPP_results
""")

rows = c.fetchall()
conn.close()

if not rows:
    print("❌ No se encontraron datos en la base BPP_results.db")
    exit()

# ---------------------------------------------------
# ORGANIZAR POR n
# ---------------------------------------------------
data_by_n = {}
for n, pct_feasible, npq_used, npq_post, num_bins_used, num_bins_post, npq_bench, num_bins_bench in rows:
    data_by_n[n] = {
        "pct_feasible": pct_feasible,
        "npq_used_best": npq_used,
        "npq_post_best": npq_post,
        "num_bins_used_best": num_bins_used,
        "num_bins_post_best": num_bins_post,
        "npq_benchmark": npq_bench,
        "num_bins_benchmark": num_bins_bench
    }

ns = sorted(data_by_n.keys())

# ---------------------------------------------------
# PREPARAR SERIES
# ---------------------------------------------------
pct_fact = [data_by_n[n]["pct_feasible"] for n in ns]

# NPQ
npq_used = [data_by_n[n]["npq_used_best"] if data_by_n[n]["npq_used_best"] is not None else np.nan for n in ns]
npq_post = [data_by_n[n]["npq_post_best"] if data_by_n[n]["npq_post_best"] is not None else np.nan for n in ns]
npq_benchmark = [data_by_n[n]["npq_benchmark"] if data_by_n[n]["npq_benchmark"] is not None else np.nan for n in ns]

# Número de bins
num_bins_used = [data_by_n[n]["num_bins_used_best"] if data_by_n[n]["num_bins_used_best"] is not None else np.nan for n in ns]
num_bins_post = [data_by_n[n]["num_bins_post_best"] if data_by_n[n]["num_bins_post_best"] is not None else np.nan for n in ns]
num_bins_benchmark = [data_by_n[n]["num_bins_benchmark"] if data_by_n[n]["num_bins_benchmark"] is not None else np.nan for n in ns]

# ---------------------------------------------------
# PLOT 1: Porcentaje de factibles
# ---------------------------------------------------
plt.figure(figsize=(10,5))
plt.bar(ns, pct_fact, color="skyblue")
plt.title("Porcentaje de soluciones factibles por JSON")
plt.xlabel("n")
plt.ylabel("% factibles")
plt.xticks(ns)
plt.ylim(0, 100)
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.savefig(os.path.join(FIG_DIR, "BPP_YJ_pct_factibles.png"), dpi=200)
plt.close()

# ---------------------------------------------------
# PLOT 2: NPQ usado/post vs Benchmark
# ---------------------------------------------------
plt.figure(figsize=(12,5))
width = 0.25
x = np.arange(len(ns))

plt.bar(x - width, npq_used, width, label="NPQ used", color="lightgreen")
plt.bar(x, npq_post, width, label="NPQ post", color="yellowgreen")
plt.bar(x + width, npq_benchmark, width, label="NPQ benchmark", color="salmon")

plt.title("NPQ mejor solución (used/post) vs NPQ Benchmark por JSON")
plt.xlabel("n")
plt.ylabel("NPQ")
plt.xticks(x, ns)
plt.ylim(0, 1.05)
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.savefig(os.path.join(FIG_DIR, "BPP_YJ_best_npq_used_post_vs_benchmark.png"), dpi=200)
plt.close()

# ---------------------------------------------------
# PLOT 3: Número de bins: used, post vs Benchmark
# ---------------------------------------------------
plt.figure(figsize=(12,5))
width = 0.25
x = np.arange(len(ns))

plt.bar(x - width, num_bins_used, width, label="Bins used", color="orange")
plt.bar(x, num_bins_post, width, label="Bins post", color="gold")
plt.bar(x + width, num_bins_benchmark, width, label="Bins benchmark", color="gray")

plt.title("Número de bins: mejor solución (used/post) vs benchmark")
plt.xlabel("n")
plt.ylabel("Número de bins")
plt.xticks(x, ns)
plt.legend()
plt.grid(axis="y", linestyle="--", alpha=0.7)
plt.savefig(os.path.join(FIG_DIR, "BPP_YJ_num_bins_used_post_vs_benchmark.png"), dpi=200)
plt.close()
