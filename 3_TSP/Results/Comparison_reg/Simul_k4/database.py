#!/usr/bin/env python3
# analyze_tsp_feasible_vs_repaired.py

import os
import json
import sqlite3
import re
import statistics
from typing import Optional

RESULTS_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_TSP/Results/Comparison_reg/Simul_k4/Resultados"
DB_NAME = "TSP_results_feasible_vs_repaired_k4.db"

THRESHOLD = 0.5

benchmark = {
    "tsp4": 6700,
    "tsp5": 6786,
    "tsp6": 9815,
    "tsp7": 7245,
    "tsp8": 2794,
    "tsp9": 2438,
    "tsp10": 3155,
    "tsp15": 5268,
    "tsp22": 13005,
    "tsp25": 83132,
}


def mejora_porcentual(val_algo: float, val_bench: float) -> Optional[float]:
    if val_algo is None or val_bench is None:
        return None
    return (val_bench - val_algo) / val_bench * 100


def check_binary_feasibility(embedding_values, threshold=0.5):

    if embedding_values is None:
        return False

    nodes = sorted([int(k) for k in embedding_values.keys()])
    m = len(nodes)

    B = []

    for node in nodes:
        row = [
            1 if val >= threshold else 0
            for val in embedding_values[str(node)]
        ]
        B.append(row)

    row_sums = [sum(row) for row in B]

    col_sums = [
        sum(B[i][j] for i in range(m))
        for j in range(m)
    ]

    rows_ok = all(s == 1 for s in row_sums)
    cols_ok = all(s == 1 for s in col_sums)

    return rows_ok and cols_ok


def create_results_table(cursor, table_name):

    cursor.execute(f"""
    CREATE TABLE IF NOT EXISTS {table_name} (
        filename TEXT PRIMARY KEY,
        instance TEXT,
        optimizer TEXT,
        best_initial_distance REAL,
        refined_for_best_initial REAL,
        mejora_initial REAL,
        mejora_refined REAL,
        mean_initial REAL,
        std_initial REAL,
        benchmark REAL
    )
    """)


