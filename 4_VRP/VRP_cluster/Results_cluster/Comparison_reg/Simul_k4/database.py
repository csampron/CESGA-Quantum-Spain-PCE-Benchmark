#!/usr/bin/env python3
# analyze_vrp_results_stats.py
# Analiza JSONs en VRP, calcula métricas y estadísticas por archivo

import os
import json
import sqlite3
import re
import numpy as np

# ------------------------
# Configuración
# ------------------------
RESULTS_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/A_DIFFERENTIAL_COMPARISON_cluster_int/Comparison_reg/Simul_k4/Resultados/VRP/Simulation/k4"
DB_NAME = "VRP_results.db"
PENALTY = 10.0

# ------------------------
# Benchmark VRP
# ------------------------
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

# ------------------------
# Funciones auxiliares
# ------------------------
def benchmark_over_capacity(tours, capacity):
    over = 0
    for tour in tours:
        visited = set()
        for edge in tour:
            visited.update(edge)
        visited.discard(0)
        if len(visited) > capacity:
            over += len(visited) - capacity
    return over

def metricas_vrp(total_cost, benchmark_cost, bench_over_capacity, penalty=PENALTY):
    benchmark_penalized = benchmark_cost + penalty * bench_over_capacity
    delta_coste = (total_cost - benchmark_penalized) / benchmark_penalized * 100
    mejora = (benchmark_penalized - total_cost) / benchmark_penalized * 100
    return mejora, delta_coste

def over_capacity_solution(clusters, capacity):
    over = 0
    for cl in clusters:
        tour = cl.get("refined_tour", [])
        clients = set(tour)
        clients.discard(0)  # depósito
        if len(clients) > capacity:
            over += len(clients) - capacity
    return over

# ------------------------
# Crear base de datos
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS VRP_results (
        filename TEXT PRIMARY KEY,
        instance TEXT,
        optimizer TEXT,
        best_total_cost REAL,
        over_capacity INTEGER,
        benchmark_over_capacity INTEGER,
        mejora_penalizada REAL,
        delta_coste REAL,
        mean_total_cost REAL,
        std_total_cost REAL
    )
    """)
    conn.commit()

# ------------------------
# Buscar JSONs
# ------------------------
json_files = []
for root, _, files in os.walk(RESULTS_DIR):
    for f in files:
        if f.startswith("Sol_") and f.endswith(".json"):
            json_files.append(os.path.join(root, f))
print(f"Encontrados {len(json_files)} JSONs")

# ------------------------
# Procesar resultados
# ------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

for ruta in sorted(json_files):
    with open(ruta, "r") as f:
        data = json.load(f)

    if "experiments" not in data or len(data["experiments"]) == 0:
        continue

    exp_list = data["experiments"]
    filename = os.path.basename(ruta)
    num_ver = str(exp_list[0]["num_ver"])
    inst = str(exp_list[0]["instancia"])
    key = f"{num_ver}_{inst}"

    if key not in benchmark_data:
        continue

    capacity = benchmark_data[key]["capacity"]
    bench = benchmark_data[key]
    bench_over = benchmark_over_capacity(bench["tours"], capacity)
    bench_cost = bench["cost"]

    # Recopilar total_costs de todas las ejecuciones
    total_costs = []
    over_caps = []

    for exp in exp_list:
        tc = exp["total_cost"]
        total_costs.append(tc)
        clusters = exp.get("clusters", [])
        over = over_capacity_solution(clusters, capacity)
        over_caps.append(over)

    # Estadísticas
    best_idx = np.argmin(total_costs)
    best_total = total_costs[best_idx]
    over_best = over_caps[best_idx]
    mean_total = float(np.mean(total_costs))
    std_total = float(np.std(total_costs))

    # Métricas
    mejora, delta_coste = metricas_vrp(best_total, bench_cost, bench_over)

    # Guardar en BD
    c.execute("""
    INSERT OR REPLACE INTO VRP_results
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        key,
        exp_list[0].get("optimizer", "UNKNOWN"),
        best_total,
        over_best,
        bench_over,
        mejora,
        delta_coste,
        mean_total,
        std_total
    ))

    print(f"{filename}: best={best_total:.2f}, over={over_best}, bench_over={bench_over}, "
          f"mejora={mejora:.2f}%, delta={delta_coste:+.2f}%, mean={mean_total:.2f}, std={std_total:.2f}")

conn.commit()
conn.close()
print("\n✅ Análisis VRP completado con estadísticas de múltiples ejecuciones")
