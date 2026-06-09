#!/usr/bin/env python3
# graph_multi_compare_feasible_combinatorial.py

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

DB_FILES_NO_REG = {
    2: "Comparison_k/BIN_results_feasible_vs_combinatorial_k2.db",
    3: "Comparison_k/BIN_results_feasible_vs_combinatorial_k3.db",
    4: "Comparison_k/BIN_results_feasible_vs_combinatorial_k4.db",
}

DB_FILES_REG = {
    2: "Comparison_reg/BIN_results_feasible_vs_combinatorial_k2.db",
    3: "Comparison_reg/BIN_results_feasible_vs_combinatorial_k3.db",
    4: "Comparison_reg/BIN_results_feasible_vs_combinatorial_k4.db",
}

TABLES = {
    "feasible": "BIN_results_feasible",
    "combinatorial": "BIN_results_combinatorial",
}

BAR_WIDTH = 0.18

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

EDGE_COLOR = "black"
LINE_WIDTH = 0.8

benchmark_bins_by_n = {
    3:  [[2], [], [0, 1]],
    4:  [[1, 2], [], [], [0, 3]],
    5:  [[], [], [0, 1], [], [2, 3, 4]],
    6:  [[], [1, 5], [], [2, 3], [], [0, 4]],
    7:  [[3, 4], [], [0, 1], [5], [2, 6], [], []],
    8:  [[], [1, 5], [4], [0, 3], [], [], [2, 6, 7], []],
    9:  [[], [2, 5, 8], [0, 1], [], [6], [3, 4, 7], [], [], []],
    10: [[0, 1], [3, 5], [], [2], [6, 7], [], [8], [], [4, 9], []],
    12: [[], [1, 3], [0, 6], [7], [], [4, 10], [2, 9, 11], [], [8], [], [], [5]],
    14: [[], [], [], [], [3, 6], [], [2], [1], [], [0], [4, 9, 12], [], [8, 10, 11], [5, 7, 13]],
}

BENCHMARK = {
    f"bin{n}": sum(1 for b in bins if len(b) > 0)
    for n, bins in benchmark_bins_by_n.items()
}


def tiene_datos(vals):
    return any(v is not None and not np.isnan(v) for v in vals)


def cargar_datos(db_files, table_name):
    data = defaultdict(lambda: defaultdict(lambda: defaultdict(dict)))

    for k, db_name in db_files.items():
        if not os.path.exists(db_name):
            print(f"⚠️ No existe {db_name}")
            continue

        conn = sqlite3.connect(db_name)
        c = conn.cursor()

        try:
            c.execute(f"""
            SELECT instance, optimizer,
                   mejora_initial, mejora_post,
                   mean_initial_bins, std_initial_bins,
                   post_for_best_initial,
                   best_initial_bins
            FROM {table_name}
            """)
        except Exception as e:
            print(f"⚠️ No se pudo leer {table_name} en {db_name}: {e}")
            conn.close()
            continue

        for inst, opt, mi, mp, mean_i, std_i, post_best, best_initial in c.fetchall():
            data[opt][inst][k] = {
                "mejora_initial": mi,
                "mejora_post": mp,
                "mean_initial_bins": mean_i,
                "std_initial_bins": std_i,
                "post_best": post_best,
                "best_initial": best_initial,
            }

        conn.close()

    return data


def get_value(data, opt, inst, k, key):
    val = data[opt][inst].get(k, {}).get(key, np.nan)
    return np.nan if val is None else val


def get_std_value(data, opt, inst, k):
    val = get_value(data, opt, inst, k, "std_initial_bins")
    return 0.0 if val is None or np.isnan(val) else val


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


def calcular_ylim_global(metric_key, include_benchmark=False):
    valores = []

    for table_name in TABLES.values():
        data_no = cargar_datos(DB_FILES_NO_REG, table_name)
        data_reg = cargar_datos(DB_FILES_REG, table_name)

        for data in [data_no, data_reg]:
            for opt in data:
                for inst in data[opt]:
                    for k in data[opt][inst]:
                        val = data[opt][inst][k].get(metric_key, np.nan)
                        if val is not None and not np.isnan(val):
                            valores.append(val)

        if include_benchmark:
            valores.extend(BENCHMARK.values())

    if not valores:
        return None

    ymin = min(valores)
    ymax = max(valores)

    margen = 0.05 * (ymax - ymin) if ymax != ymin else 1.0

    return ymin - margen, ymax + margen


YLIMS = {
    "mejora_initial": calcular_ylim_global("mejora_initial"),
    "mejora_post": calcular_ylim_global("mejora_post"),
    "mean_initial_bins": calcular_ylim_global("mean_initial_bins", include_benchmark=True),
    "best_initial": calcular_ylim_global("best_initial", include_benchmark=True),
    "post_best": calcular_ylim_global("post_best", include_benchmark=True),
}