def save_group_results(
    cursor,
    table_name,
    filename,
    instance,
    optimizer,
    runs,
    bench
):

    initial_distances = []
    best_initial_distance = None
    refined_for_best_initial = None

    for run_data in runs:

        initial_distance = run_data.get("initial_distance")
        refined_distance = run_data.get("refined_distance")

        if initial_distance is None or refined_distance is None:
            continue

        initial_distances.append(initial_distance)

        if (
            best_initial_distance is None
            or initial_distance < best_initial_distance
        ):
            best_initial_distance = initial_distance
            refined_for_best_initial = refined_distance

    if not initial_distances:
        return False

    mean_initial = statistics.mean(initial_distances)

    std_initial = (
        statistics.stdev(initial_distances)
        if len(initial_distances) > 1 else 0.0
    )

    mejora_initial = mejora_porcentual(
        best_initial_distance,
        bench
    )

    mejora_refined = mejora_porcentual(
        refined_for_best_initial,
        bench
    )

    cursor.execute(f"""
    INSERT OR REPLACE INTO {table_name}
    (
        filename,
        instance,
        optimizer,
        best_initial_distance,
        refined_for_best_initial,
        mejora_initial,
        mejora_refined,
        mean_initial,
        std_initial,
        benchmark
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        instance,
        optimizer,
        best_initial_distance,
        refined_for_best_initial,
        mejora_initial,
        mejora_refined,
        mean_initial,
        std_initial,
        bench
    ))

    return True


# -------------------------------------------------
# Crear BD
# -------------------------------------------------

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

create_results_table(c, "TSP_results_feasible")
create_results_table(c, "TSP_results_repaired")

c.execute("""
CREATE TABLE IF NOT EXISTS TSP_feasibility_counts (
    filename TEXT PRIMARY KEY,
    instance TEXT,
    optimizer TEXT,
    total_runs INTEGER,
    feasible_runs INTEGER,
    repaired_runs INTEGER,
    feasible_percentage REAL,
    best_feasible_initial REAL,
    best_feasible_count INTEGER,
    best_feasible_percentage REAL
)
""")

# Limpiar tablas para evitar mezclar ejecuciones
c.execute("DELETE FROM TSP_results_feasible")
c.execute("DELETE FROM TSP_results_repaired")
c.execute("DELETE FROM TSP_feasibility_counts")

conn.commit()

# -------------------------------------------------
# Buscar JSONs
# -------------------------------------------------

json_files = []

for root, dirs, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.startswith("TSP") and file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"Encontrados {len(json_files)} JSONs")

# -------------------------------------------------
# Procesar JSONs
# -------------------------------------------------

for ruta in sorted(json_files):

    filename = os.path.basename(ruta)

    m = re.match(
        r"TSP_(\d+)_([A-Za-z0-9]+)_(\d+)\.json",
        filename
    )

    if not m:
        print(f"Saltando nombre no válido: {filename}")
        continue

    instance = f"tsp{m.group(1)}"
    optimizer = m.group(2)

    if instance not in benchmark:
        print(f"No benchmark para {instance}")
        continue

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            data = json.load(f)

    except Exception as e:
        print(f"ERROR leyendo {filename}: {e}")
        continue

    resultados = data.get("resultados", [])

    feasible_runs = []
    repaired_runs = []

    # -------------------------------------------------
    # Separar runs
    # -------------------------------------------------

    feasible_runs = []
    repaired_runs = []   # ahora equivale a greedy

    for run_data in resultados:

        status = run_data.get("status")

        if status == "perfect":
            feasible_runs.append(run_data)

        elif status == "greedy":
            repaired_runs.append(run_data)

        elif status == "infeasible":
            # No se guarda en feasible ni repaired
            pass

        else:
            print(f"Status desconocido en {filename}: {status}")

    total_runs_count = len(resultados)
    feasible_runs_count = len(feasible_runs)
    repaired_runs_count = len(repaired_runs)

    feasible_percentage = (
        100.0 * feasible_runs_count / total_runs_count
        if total_runs_count > 0 else None
    )

    # =====================================================
    # Mejor solución perfect encontrada y frecuencia
    # =====================================================

    feasible_initial_distances = [
        r.get("initial_distance")
        for r in feasible_runs
        if r.get("initial_distance") is not None
    ]

    if feasible_initial_distances:

        best_feasible_initial = min(feasible_initial_distances)

        best_feasible_count = sum(
            1
            for v in feasible_initial_distances
            if v == best_feasible_initial
        )

        best_feasible_percentage = (
            100.0 * best_feasible_count /
            len(feasible_initial_distances)
        )

    else:

        best_feasible_initial = None
        best_feasible_count = 0
        best_feasible_percentage = None

    c.execute("""
    INSERT OR REPLACE INTO TSP_feasibility_counts
    (
        filename,
        instance,
        optimizer,
        total_runs,
        feasible_runs,
        repaired_runs,
        feasible_percentage,
        best_feasible_initial,
        best_feasible_count,
        best_feasible_percentage
    )
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        instance,
        optimizer,
        total_runs_count,
        feasible_runs_count,
        repaired_runs_count,
        feasible_percentage,
        best_feasible_initial,
        best_feasible_count,
        best_feasible_percentage
    ))

    bench = benchmark[instance]

    saved_feasible = save_group_results(
        c,
        "TSP_results_feasible",
        filename,
        instance,
        optimizer,
        feasible_runs,
        bench
    )

    saved_repaired = save_group_results(
        c,
        "TSP_results_repaired",
        filename,
        instance,
        optimizer,
        repaired_runs,
        bench
    )

    print(
        f"{filename}: "
        f"feasible={len(feasible_runs)}, "
        f"repaired={len(repaired_runs)}, "
        f"saved_feasible={saved_feasible}, "
        f"saved_repaired={saved_repaired}"
    )

# -------------------------------------------------
# Finalizar
# -------------------------------------------------

conn.commit()
conn.close()

print("\nAnálisis completado.")
print(f"Resultados guardados en: {DB_NAME}")
print("Tablas creadas:")
print("  - TSP_results_feasible")
print("  - TSP_results_repaired")