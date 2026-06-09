#!/usr/bin/env python3
# analyze_bins_feasible_vs_combinatorial.py

import os
import json
import sqlite3
import re
import statistics
from typing import Optional

RESULTS_DIR = "Your_path/z_BPP/Results/Comparison_reg/Simul_k3/Resultados"
DB_NAME = "BIN_results_feasible_vs_combinatorial_k3.db"

benchmark = {
    # Completar si tienes óptimos por instancia
    # "bin5": 3,
}


def mejora_porcentual(val_algo: float, val_bench: float) -> Optional[float]:
    if val_algo is None or val_bench is None:
        return None
    return (val_bench - val_algo) / val_bench * 100


def create_results_table(cursor, table_name):
    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        filename TEXT PRIMARY KEY,
        instance TEXT,
        optimizer TEXT,
        best_initial_bins REAL,
        post_for_best_initial REAL,
        mejora_initial REAL,
        mejora_post REAL,
        mean_initial_bins REAL,
        std_initial_bins REAL,
        benchmark REAL
    )
    """)


def save_group_results(cursor, table_name, filename, instance, optimizer, runs, bench):
    initial_bins_values = []
    best_initial_bins = None
    post_for_best_initial = None

    for run_data in runs:
        initial_bins = run_data.get("num_bins_used")
        post_bins = run_data.get("num_bins_used_post")

        if initial_bins is None or post_bins is None:
            continue

        initial_bins_values.append(initial_bins)

        if best_initial_bins is None or initial_bins < best_initial_bins:
            best_initial_bins = initial_bins
            post_for_best_initial = post_bins

    if not initial_bins_values:
        return False

    mean_initial_bins = statistics.mean(initial_bins_values)
    std_initial_bins = (
        statistics.stdev(initial_bins_values)
        if len(initial_bins_values) > 1 else 0.0
    )

    mejora_initial = mejora_porcentual(best_initial_bins, bench)
    mejora_post = mejora_porcentual(post_for_best_initial, bench)

    cursor.execute(f"""
    INSERT OR REPLACE INTO {table_name}
    (
        filename,
        instance,
        optimizer,
        best_initial_bins,
        post_for_best_initial,
        mejora_initial,
        mejora_post,
        mean_initial_bins,
        std_initial_bins,
        benchmark
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        instance,
        optimizer,
        best_initial_bins,
        post_for_best_initial,
        mejora_initial,
        mejora_post,
        mean_initial_bins,
        std_initial_bins,
        bench
    ))

    return True


conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

create_results_table(c, "BIN_results_feasible")
create_results_table(c, "BIN_results_combinatorial")

c.execute("""
CREATE TABLE IF NOT EXISTS BIN_feasibility_counts (
    filename TEXT PRIMARY KEY,
    instance TEXT,
    optimizer TEXT,
    total_runs INTEGER,
    feasible_runs INTEGER,
    combinatorial_runs INTEGER,
    feasible_percentage REAL,
    best_perfect_bins REAL,
    best_perfect_count INTEGER,
    best_perfect_percentage REAL
)
""")

c.execute("DELETE FROM BIN_results_feasible")
c.execute("DELETE FROM BIN_results_combinatorial")
c.execute("DELETE FROM BIN_feasibility_counts")
conn.commit()

json_files = []

for root, dirs, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"Encontrados {len(json_files)} JSONs")

for ruta in sorted(json_files):
    filename = os.path.basename(ruta)

    m = re.match(r".*?(\d+)_([A-Za-z0-9]+)_(\d+)\.json", filename)

    if not m:
        print(f"Saltando nombre no válido: {filename}")
        continue

    instance = f"bin{m.group(1)}"
    optimizer = m.group(2)

    bench = benchmark.get(instance)

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"ERROR leyendo {filename}: {e}")
        continue

    resultados = data.get("resultados", [])

    feasible_runs = []
    combinatorial_runs = []

    for run_data in resultados:
        status = run_data.get("status_initial")

        if status == "perfect":
            feasible_runs.append(run_data)

        elif status == "combinatorial":
            combinatorial_runs.append(run_data)

        elif status == "infeasible":
            pass

        else:
            print(f"Status desconocido en {filename}: {status}")

    total_runs_count = len(resultados)
    feasible_runs_count = len(feasible_runs)
    combinatorial_runs_count = len(combinatorial_runs)

    feasible_percentage = (
        100.0 * feasible_runs_count / total_runs_count
        if total_runs_count > 0 else None
    )

    # =====================================================
    # Mejor solución perfect encontrada y frecuencia
    # =====================================================

    perfect_initial_bins = [
        r.get("num_bins_used")
        for r in feasible_runs
        if r.get("num_bins_used") is not None
    ]

    if perfect_initial_bins:

        best_perfect_bins = min(perfect_initial_bins)

        best_perfect_count = sum(
            1
            for v in perfect_initial_bins
            if v == best_perfect_bins
        )

        best_perfect_percentage = (
            100.0 * best_perfect_count /
            len(perfect_initial_bins)
        )

    else:

        best_perfect_bins = None
        best_perfect_count = 0
        best_perfect_percentage = None

    c.execute("""
    INSERT OR REPLACE INTO BIN_feasibility_counts
    (
        filename,
        instance,
        optimizer,
        total_runs,
        feasible_runs,
        combinatorial_runs,
        feasible_percentage,
        best_perfect_bins,
        best_perfect_count,
        best_perfect_percentage
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        instance,
        optimizer,
        total_runs_count,
        feasible_runs_count,
        combinatorial_runs_count,
        feasible_percentage,
        best_perfect_bins,
        best_perfect_count,
        best_perfect_percentage
    ))

    saved_feasible = save_group_results(
        c,
        "BIN_results_feasible",
        filename,
        instance,
        optimizer,
        feasible_runs,
        bench
    )

    saved_combinatorial = save_group_results(
        c,
        "BIN_results_combinatorial",
        filename,
        instance,
        optimizer,
        combinatorial_runs,
        bench
    )

    print(
        f"{filename}: "
        f"feasible={len(feasible_runs)}, "
        f"combinatorial={len(combinatorial_runs)}, "
        f"saved_feasible={saved_feasible}, "
        f"saved_combinatorial={saved_combinatorial}"
    )

conn.commit()
conn.close()

print("\nAnálisis completado.")
print(f"Resultados guardados en: {DB_NAME}")
print("Tablas creadas:")
print("  - BIN_results_feasible")
print("  - BIN_results_combinatorial")
print("  - BIN_feasibility_counts")