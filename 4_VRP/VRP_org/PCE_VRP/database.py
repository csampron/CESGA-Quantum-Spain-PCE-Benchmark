#!/usr/bin/env python3

import os
import json
import sqlite3
import re
import glob

# ------------------------
# Configuración
# ------------------------
RESULTS_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/VRP_org/PCE_VRP/Resultados/VRP/k_2/Simulation"
DB_NAME = "VRP_results.db"

PENALTY = 10.0

# ---------------------------------------------------
# BENCHMARK
# ---------------------------------------------------
benchmark_data = {
    "4_1": {"tours": [[[0,1],[1,0]], [[0,2],[2,3],[3,0]]], "cost": 97, "capacity": 3},
    "4_2": {"tours": [[[0,1],[1,0]], [[0,2],[2,3],[3,0]]], "cost": 121, "capacity": 3},
    "5_1": {"tours": [[[0,1],[1,4],[4,0]], [[0,3],[3,2],[2,0]]], "cost": 94, "capacity": 3},
    "5_2": {"tours": [[[0,2],[2,0]], [[0,4],[4,1],[1,3],[3,0]]], "cost": 295, "capacity": 3},
    "6_1": {"tours": [[[0,1],[1,5],[5,2],[2,0]], [[0,4],[4,3],[3,0]]], "cost": 118, "capacity": 3},
    "6_2": {"tours": [[[0,1],[1,0]], [[0,5],[5,4],[4,2],[2,3],[3,0]]], "cost": 122, "capacity": 4},
    "7_1": {"tours": [[[0,2],[2,3],[3,1],[1,6],[6,4],[4,0]], [[0,5],[5,0]]], "cost": 119, "capacity": 4},
    "7_2": {"tours": [[[0,1],[1,2],[2,3],[3,4],[4,5],[5,0]], [[0,6],[6,0]]], "cost": 164, "capacity": 4},
    "8_1": {"tours": [[[0,1],[1,6],[6,2],[2,7],[7,5],[5,0]], [[0,3],[3,4],[4,0]]], "cost": 153, "capacity": 5},
    "8_2": {"tours": [[[0,4],[4,1],[1,3],[3,2],[2,7],[7,5],[5,0]], [[0,6],[6,0]]], "cost": 269, "capacity": 5},
}

# ---------------------------------------------------
# BENCHMARK OVER CAPACITY (CORRECTO)
# ---------------------------------------------------
def benchmark_over_capacity(tours, capacity):
    over = 0

    for tour in tours:
        visited = set()

        for edge in tour:
            visited.update(edge)

        visited.discard(0)

        excess = len(visited) - capacity
        if excess > 0:
            over += excess

    return over

# ---------------------------------------------------
# MÉTRICAS (CORREGIDAS)
# ---------------------------------------------------
def metricas(best_cost, bench_cost, bench_over):

    # penalización SOLO si benchmark es infactible
    bench_pen = bench_cost + PENALTY * bench_over

    # mejora respecto benchmark puro (siempre)
    mejora = (bench_cost - best_cost) / bench_cost * 100

    # delta SOLO tiene sentido si hay infactibilidad
    if bench_over > 0:
        delta = (best_cost - bench_pen) / bench_pen * 100
    else:
        delta = np.nan

    return mejora, delta

# ---------------------------------------------------
# CREAR DB
# ---------------------------------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()

    c.execute("""
    CREATE TABLE IF NOT EXISTS VRP_results (
        filename TEXT PRIMARY KEY,
        instance TEXT,
        optimizer TEXT,

        total_runs INTEGER,
        feasible_ratio REAL,

        best_cost REAL,
        best_count INTEGER,

        alpha REAL,
        beta REAL,

        over_capacity INTEGER,
        benchmark_over_capacity INTEGER,

        mejora REAL,
        delta REAL
    )
    """)

    conn.commit()

# ---------------------------------------------------
# JSONs
# ---------------------------------------------------
json_files = glob.glob(os.path.join(RESULTS_DIR, "**", "VRP_*.json"), recursive=True)

print(f"Encontrados {len(json_files)} JSONs")

# ---------------------------------------------------
# PROCESAMIENTO
# ---------------------------------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()

    for ruta in sorted(json_files):

        with open(ruta, "r") as f:
            data = json.load(f)

        filename = os.path.basename(ruta)

        m = re.match(r"VRP_(\d+)_(\d+)_([A-Z]+)_(\d+)\.json", filename)
        if not m:
            continue

        num_ver = m.group(1)
        inst_id = m.group(2)
        optimizer = m.group(3)

        key = f"{num_ver}_{inst_id}"

        if key not in benchmark_data:
            continue

        bench = benchmark_data[key]
        capacity = bench["capacity"]

        results = data.get("resultados", [])
        if not results:
            continue

        total_runs = len(results)
        feasible_runs = 0

        costs = []

        for res in results:

            if res.get("initial_feasible", False):
                feasible_runs += 1

            cost = res.get("refined_cost")
            if cost is not None:
                costs.append(cost)

        # -----------------------------
        # BEST REAL
        # -----------------------------
        if costs:
            best_cost = min(costs)
            best_count = costs.count(best_cost)
        else:
            best_cost = np.nan
            best_count = 0

        feasible_ratio = feasible_runs / total_runs if total_runs else 0

        # -----------------------------
        # BENCHMARK OVER CAPACITY
        # -----------------------------
        bench_over = benchmark_over_capacity(bench["tours"], capacity)

        # -----------------------------
        # MÉTRICAS CONSISTENTES
        # -----------------------------
        mejora, delta = metricas(best_cost, bench["cost"], bench_over)

        # -----------------------------
        # INSERT DB
        # -----------------------------
        c.execute("""
        INSERT OR REPLACE INTO VRP_results
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            filename,
            key,
            optimizer,

            total_runs,
            feasible_ratio,

            best_cost,
            best_count,

            None,
            None,

            0,
            bench_over,

            mejora,
            delta
        ))

        print(
            f"{filename} | best={best_cost:.2f} | feas={feasible_ratio:.2f} | "
            f"bench_over={bench_over} | mejora={mejora:.2f}% | delta={delta if not np.isnan(delta) else None}"
        )

print("\n✅ DB corregida y completamente consistente")