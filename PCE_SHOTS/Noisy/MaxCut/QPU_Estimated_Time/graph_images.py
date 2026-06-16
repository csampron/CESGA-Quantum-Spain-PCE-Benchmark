#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
import matplotlib.pyplot as plt
from collections import defaultdict

# ------------------------------------------------
# PARÁMETROS
# ------------------------------------------------

INPUT_DIR = "./Results"
OUTPUT_DIR = "./Images"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEFAULT_COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

# ------------------------------------------------
# ARGUMENTOS
# ------------------------------------------------

parser = argparse.ArgumentParser(description="Graficar Results de experimentos")
parser.add_argument("--shots_to_plot", type=int, nargs="+", default=None,
                    help="Lista de valores de shots a graficar. Ej: --shots_to_plot 1000 100000")
args = parser.parse_args()

# ------------------------------------------------
# ESTRUCTURAS DE DATOS
# ------------------------------------------------

# (size, qubits, depth, params, teo_layers)
structure_results = defaultdict(list)

# time_results[shots][k] = [(size, total_time)]
time_results = defaultdict(lambda: defaultdict(list))

# ------------------------------------------------
# LEER JSON
# ------------------------------------------------

for fname in os.listdir(INPUT_DIR):

    if not fname.endswith(".json"):
        continue

    with open(os.path.join(INPUT_DIR, fname)) as f:
        data = json.load(f)

    if "Results" not in data:
        continue

    for r in data["Results"]:

        k = r["k"]
        size = r["tamano"]
        shots = r["shots"]

        qubits = r["qubits"]
        depth = r["n_profundidad"]
        params = r["n_params"]
        teo_layers = r["teo_layers"]

        average_time = r["average_time"]
        total_time = r["total_time"]

        structure_results[k].append((size, qubits, depth, params, teo_layers))
        time_results[shots][k].append((size, total_time))

# ------------------------------------------------
# ORDENAR DATOS
# ------------------------------------------------

for k in structure_results:
    structure_results[k] = sorted(structure_results[k], key=lambda x: x[0])

for shots in time_results:
    for k in time_results[shots]:
        time_results[shots][k] = sorted(time_results[shots][k], key=lambda x: x[0])

# ------------------------------------------------
# FUNCIONES DE PLOTEO
# ------------------------------------------------

def plot_structure(metric_index, ylabel, filename):

    plt.figure(figsize=(10,5))
    ks = sorted(structure_results.keys())

    for idx, k in enumerate(ks):

        data = structure_results[k]

        x = [d[0] for d in data]
        y = [d[metric_index] for d in data]

        plt.plot(
            x,
            y,
            marker="o",
            label=f"k={k}",
            color=COLORS_K.get(k, DEFAULT_COLORS[idx % len(DEFAULT_COLORS)])
        )

    plt.xlabel("Number of variables")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} vs Number of variables")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

    print(f"✔ {filename} generada")


def plot_depth_vs_params():

    plt.figure(figsize=(10,5))
    ks = sorted(structure_results.keys())

    for idx, k in enumerate(ks):

        data = structure_results[k]

        depth = [d[2] for d in data]
        params = [d[3] for d in data]

        plt.plot(
            depth,
            params,
            marker="o",
            label=f"k={k}",
            color=COLORS_K.get(k, DEFAULT_COLORS[idx % len(DEFAULT_COLORS)])
        )

    plt.xlabel("Depth")
    plt.ylabel("Number of parameters")
    plt.title("Number of parameters vs Depth")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    filename = "params_vs_depth.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

    print(f"✔ {filename} generada")

# ------------------------------------------------
# GRAFICAS ESTRUCTURALES
# ------------------------------------------------

plot_structure(1, "Number of qubits", "qubits_vs_nodes.png")
plot_structure(2, "Depth", "depth_vs_nodes.png")
plot_structure(3, "Number of parameters", "params_vs_nodes.png")
plot_structure(4, "Theoretical layers", "teo_layers_vs_nodes.png")

# NUEVA GRÁFICA
plot_depth_vs_params()

# ------------------------------------------------
# GRAFICAS DE RUNTIME POR SHOTS
# ------------------------------------------------

shots_list = sorted(time_results.keys()) if args.shots_to_plot is None else args.shots_to_plot

for shots in shots_list:

    if shots not in time_results:
        print(f"⚠ No hay datos para {shots} shots, se omite.")
        continue

    plt.figure(figsize=(10,5))

    ks = sorted(time_results[shots].keys())

    for idx, k in enumerate(ks):

        data = time_results[shots][k]

        x = [d[0] for d in data]
        y = [d[1] / 3600 for d in data]   # convertir a horas

        plt.plot(
            x,
            y,
            marker="o",
            label=f"k={k}",
            color=COLORS_K.get(k, DEFAULT_COLORS[idx % len(DEFAULT_COLORS)])
        )

    plt.xlabel("Number of variables")
    plt.ylabel("Total time (h)")
    plt.title(f"Runtime vs Number of variables ({shots} shots)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    filename = f"runtime_vs_variables_{shots}_shots.png"

    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

    print(f"✔ {filename} generada")

print("✔ Todas las gráficas generadas en", OUTPUT_DIR)