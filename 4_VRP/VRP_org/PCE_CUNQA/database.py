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

# ------------------------
# Benchmark
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
            visited.add(edge[0])
            visited.add(edge[1])
        visited.discard(0)
        if len(visited) > capacity:
            over += len(visited) - capacity
    return over

def metricas_vrp(total_cost, benchmark_cost, over_capacity, bench_over_capacity, penalty=10.0):
    benchmark_penalized = benchmark_cost + penalty * bench_over_capacity
    delta_coste = (total_cost - benchmark_penalized) / benchmark_penalized * 100
    mejora = (benchmark_penalized - total_cost) / benchmark_penalized * 100
    return mejora, delta_coste

# ------------------------
# Crear la base de datos si no existe
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS VRP_results (
        id TEXT PRIMARY KEY,
        filename TEXT,
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
# Leer todos los JSONs
# ------------------------
json_files = glob.glob(os.path.join(RESULTS_DIR, "**", "VRP_*.json"), recursive=True)
print(f"Encontrados {len(json_files)} JSONs")

conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

# ------------------------
# Procesar cada JSON
# ------------------------
for ruta in sorted(json_files):
    with open(ruta, "r") as f:
        data = json.load(f)

    filename = os.path.basename(ruta)
    
    # Extraer num_ver, optimizer y k
    m = re.match(r"VRP_(\d+)_([A-Z]+)_(\d+)\.json", filename)
    if not m:
        print(f"Nombre no coincide con patrón: {filename}")
        continue

    num_ver = m.group(1)
    optimizer = m.group(2)
    k = m.group(3)
    key = f"{num_ver}_{k}"

    if key not in benchmark_data:
        print(f"No hay benchmark para {key}, se omite")
        continue

    bench = benchmark_data[key]
    capacity = bench["capacity"]
    bench_over = benchmark_over_capacity(bench["tours"], capacity)

    # Iterar sobre los resultados dentro del JSON
    for idx, res in enumerate(data.get("resultados", [])):
        total_cost = res.get("refined_cost", 0.0)
        routes = res.get("refined_routes", {})

        # Calcular over_capacity
        over_capacity = 0
        for route in routes.values():
            clients = [n for n in route if n != 0]
            if len(clients) > capacity:
                over_capacity += len(clients) - capacity

        # Métricas
        mejora, delta_coste = metricas_vrp(
            total_cost,
            bench["cost"],
            over_capacity,
            bench_over
        )

        # ID único por resultado
        unique_id = f"{filename}_{idx}"

        # Insertar en BD
        c.execute("""
        INSERT OR REPLACE INTO VRP_results
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            unique_id,
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
            f"{unique_id}: cost={total_cost:.2f}, "
            f"over={over_capacity}, "
            f"mejora={mejora:.2f}%, "
            f"delta={delta_coste:+.2f}%"
        )

conn.commit()
conn.close()
print("\n✅ Análisis VRP completado")