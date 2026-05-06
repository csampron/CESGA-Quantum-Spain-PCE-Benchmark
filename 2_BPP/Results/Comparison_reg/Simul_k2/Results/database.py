#!/usr/bin/env python3
# analyze_bpp_results.py

import os
import json
import sqlite3
from typing import List, Optional

RESULTS_DIR = (
    "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/A_DIFFERENTIAL_COMPARISON/Comparison_reg/Simul_k2"
)

DB_NAME = "BPP_results.db"

# ------------------------
# Datos del problema
# ------------------------
weights_by_n = {
    3:  [5, 5, 2],
    4:  [5, 2, 2, 2],
    5:  [5, 5, 5, 2, 2],
    6:  [5, 5, 2, 2, 5, 5],
    7:  [5, 5, 2, 5, 5, 2, 2],
    8:  [5, 5, 2, 2, 2, 2, 2, 2],
    9:  [5, 5, 2, 2, 2, 5, 5, 2, 2],
    10: [5, 5, 5, 5, 2, 2, 5, 2, 2, 5],
    12: [5, 5, 2, 2, 2, 5, 5, 2, 5, 2, 5, 5],
    14: [5, 5, 5, 2, 2, 2, 5, 5, 5, 2, 2, 2, 2, 2],
}

capacity_by_n = {
    3: 10, 4: 10, 5: 12, 6: 10, 7: 10,
    8: 12, 9: 12, 10: 10, 12: 10, 14: 12,
}

benchmark_bins_by_n = {
    3:  [[2], [], [0, 1]],
    4:  [[1, 2], [], [], [0, 3]],
    5:  [[], [], [0, 1], [], [2, 3, 4]],
    6:  [[], [1, 5], [], [2, 3], [], [0, 4]],
    7:  [[3, 4], [], [0, 1], [5], [2, 6], [], []],
    8:  [[], [1, 5], [4], [0, 3], [], [], [2, 6, 7], []],
    9:  [[], [2, 5, 8], [0, 1], [], [6], [3, 4, 7], [], [], []],
    10: [[0, 1], [3, 5], [], [2], [6, 7], [], [8], [], [4, 9], []],
    12: [[], [1, 3], [0, 6], [7], [], [4, 10], [2, 9, 11], [], [8], [], [], [5]],
    14: [[], [], [], [], [3, 6], [], [2], [1], [], [0], [4, 9, 12], [], [8, 10, 11], [5, 7, 13]],
}

# ------------------------
# Funciones auxiliares
# ------------------------
def normalize_bins(bins: List[List[int]]) -> List[List[int]]:
    return [[int(x) for x in b] for b in (bins or [])]

def filter_nonempty_bins(bins: List[List[int]]) -> List[List[int]]:
    return [b for b in bins if len(b) > 0]

def compute_npq_for_bins(
    bins: List[List[int]],
    weights: List[int],
    capacity: int
) -> Optional[float]:
    for b in bins:
        if sum(weights[i] for i in b) > capacity:
            return None

    N = len(weights)
    bin_weights = [sum(weights[i] for i in b) for b in bins]
    waste_total = sum(max(0, capacity - bw) for bw in bin_weights)

    npq = 1.0 - (waste_total / (N * capacity))
    return max(0.0, min(1.0, npq))

# ------------------------
# Crear BD
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS BPP_results (
        filename TEXT PRIMARY KEY,
        n INTEGER,
        optimizer TEXT,
        pct_feasible REAL,
        pct_initial_best REAL,
        num_bins_used_best INTEGER,
        num_bins_post_best INTEGER,
        npq_used_best REAL,
        npq_post_best REAL,
        num_bins_benchmark INTEGER,
        npq_benchmark REAL
    )
    """)
    conn.commit()

# ------------------------
# Buscar JSONs
# ------------------------
json_files = []
for root, _, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.startswith("BPP") and file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"Encontrados {len(json_files)} JSONs")

# ------------------------
# Procesar
# ------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

for ruta in sorted(json_files):
    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR leyendo {ruta}: {e}")
        continue

    filename = os.path.basename(ruta)
    parts = ruta.split(os.sep)

    try:
        items_folder = next(p for p in parts if p.endswith("_items"))
        n = int(items_folder.replace("_items", ""))
        idx = parts.index(items_folder)
        optimizer = parts[idx + 1].upper()
    except Exception:
        print(f"Error extrayendo info de {ruta}")
        continue

    if n not in weights_by_n:
        continue

    weights = weights_by_n[n]
    capacity = capacity_by_n[n]

    # ---- Benchmark ----
    benchmark_bins = filter_nonempty_bins(normalize_bins(benchmark_bins_by_n[n]))
    npq_bench = compute_npq_for_bins(benchmark_bins, weights, capacity)
    num_bins_benchmark = len(benchmark_bins)

    # ---- Inicialización ----
    total_runs = 0
    num_feasible = 0

    best_npq_used = None
    best_npq_post = None
    num_bins_used_best = None
    num_bins_post_best = None

    all_bins_used = []  # 👈 CLAVE

    # ---- Loop ----
    for run_data in data.get("resultados", []):
        total_runs += 1

        bins_solution = filter_nonempty_bins(
            normalize_bins(run_data.get("bins_solution", []))
        )

        num_bins_used = run_data.get("num_bins_used", len(bins_solution))
        if num_bins_used is not None:
            all_bins_used.append(num_bins_used)

        feasible_flag = run_data.get("feasibility_initial", {}).get("feasible", False)

        if feasible_flag:
            num_feasible += 1

            npq_used = compute_npq_for_bins(bins_solution, weights, capacity)

            bins_post = filter_nonempty_bins(
                normalize_bins(run_data.get("bins_solution_post", []))
            )
            npq_post = compute_npq_for_bins(bins_post, weights, capacity)

            if best_npq_used is None or (npq_used and npq_used > best_npq_used):
                best_npq_used = npq_used
                num_bins_used_best = num_bins_used

            if best_npq_post is None or (npq_post and npq_post > best_npq_post):
                best_npq_post = npq_post
                num_bins_post_best = run_data.get("num_bins_used_post", len(bins_post))

    # ---- Métricas ----
    pct_feasible = 100 * num_feasible / total_runs if total_runs else 0

    if all_bins_used:
        min_bins_used = min(all_bins_used)
        count_best = sum(1 for b in all_bins_used if b == min_bins_used)
        pct_initial_best = 100 * count_best / total_runs
    else:
        pct_initial_best = 0

    # ---- Guardar ----
    c.execute("""
    INSERT OR REPLACE INTO BPP_results
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename, n, optimizer,
        pct_feasible,
        pct_initial_best,
        num_bins_used_best,
        num_bins_post_best,
        best_npq_used,
        best_npq_post,
        num_bins_benchmark,
        npq_bench
    ))

    print(
        f"{filename} | n={n} | "
        f"feasible={pct_feasible:.1f}% | "
        f"initial_best={pct_initial_best:.1f}%"
    )

conn.commit()
conn.close()

print("\n✅ Análisis completado")