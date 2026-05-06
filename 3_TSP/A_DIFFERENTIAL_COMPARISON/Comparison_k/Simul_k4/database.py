#!/usr/bin/env python3
# analyze_tsp_results.py
# Analiza JSONs en Resultados/TSP/... -> calcula distancias y mejora porcentual
# Solo considera benchmark Hybrid

import os
import json
import sqlite3
import re
from typing import List, Optional
import statistics

RESULTS_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_TSP/A_DIFFERENTIAL_COMPARISON/Comparison_k/Simul_k4/Resultados"
DB_NAME = "TSP_results_4.db"

# ------------------------
# Benchmark por instancia
# ------------------------
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

# ------------------------
# Función de mejora porcentual
# ------------------------
def mejora_porcentual(val_algo: float, val_bench: float) -> Optional[float]:
    if val_bench == "--":
        return None
    return (val_bench - val_algo) / val_bench * 100

# ------------------------
# Crear/abrir BD
# ------------------------
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute("""
    CREATE TABLE IF NOT EXISTS TSP_results (
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
    conn.commit()

# ------------------------
# Buscar archivos JSON
# ------------------------
json_files = []
for root, dirs, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.startswith("TSP") and file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"Encontrados {len(json_files)} JSONs en {RESULTS_DIR}")

# ------------------------
# Procesar cada JSON
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
    m = re.match(r"TSP_(\d+)_([A-Za-z0-9]+)_(\d+)\.json", filename)
    if not m:
        print(f"Archivo con nombre no esperado, se salta: {filename}")
        continue

    instance = f"tsp{m.group(1)}"
    optimizer = m.group(2)

    if instance not in benchmark:
        print(f"No hay benchmark para la instancia {instance}, saltando {filename}")
        continue

    all_initial_distances = []
    best_initial_distance = None
    refined_for_best_initial = None

    # Recorremos cada iteración
    for run_data in data.get("resultados", []):
        initial_distance = run_data.get("initial_distance")
        refined_distance = run_data.get("refined_distance")
        if initial_distance is None or refined_distance is None:
            continue

        all_initial_distances.append(initial_distance)

        # Guardamos el par asociado al menor initial_distance
        if best_initial_distance is None or initial_distance < best_initial_distance:
            best_initial_distance = initial_distance
            refined_for_best_initial = refined_distance

    if not all_initial_distances:
        print(f"No hay datos de distancia en {filename}, saltando")
        continue

    # Estadísticas de todas las initial_distance
    mean_initial = statistics.mean(all_initial_distances)
    std_initial = statistics.stdev(all_initial_distances) if len(all_initial_distances) > 1 else 0.0

    bench = benchmark[instance]
    mejora_initial = mejora_porcentual(best_initial_distance, bench)
    mejora_refined = mejora_porcentual(refined_for_best_initial, bench)

    # Guardar en la BD
    c.execute("""
    INSERT OR REPLACE INTO TSP_results
    (filename, instance, optimizer, best_initial_distance, refined_for_best_initial,
     mejora_initial, mejora_refined, mean_initial, std_initial, benchmark)
    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (filename, instance, optimizer, best_initial_distance, refined_for_best_initial,
          mejora_initial, mejora_refined, mean_initial, std_initial, bench))

    print(f"Procesado {filename}: best_initial={best_initial_distance}, refined={refined_for_best_initial}, "
          f"mejora_initial={mejora_initial}, mejora_refined={mejora_refined}")

conn.commit()
conn.close()
print("\nAnálisis completado. Resultados guardados en:", DB_NAME)
