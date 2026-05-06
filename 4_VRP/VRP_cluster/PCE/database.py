#!/usr/bin/env python3
# analyze_vrp_results.py
# Analiza JSONs en Resultados/VRP/... -> calcula total_cost y métricas VRP correctas

import os
import json
import sqlite3
import re

# ------------------------
# Configuración
# ------------------------
RESULTS_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/VRP_cluster/PCE_TSP_2/Resultados/VRP/Simulation"
DB_NAME = "VRP_results.db"

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
# Capacidad violada en benchmark
# ------------------------
def benchmark_over_capacity(tours, capacity):
    over = 0
    for tour in tours:
        visited = set()
        for edge in tour:
            visited.add(edge[0])
            visited.add(edge[1])
        visited.discard(0)
        if len(visited) > capacity:
            over += len(visited) - capacity
    return over

# ------------------------
# Métricas VRP correctas
# ------------------------
def metricas_vrp(total_cost, benchmark_cost, bench_over_capacity, penalty=10.0):
    """
    Calcula las métricas de evaluación para VRP:
    - delta_coste: % de sobrecoste/ahorro respecto al benchmark penalizado
    - mejora: % de mejora frente al benchmark penalizado (ranking)
    
    Parámetros:
    - total_cost: coste de la solución propuesta (siempre factible)
    - benchmark_cost: coste de la solución de referencia
    - bench_over_capacity: exceso de capacidad del benchmark
    - penalty: factor de penalización por exceso de capacidad
    
    Devuelve:
    - mejora: float
    - delta_coste: float
    """

    # Calcular coste penalizado del benchmark
    benchmark_penalized = benchmark_cost + penalty * bench_over_capacity

    # Delta coste (descriptivo)
    delta_coste = (total_cost - benchmark_penalized) / benchmark_penalized * 100

    # Mejora porcentual (ranking)
    mejora = (benchmark_penalized - total_cost) / benchmark_penalized * 100

    return mejora, delta_coste


# ------------------------
# Crear BD
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS VRP_results (
        filename TEXT PRIMARY KEY,
        instance TEXT,
        optimizer TEXT,
        total_cost REAL,
        over_capacity INTEGER,
        benchmark_over_capacity INTEGER,
        mejora_penalizada REAL,
        delta_coste REAL
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

    filename = os.path.basename(ruta)
    m = re.match(r"Sol_(\d+)_vertices_inst_(\d+)\.json", filename)
    if not m:
        continue

    num_ver = m.group(1)
    inst = m.group(2)
    key = f"{num_ver}_{inst}"

    if key not in benchmark_data:
        continue

    optimizer = data.get("optimizer", "UNKNOWN")
    total_cost = data.get("total_cost", 0.0)

    # ------------------------
    # TU solución: violación
    # ------------------------
    over_capacity = 0
    capacity = benchmark_data[key]["capacity"]

    for cl in data.get("clusters", []):
        tour = cl.get("refined_tour", [])
        clients = [n for n in tour if n != 1]
        if len(clients) > capacity:
            over_capacity += len(clients) - capacity

    # ------------------------
    # BENCHMARK: violación
    # ------------------------
    bench = benchmark_data[key]
    bench_over = benchmark_over_capacity(bench["tours"], bench["capacity"])

    # ------------------------
    # Métricas
    # ------------------------
    mejora, delta_coste = metricas_vrp(
        total_cost,
        bench["cost"],
        over_capacity,
        bench_over
    )

    # ------------------------
    # Guardar
    # ------------------------
    c.execute("""
    INSERT OR REPLACE INTO VRP_results
    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (
        filename,
        key,
        optimizer,
        total_cost,
        over_capacity,
        bench_over,
        mejora,
        delta_coste
    ))

    print(
        f"{filename}: "
        f"cost={total_cost:.2f}, "
        f"over={over_capacity}, "
        f"bench_over={bench_over}, "
        f"mejora={mejora:.2f}%, "
        f"delta_coste={delta_coste:+.2f}%"
    )

conn.commit()
conn.close()

print("\n✅ Análisis VRP completado")
