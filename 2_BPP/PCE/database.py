#!/usr/bin/env python3
# analyze_bpp_results.py
# Analiza JSONs en Resultados/BPP/... -> calcula NPQ
# Guarda la mejor solución factible, porcentaje de factibles y benchmark
# Incluye NPQ y número de bins para used y post

import os
import json
import sqlite3
import re
from typing import List, Optional

RESULTS_DIR = "Resultados/BPP"
DB_NAME = "BPP_results.db"

# ------------------------
# Pesos, capacidades y benchmark por N
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
    3:  10,
    4:  10,
    5:  12,
    6:  10,
    7:  10,
    8:  12,
    9:  12,
    10: 10,
    12: 10,
    14: 12,
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
# Funciones utilitarias
# ------------------------
def normalize_bins(bins: List[List[int]]) -> List[List[int]]:
    return [[int(x) for x in b] for b in (bins or [])]

def filter_nonempty_bins(bins: List[List[int]]) -> List[List[int]]:
    """Elimina bins vacíos"""
    return [b for b in bins if len(b) > 0]

def compute_npq_for_bins(
    bins: List[List[int]],
    weights: List[int],
    capacity: int
) -> Optional[float]:
    """Devuelve NPQ si es factible, None si no lo es."""
    for b in bins:
        if sum(weights[i] for i in b) > capacity:
            return None

    N = len(weights)
    bin_weights = [sum(weights[i] for i in b) for b in bins]
    waste_total = sum(max(0, capacity - bw) for bw in bin_weights)

    npq = 1.0 - (waste_total / (N * capacity))
    return max(0.0, min(1.0, npq))

# ------------------------
# Crear / abrir BD
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS BPP_results (
        filename TEXT PRIMARY KEY,
        n INTEGER,
        optimizer TEXT,
        pct_feasible REAL,
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
# Buscar archivos JSON
# ------------------------
json_files = []
for root, _, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.startswith("BPP") and file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"Encontrados {len(json_files)} JSONs en {RESULTS_DIR}")

# ------------------------
# Procesar JSONs
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
    m = re.match(r"BPP(\d+)_([A-Za-z0-9]+)_(\d+)\.json", filename)
    if not m:
        print(f"Nombre no esperado, se salta: {filename}")
        continue

    n = int(m.group(1))
    optimizer = m.group(2)

    if n not in weights_by_n or n not in capacity_by_n or n not in benchmark_bins_by_n:
        print(f"No hay benchmark para n={n}, archivo {filename}")
        continue

    weights = weights_by_n[n]
    capacity = capacity_by_n[n]

    # ---- Benchmark ----
    benchmark_bins_raw = normalize_bins(benchmark_bins_by_n[n])
    benchmark_bins = filter_nonempty_bins(benchmark_bins_raw)

    npq_bench = compute_npq_for_bins(benchmark_bins, weights, capacity)
    num_bins_benchmark = len(benchmark_bins)

    # ---- Resultados ----
    total_runs = 0
    num_feasible = 0
    best_npq_used = None
    best_npq_post = None
    num_bins_used_best = None
    num_bins_post_best = None

    for run_data in data.get("resultados", []):
        total_runs += 1

        bins_solution_raw = normalize_bins(run_data.get("bins_solution", []))
        bins_solution = filter_nonempty_bins(bins_solution_raw)

        feasible_flag = run_data.get("feasibility_initial", {}).get("feasible", False)

        if feasible_flag:
            # NPQ used
            npq_used = compute_npq_for_bins(bins_solution, weights, capacity)

            # NPQ post
            bins_solution_post_raw = normalize_bins(run_data.get("bins_solution_post", []))
            bins_solution_post = filter_nonempty_bins(bins_solution_post_raw)
            npq_post = compute_npq_for_bins(bins_solution_post, weights, capacity)

            num_feasible += 1

            # Actualizar mejor NPQ used
            if best_npq_used is None or (npq_used is not None and npq_used > best_npq_used):
                best_npq_used = npq_used
                num_bins_used_best = run_data.get("num_bins_used", len(bins_solution))

            # Actualizar mejor NPQ post
            if best_npq_post is None or (npq_post is not None and npq_post > best_npq_post):
                best_npq_post = npq_post
                num_bins_post_best = run_data.get("num_bins_used_post", len(bins_solution_post))

    pct_feasible = 100 * num_feasible / total_runs if total_runs else 0

    # ---- Guardar en BD ----
    c.execute("""
    INSERT OR REPLACE INTO BPP_results
    (filename, n, optimizer, pct_feasible,
     num_bins_used_best, num_bins_post_best,
     npq_used_best, npq_post_best,
     num_bins_benchmark, npq_benchmark)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename, n, optimizer, pct_feasible,
        num_bins_used_best, num_bins_post_best,
        best_npq_used, best_npq_post,
        num_bins_benchmark, npq_bench
    ))

    print(
        f"{filename}: n={n}, "
        f"factibles={pct_feasible:.1f}%, "
        f"bins_used_best={num_bins_used_best}, "
        f"bins_post_best={num_bins_post_best}, "
        f"npq_used_best={best_npq_used}, "
        f"npq_post_best={best_npq_post}, "
        f"bins_benchmark={num_bins_benchmark}, "
        f"npq_benchmark={npq_bench}"
    )

conn.commit()
conn.close()

print("\nAnálisis completado. Resultados guardados en:", DB_NAME)
