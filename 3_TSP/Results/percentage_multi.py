#!/usr/bin/env python3
# graph_tsp_pct_feasible_and_best_feasible_all_k.py

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

DB_FILES_NO_REG = {
    2: "Comparison_k/TSP_results_feasible_vs_repaired_k2.db",
    3: "Comparison_k/TSP_results_feasible_vs_repaired_k3.db",
    4: "Comparison_k/TSP_results_feasible_vs_repaired_k4.db",
}

DB_FILES_REG = {
    2: "Comparison_reg/TSP_results_feasible_vs_repaired_k2.db",
    3: "Comparison_reg/TSP_results_feasible_vs_repaired_k3.db",
    4: "Comparison_reg/TSP_results_feasible_vs_repaired_k4.db",
}

FIG_DIR = "Images_pct_feasible"
os.makedirs(FIG_DIR, exist_ok=True)

BAR_WIDTH = 0.18

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

EDGE_COLOR = "black"
LINE_WIDTH = 0.8


def tiene_datos(vals):
    return any(v is not None and not np.isnan(v) for v in vals)


def cargar_porcentajes(db_files):
    data_feasible = defaultdict(lambda: defaultdict(dict))
    data_best = defaultdict(lambda: defaultdict(dict))

    for k, db_name in db_files.items():

        if not os.path.exists(db_name):
            print(f"⚠️ No existe {db_name}")
            continue

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        try:
            c.execute("""
            SELECT instance, optimizer,
                   feasible_percentage,
                   best_feasible_percentage
            FROM TSP_feasibility_counts
            """)
        except Exception as e:
            print(f"⚠️ Error leyendo TSP_feasibility_counts en {db_name}: {e}")
            conn.close()
            continue

        for instance, optimizer, pct_feasible, pct_best in c.fetchall():
            data_feasible[optimizer][instance][k] = (
                pct_feasible if pct_feasible is not None else np.nan
            )

            data_best[optimizer][instance][k] = (
                pct_best if pct_best is not None else np.nan
            )

        conn.close()

    return data_feasible, data_best


def limpiar_leyenda():
    handles, labels = plt.gca().get_legend_handles_labels()
    by_label = dict(zip(labels, handles))

    plt.legend(
        by_label.values(),
        by_label.keys(),
        loc="center left",
        bbox_to_anchor=(1, 0.5),
        frameon=True
    )


def get_offset(idx, group_width):
    return -group_width / 2 + idx * BAR_WIDTH


def graficar_porcentaje(data_no, data_reg, metric_name, ylabel, filename_suffix):

    optimizers = sorted(set(data_no) | set(data_reg))

    if not optimizers:
        print(f"⚠️ No hay datos para graficar {metric_name}.")
        return

    for opt in optimizers:

        print(f"📊 {metric_name} | Optimizer: {opt}")

        instancias = sorted(
            set(data_no[opt]) | set(data_reg[opt]),
            key=lambda x: int(x.replace("tsp", ""))
        )

        n_k = len(DB_FILES_NO_REG)
        n_barras = n_k * 2
        GROUP_WIDTH = n_barras * BAR_WIDTH

        x = np.arange(len(instancias)) * (GROUP_WIDTH + 0.5)

        plt.figure(figsize=(12, 4))

        for i, k in enumerate(DB_FILES_NO_REG):
            base = i * 2

            vals_no = [
                data_no[opt][inst].get(k, np.nan)
                for inst in instancias
            ]

            vals_reg = [
                data_reg[opt][inst].get(k, np.nan)
                for inst in instancias
            ]

            plt.bar(
                x + get_offset(base, GROUP_WIDTH),
                vals_no,
                width=BAR_WIDTH,
                color=COLORS_K[k],
                label=f"k={k} (No reg)" if tiene_datos(vals_no) else None
            )

            plt.bar(
                x + get_offset(base + 1, GROUP_WIDTH),
                vals_reg,
                width=BAR_WIDTH,
                color=COLORS_K[k],
                hatch="//",
                alpha=0.8,
                edgecolor=EDGE_COLOR,
                linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)" if tiene_datos(vals_reg) else None
            )

        plt.title(
            f"Simulation | Optimizer: {opt} | k=2,3,4 | {metric_name}"
        )
        plt.xlabel("TSP instance")
        plt.ylabel(ylabel)
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)
        plt.ylim(0, 110)

        limpiar_leyenda()
        plt.grid(axis="y", linestyle="--", alpha=0.7)

        plt.savefig(
            os.path.join(FIG_DIR, f"TSP_{opt}_{filename_suffix}.png"),
            dpi=200,
            bbox_inches="tight"
        )

        plt.close()


data_feasible_no, data_best_no = cargar_porcentajes(DB_FILES_NO_REG)
data_feasible_reg, data_best_reg = cargar_porcentajes(DB_FILES_REG)

graficar_porcentaje(
    data_feasible_no,
    data_feasible_reg,
    metric_name="Percentage of Feasible Solutions",
    ylabel="Perfect solutions (%)",
    filename_suffix="pct_perfect_all_k"
)

graficar_porcentaje(
    data_best_no,
    data_best_reg,
    metric_name="Percentage of the Best Solution Among All Feasible Solutions",
    ylabel="Best perfect initial solution frequency (%)",
    filename_suffix="pct_best_perfect_initial_all_k"
)


print("✅ Gráficas generadas en:", FIG_DIR)