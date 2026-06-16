#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import argparse
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict
from scipy.optimize import curve_fit

# ------------------------------------------------
# PARÁMETROS
# ------------------------------------------------

INPUT_DIR = "./Results"
OUTPUT_DIR = "./Images_params_runtime"
os.makedirs(OUTPUT_DIR, exist_ok=True)

DEFAULT_COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']

# ------------------------------------------------
# ARGUMENTOS
# ------------------------------------------------

parser = argparse.ArgumentParser(description="Runtime vs params con ajuste avanzado")
parser.add_argument("--shots_to_plot", type=int, nargs="+", default=None,
                    help="Lista de shots a graficar")
args = parser.parse_args()

# ------------------------------------------------
# ESTRUCTURAS DE DATOS
# ------------------------------------------------

# time_vs_params[shots][k] = [(params, total_time)]
time_vs_params = defaultdict(lambda: defaultdict(list))

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
        shots = r["shots"]
        params = r["n_params"]
        total_time = r["total_time"]
        time_vs_params[shots][k].append((params, total_time))

# ------------------------------------------------
# ORDENAR DATOS
# ------------------------------------------------

for shots in time_vs_params:
    for k in time_vs_params[shots]:
        time_vs_params[shots][k] = sorted(
            time_vs_params[shots][k],
            key=lambda x: x[0]
        )

# ------------------------------------------------
# MODELOS DE AJUSTE
# ------------------------------------------------

def linear(x, a, b): return a*x + b
def power_law(x, a, b): return a * np.power(x, b)
def exponential(x, a, b): return a * np.exp(b*x)
def logarithmic(x, a, b): return a * np.log(x) + b

def fit_models(x, y):
    models = {"linear": linear, "power": power_law, "exp": exponential, "log": logarithmic}
    results = []
    for name, func in models.items():
        try:
            if name == "log" and np.any(x <= 0): 
                continue
            popt, _ = curve_fit(func, x, y, maxfev=20000)
            y_pred = func(x, *popt)
            mse = np.mean((y - y_pred)**2)
            results.append((name, func, popt, mse))
        except Exception:
            continue
    results.sort(key=lambda r: r[3])  # ordenar por MSE
    return results

# ------------------------------------------------
# PLOTEO
# ------------------------------------------------

def plot_individual(shots, k, data):
    plt.figure(figsize=(8,5))

    x = np.array([d[0] for d in data])
    y = np.array([d[1] for d in data]) / 3600  # convertir a horas

    mask = (x > 0) & (y > 0)
    x, y = x[mask], y[mask]

    if len(x) < 2:
        print(f"⚠ Muy pocos puntos para ajustar k={k}, shots={shots}")
        return

    # Ajuste modelos
    results = fit_models(x, y)
    if not results:
        print(f"⚠ No se pudo ajustar ningún modelo para k={k}, shots={shots}")
        return

    # Tomar los 2 mejores modelos para mostrar en la gráfica
    best_results = results[:1]

    # Plot datos
    plt.plot(x, y, "o", label="Data")

    x_fit = np.linspace(min(x), max(x), 300)

    # Diccionario para nombres “profesionales”
    model_names = {
        "linear": "LINEAR",
        "power": "POWER LAW",
        "exp": "EXPONENTIAL",
        "log": "LOGARITHMIC"
    }

    for name, func, popt, mse in best_results:
        y_fit = func(x_fit, *popt)
        display_name = model_names.get(name, name.upper())

        # Crear ecuación legible según el modelo
        if name == "linear":
            eq = f"y = {popt[0]:.2e}·x + {popt[1]:.2e}"
        elif name == "power":
            eq = f"y = {popt[0]:.2e}·x^{popt[1]:.2f}"
        elif name == "exp":
            eq = f"y = {popt[0]:.2e}·exp({popt[1]:.2f}·x)"
        elif name == "log":
            eq = f"y = {popt[0]:.2e}·ln(x) + {popt[1]:.2e}"
        else:
            eq = f"{display_name} fit"

        plt.plot(x_fit, y_fit, "--", label=f"{display_name}: {eq}\n(MSE={mse:.2e})")

    plt.xlabel("Number of parameters")
    plt.ylabel("Total time (h)")
    plt.title(f"Runtime vs Params (k={k}, {shots} shots)")
    plt.grid(True)
    plt.legend(fontsize=9)
    plt.tight_layout()

    filename = f"runtime_vs_params_k{k}_{shots}_shots.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()

    print(f"✔ {filename} | Mejores fits mostrados en la leyenda")

def plot_combined(shots, data_dict):
    plt.figure(figsize=(9,6))
    ks = sorted(data_dict.keys())
    for idx, k in enumerate(ks):
        data = data_dict[k]
        x = [d[0] for d in data]
        y = [d[1] / 3600 for d in data]
        plt.plot(
            x, y,
            marker="o",
            label=f"k={k}",
            color=DEFAULT_COLORS[idx % len(DEFAULT_COLORS)]
        )

    plt.xlabel("Number of parameters")
    plt.ylabel("Total time (h)")
    plt.title(f"Runtime vs Params ({shots} shots)")
    plt.grid(True)
    plt.legend()
    plt.tight_layout()

    filename = f"runtime_vs_params_ALL_{shots}_shots.png"
    plt.savefig(os.path.join(OUTPUT_DIR, filename), dpi=300)
    plt.close()
    print(f"✔ {filename} generada")

# ------------------------------------------------
# GENERAR GRÁFICAS
# ------------------------------------------------

shots_list = sorted(time_vs_params.keys()) if args.shots_to_plot is None else args.shots_to_plot

for shots in shots_list:
    if shots not in time_vs_params:
        print(f"⚠ No hay datos para {shots} shots")
        continue

    print(f"\n=== SHOTS: {shots} ===")

    for k, data in time_vs_params[shots].items():
        plot_individual(shots, k, data)

    plot_combined(shots, time_vs_params[shots])

print("\n✔ Todas las gráficas generadas en", OUTPUT_DIR)