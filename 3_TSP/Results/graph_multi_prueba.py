#!/usr/bin/env python3
# graph_multi_compare_feasible_repaired.py

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

TABLES = {
    "feasible": "TSP_results_feasible",
    "repaired": "TSP_results_repaired",
}

BAR_WIDTH = 0.18

COLORS_K = {
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
}

EDGE_COLOR = "black"
LINE_WIDTH = 0.8

BENCHMARK = {
    "tsp4": 6700, "tsp5": 6786, "tsp6": 9815,
    "tsp7": 7245, "tsp8": 2794, "tsp9": 2438,
    "tsp10": 3155, "tsp15": 5268,
    "tsp22": 13005, "tsp25": 83132,
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
                   mejora_initial, mejora_refined,
                   mean_initial, std_initial,
                   refined_for_best_initial,
                   best_initial_distance
            FROM {table_name}
            """)
        except Exception as e:
            print(f"⚠️ No se pudo leer {table_name} en {db_name}: {e}")
            conn.close()
            continue

        for inst, opt, mi, mr, mean_i, std_i, refined_best, best_initial in c.fetchall():
            data[opt][inst][k] = {
                "mejora_initial": mi,
                "mejora_refined": mr,
                "mean_initial": mean_i,
                "std_initial": std_i,
                "refined_best": refined_best,
                "best_initial": best_initial,
            }

        conn.close()

    return data


def get_value(data, opt, inst, k, key):
    return data[opt][inst].get(k, {}).get(key, np.nan)


def get_std_value(data, opt, inst, k):
    val = get_value(data, opt, inst, k, "std_initial")
    return 0.0 if np.isnan(val) else val



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
    "mejora_refined": calcular_ylim_global("mejora_refined"),
    "mean_initial": calcular_ylim_global("mean_initial", include_benchmark=True),
    "best_initial": calcular_ylim_global("best_initial", include_benchmark=True),
    "refined_best": calcular_ylim_global("refined_best", include_benchmark=True),
}


def generar_graficas(result_type, table_name):

    fig_dir = f"Images_comparison_{result_type}"
    os.makedirs(fig_dir, exist_ok=True)

    data_no = cargar_datos(DB_FILES_NO_REG, table_name)
    data_reg = cargar_datos(DB_FILES_REG, table_name)

    # IMPORTANTE:
    # Unión, no intersección.
    # Así no se pierden optimizers que solo existan en reg o no_reg.
    optimizers = sorted(set(data_no) | set(data_reg))

    if not optimizers:
        print(f"⚠️ No hay datos para {result_type}")
        return

    for opt in optimizers:

        print(f"📊 {result_type} | {opt}")

        # También unión de instancias.
        instancias = sorted(
            set(data_no[opt]) | set(data_reg[opt]),
            key=lambda x: int(x.replace("tsp", ""))
        )

        n_k = len(DB_FILES_NO_REG)
        n_barras = n_k * 2 + 1
        GROUP_WIDTH = n_barras * BAR_WIDTH

        x = np.arange(len(instancias)) * (GROUP_WIDTH + 0.5)

        # =================================================
        # 1. MEJORA INITIAL
        # =================================================
        plt.figure(figsize=(12, 4))

        for i, k in enumerate(DB_FILES_NO_REG):
            base = i * 2

            vals_no = [
                get_value(data_no, opt, inst, k, "mejora_initial")
                for inst in instancias
            ]

            vals_reg = [
                get_value(data_reg, opt, inst, k, "mejora_initial")
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
            f"Simulation | {result_type} | Optimizer: {opt} | "
            f"k=2,3,4 | Initial improvement"
        )
        plt.ylabel("%")
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

        limpiar_leyenda()

        if YLIMS["mejora_initial"] is not None:
            plt.ylim(YLIMS["mejora_initial"])

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(
            f"{fig_dir}/{result_type}_compare_mejora_initial.png",
            bbox_inches="tight",
            dpi=200
        )
        plt.close()

        # =================================================
        # 2. MEJORA REFINED
        # =================================================
        plt.figure(figsize=(12, 4))

        for i, k in enumerate(DB_FILES_NO_REG):
            base = i * 2

            vals_no = [
                get_value(data_no, opt, inst, k, "mejora_refined")
                for inst in instancias
            ]

            vals_reg = [
                get_value(data_reg, opt, inst, k, "mejora_refined")
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
            f"Simulation | {result_type} | Optimizer: {opt} | "
            f"k=2,3,4 | Refined improvement"
        )
        plt.ylabel("%")
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

        limpiar_leyenda()
        
        if YLIMS["mejora_refined"] is not None:
            plt.ylim(YLIMS["mejora_refined"])

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(
            f"{fig_dir}/{result_type}_compare_mejora_refined.png",
            bbox_inches="tight",
            dpi=200
        )
        plt.close()

        # =================================================
        # 3. MEDIA + STD
        # =================================================
        plt.figure(figsize=(12, 4))

        benchmark_vals = [
            BENCHMARK.get(inst, np.nan)
            for inst in instancias
        ]

        plt.bar(
            x + get_offset(0, GROUP_WIDTH),
            benchmark_vals,
            width=BAR_WIDTH,
            color="grey",
            label="Benchmark"
        )

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            medias_no = [
                get_value(data_no, opt, inst, k, "mean_initial")
                for inst in instancias
            ]

            medias_reg = [
                get_value(data_reg, opt, inst, k, "mean_initial")
                for inst in instancias
            ]

            stds_no = [
                get_std_value(data_no, opt, inst, k)
                for inst in instancias
            ]

            stds_reg = [
                get_std_value(data_reg, opt, inst, k)
                for inst in instancias
            ]

            plt.bar(
                x + get_offset(base, GROUP_WIDTH),
                medias_no,
                width=BAR_WIDTH,
                color=COLORS_K[k],
                yerr=stds_no,
                capsize=5,
                error_kw={"elinewidth": 0.8, "ecolor": "black"},
                label=f"k={k} (No reg)" if tiene_datos(vals_no) else None
            )

            plt.bar(
                x + get_offset(base + 1, GROUP_WIDTH),
                medias_reg,
                width=BAR_WIDTH,
                color=COLORS_K[k],
                yerr=stds_reg,
                capsize=5,
                error_kw={"elinewidth": 0.8, "ecolor": "black"},
                hatch="//",
                alpha=0.8,
                edgecolor=EDGE_COLOR,
                linewidth=LINE_WIDTH,
                label=f"k={k} (Reg)" if tiene_datos(vals_reg) else None
            )

        plt.title(
            f"Simulation | {result_type} | Optimizer: {opt} | "
            f"k=2,3,4 | Mean initial distance"
        )
        plt.ylabel("Distance")
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

        limpiar_leyenda()

        if YLIMS["mean_initial"] is not None:
            plt.ylim(YLIMS["mean_initial"])

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(
            f"{fig_dir}/{result_type}_compare_media_std.png",
            bbox_inches="tight",
            dpi=200
        )
        plt.close()

        # =================================================
        # 3bis. BEST INITIAL
        # =================================================
        plt.figure(figsize=(12, 4))

        plt.bar(
            x + get_offset(0, GROUP_WIDTH),
            benchmark_vals,
            width=BAR_WIDTH,
            color="grey",
            label="Benchmark"
        )

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            vals_no = [
                get_value(data_no, opt, inst, k, "best_initial")
                for inst in instancias
            ]

            vals_reg = [
                get_value(data_reg, opt, inst, k, "best_initial")
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
            f"Simulation | {result_type} | Optimizer: {opt} | "
            f"k=2,3,4 | Best initial distance vs Benchmark"
        )
        plt.ylabel("Distance")
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

        limpiar_leyenda()

        if YLIMS["best_initial"] is not None:
            plt.ylim(YLIMS["best_initial"])

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(
            f"{fig_dir}/{result_type}_compare_best_initial.png",
            bbox_inches="tight",
            dpi=200
        )
        plt.close()

        # =================================================
        # 4. BEST REFINED VS BENCHMARK
        # =================================================
        plt.figure(figsize=(12, 4))

        plt.bar(
            x + get_offset(0, GROUP_WIDTH),
            benchmark_vals,
            width=BAR_WIDTH,
            color="grey",
            label="Benchmark"
        )

        for i, k in enumerate(DB_FILES_NO_REG):
            base = 1 + i * 2

            vals_no = [
                get_value(data_no, opt, inst, k, "refined_best")
                for inst in instancias
            ]

            vals_reg = [
                get_value(data_reg, opt, inst, k, "refined_best")
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
            f"Simulation | {result_type} | Optimizer: {opt} | "
            f"k=2,3,4 | Best refined vs benchmark"
        )
        plt.ylabel("Distance")
        plt.xticks(x, [i.replace("tsp", "") for i in instancias], rotation=45)

        limpiar_leyenda()

        if YLIMS["refined_best"] is not None:
            plt.ylim(YLIMS["refined_best"])

        plt.grid(True, linestyle="--", alpha=0.5)
        plt.savefig(
            f"{fig_dir}/{result_type}_compare_refined_best.png",
            bbox_inches="tight",
            dpi=200
        )
        plt.close()


for result_type, table_name in TABLES.items():
    generar_graficas(result_type, table_name)

print("✅ Comparación completada")