def generar_graficas(result_type, table_name):
    fig_dir = f"Images_comparison_{result_type}"
    os.makedirs(fig_dir, exist_ok=True)

    data_no = cargar_datos(DB_FILES_NO_REG, table_name)
    data_reg = cargar_datos(DB_FILES_REG, table_name)

    optimizers = sorted(set(data_no) | set(data_reg))

    if not optimizers:
        print(f"⚠️ No hay datos para {result_type}")
        return

    for opt in optimizers:
        print(f"📊 {result_type} | {opt}")

        instancias = sorted(
            set(data_no[opt]) | set(data_reg[opt]),
            key=lambda x: int(x.replace("bin", ""))
        )

        n_k = len(DB_FILES_NO_REG)
        n_barras = n_k * 2 + 1
        GROUP_WIDTH = n_barras * BAR_WIDTH

        x = np.arange(len(instancias)) * (GROUP_WIDTH + 0.5)

        benchmark_vals = [
            BENCHMARK.get(inst, np.nan)
            for inst in instancias
        ]

                # 3. MEDIA INITIAL + STD
        plt.figure(figsize=(12, 4))

        plt.bar(x + get_offset(0, GROUP_WIDTH), benchmark_vals, width=BAR_WIDTH,
                color="grey", label="Benchmark")

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            medias_no = [get_value(data_no, opt, inst, k, "mean_initial_bins") for inst in instancias]
            medias_reg = [get_value(data_reg, opt, inst, k, "mean_initial_bins") for inst in instancias]

            stds_no = [get_std_value(data_no, opt, inst, k) for inst in instancias]
            stds_reg = [get_std_value(data_reg, opt, inst, k) for inst in instancias]

            plt.bar(x + get_offset(base, GROUP_WIDTH), medias_no, width=BAR_WIDTH,
                    color=COLORS_K[k], yerr=stds_no, capsize=5,
                    error_kw={"elinewidth": 0.8, "ecolor": "black"},
                    label=f"k={k} (No reg)" if tiene_datos(medias_no) else None)

            plt.bar(x + get_offset(base + 1, GROUP_WIDTH), medias_reg, width=BAR_WIDTH,
                    color=COLORS_K[k], yerr=stds_reg, capsize=5,
                    error_kw={"elinewidth": 0.8, "ecolor": "black"},
                    hatch="//", alpha=0.8,
                    edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                    label=f"k={k} (Reg)" if tiene_datos(medias_reg) else None)

        plt.title(f"Simulation | {result_type} | Optimizer: {opt} | Mean Initial Number of Bins")
        plt.ylabel("Number of bins")
        plt.xticks(x, [i.replace("bin", "") for i in instancias], rotation=45)
        limpiar_leyenda()
        if YLIMS["mean_initial_bins"] is not None:
            plt.ylim(YLIMS["mean_initial_bins"])
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(f"{fig_dir}/{result_type}_compare_mean_initial_bins.png", bbox_inches="tight", dpi=200)
        plt.close()

        # 4. BEST INITIAL
        plt.figure(figsize=(12, 4))

        plt.bar(x + get_offset(0, GROUP_WIDTH), benchmark_vals, width=BAR_WIDTH,
                color="grey", label="Benchmark")

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            vals_no = [get_value(data_no, opt, inst, k, "best_initial") for inst in instancias]
            vals_reg = [get_value(data_reg, opt, inst, k, "best_initial") for inst in instancias]

            plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no, width=BAR_WIDTH,
                    color=COLORS_K[k], label=f"k={k} (No reg)" if tiene_datos(vals_no) else None)

            plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg, width=BAR_WIDTH,
                    color=COLORS_K[k], hatch="//", alpha=0.8,
                    edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                    label=f"k={k} (Reg)" if tiene_datos(vals_reg) else None)

        plt.title(f"Simulation | {result_type} | Optimizer: {opt} | Best Initial Number of Bins")
        plt.ylabel("Number of bins")
        plt.xticks(x, [i.replace("bin", "") for i in instancias], rotation=45)
        limpiar_leyenda()
        if YLIMS["best_initial"] is not None:
            plt.ylim(YLIMS["best_initial"])
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(f"{fig_dir}/{result_type}_compare_best_initial_bins.png", bbox_inches="tight", dpi=200)
        plt.close()

        # 5. POST FOR BEST INITIAL
        plt.figure(figsize=(12, 4))

        plt.bar(x + get_offset(0, GROUP_WIDTH), benchmark_vals, width=BAR_WIDTH,
                color="grey", label="Benchmark")

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            vals_no = [get_value(data_no, opt, inst, k, "post_best") for inst in instancias]
            vals_reg = [get_value(data_reg, opt, inst, k, "post_best") for inst in instancias]

            plt.bar(x + get_offset(base, GROUP_WIDTH), vals_no, width=BAR_WIDTH,
                    color=COLORS_K[k], label=f"k={k} (No reg)" if tiene_datos(vals_no) else None)

            plt.bar(x + get_offset(base + 1, GROUP_WIDTH), vals_reg, width=BAR_WIDTH,
                    color=COLORS_K[k], hatch="//", alpha=0.8,
                    edgecolor=EDGE_COLOR, linewidth=LINE_WIDTH,
                    label=f"k={k} (Reg)" if tiene_datos(vals_reg) else None)

        plt.title(f"Simulation | {result_type} | Optimizer: {opt} | Best Post Processed Number of Bins")
        plt.ylabel("Number of bins")
        plt.xticks(x, [i.replace("bin", "") for i in instancias], rotation=45)
        limpiar_leyenda()
        if YLIMS["post_best"] is not None:
            plt.ylim(YLIMS["post_best"])
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(f"{fig_dir}/{result_type}_compare_post_best_bins.png", bbox_inches="tight", dpi=200)
        plt.close()


for result_type, table_name in TABLES.items():
    generar_graficas(result_type, table_name)

print("✅ Comparación completada")