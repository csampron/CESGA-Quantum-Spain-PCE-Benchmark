import os
import json
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict


def plot_error_vs_shots(size, k, error_type="mse", base_folder="Results"):
    """
    Genera gráfica error vs shots para un tamaño m dado.
    error_type: "mse", "mae" o "max_error"
    """

    folder = os.path.join(base_folder, f"k_{k}", f"m_{size}")

    if not os.path.isdir(folder):
        print(f"[WARNING] No existe la carpeta: {folder}")
        return

    data_by_shots = defaultdict(list)

    # Leer todos los JSON del directorio
    for file in os.listdir(folder):
        if file.endswith(".json"):
            with open(os.path.join(folder, file), "r") as f:
                data = json.load(f)

                for key, results in data.items():
                    if not key.startswith("shots"):
                        continue

                    shots = int(key[5:])

                    for entry in results:
                        if error_type in entry:
                            data_by_shots[shots].append(entry[error_type])

    if not data_by_shots:
        print(f"[WARNING] No hay datos válidos en m_{size}")
        return

    shots_sorted = sorted(data_by_shots.keys())
    error_mean = []
    error_std = []

    for s in shots_sorted:
        values = np.array(data_by_shots[s])
        error_mean.append(np.mean(values))
        error_std.append(np.std(values))

        # ---------- PLOT ----------
    plt.figure(figsize=(6,4))
    plt.errorbar(
        shots_sorted,
        error_mean,
        yerr=error_std,
        marker='o',
        capsize=5,
        elinewidth=1.5,
        label=f"{error_type}"
    )

    # ---------- Curva teórica 1/sqrt(N) ----------
    """ shots_array = np.linspace(shots_sorted[0], 1e7, 500)  # lineal
    C = 10
    theory_curve = C / np.sqrt(shots_array)

    plt.plot(
        shots_array,
        theory_curve,
        '--',
        linewidth=2,
        color='black',
        label=r"$\propto 1/\sqrt{N}$"
    ) """

    plt.xlabel("Number of shots")
    plt.ylabel(error_type.upper())
    plt.title(f"{error_type.upper()} vs Shots (m={size}, k={k})")
    plt.xscale("log")
    plt.yscale("log")
    plt.grid(True, which="both", linestyle="--", alpha=0.6)
    plt.legend()
    plt.tight_layout()
    
    filename = os.path.join(folder, f"{error_type}_vs_shots_m_{size}.png")
    plt.savefig(filename, dpi=300)
    plt.close()  # ahora sí cerramos la figura
    print(f"[OK] Guardado {filename}")




def generar_graficas_varios_m(lista_m, k, base_folder="Results"):
    """
    Genera gráficas para varios tamaños m
    """

    for m in lista_m:
        print(f"\nProcesando m = {m}")
        plot_error_vs_shots(m, k, "mse", base_folder)
        plot_error_vs_shots(m, k, "mae", base_folder)
        plot_error_vs_shots(m, k, "max_error", base_folder)


def plot_errors_vs_m_separado(lista_m, k, base_folder="Results"):
    """
    Genera tres gráficas separadas para cada tipo de error:
    - eje X: tamaño m
    - eje Y: error medio
    - curvas: cada número de shots
    """
    errores = ["mse", "mae", "max_error"]

    # Guardar datos por error y shots
    data_global = {etype: defaultdict(lambda: {"m": [], "mean": [], "std": []}) for etype in errores}

    for size in lista_m:
        folder = os.path.join(base_folder, f"k_{k}", f"m_{size}")
        if not os.path.isdir(folder):
            print(f"[WARNING] No existe la carpeta: {folder}")
            continue

        data_by_shots = {etype: defaultdict(list) for etype in errores}

        # Leer JSON
        for file in os.listdir(folder):
            if file.endswith(".json"):
                with open(os.path.join(folder, file), "r") as f:
                    data = json.load(f)
                    for key, results in data.items():
                        if not key.startswith("shots"):
                            continue
                        shots = int(key[5:])
                        for entry in results:
                            for etype in errores:
                                if etype in entry:
                                    data_by_shots[etype][shots].append(entry[etype])

        # Calcular media y std por shots
        for etype in errores:
            for shots, values in data_by_shots[etype].items():
                values = np.array(values)
                data_global[etype][shots]["m"].append(size)
                data_global[etype][shots]["mean"].append(np.mean(values))
                data_global[etype][shots]["std"].append(np.std(values))

    # ---------- Generar un gráfico por cada tipo de error ----------
    output_folder = os.path.join(base_folder, f"k_{k}")
    os.makedirs(output_folder, exist_ok=True)

    for etype in errores:
        if etype != "max_error":
            plt.figure(figsize=(8,6))
            for shots, stats in sorted(data_global[etype].items()):
                plt.errorbar(
                    stats["m"],
                    stats["mean"],
                    yerr=stats["std"],
                    marker='o',
                    capsize=5,
                    elinewidth=1.5,
                    label=f"{shots} shots"
                )
            plt.xlabel("Size m")
            plt.ylabel(etype.upper())
            plt.ylim(0,0.2)
            plt.title(f"{etype.upper()} vs Size m (k={k})")
            #plt.xscale("log")
            #plt.yscale("log")
            plt.grid(True, which="both", linestyle="--", alpha=0.6)
            plt.legend()
            plt.tight_layout()

            filename = os.path.join(output_folder, f"not_noisy_{etype}_vs_m_k_{k}.png")
            plt.savefig(filename, dpi=300)
            plt.close()
            print(f"[OK] Guardado {filename}")
        else:
            plt.figure(figsize=(8,6))
            for shots, stats in sorted(data_global[etype].items()):
                plt.errorbar(
                    stats["m"],
                    stats["mean"],
                    yerr=stats["std"],
                    marker='o',
                    capsize=5,
                    elinewidth=1.5,
                    label=f"{shots} shots"
                )
            plt.xlabel("Size m")
            plt.ylabel(etype.upper())
            plt.ylim(0, 0.8)
            plt.title(f"{etype.upper()} vs Size m (k={k})")
            #plt.xscale("log")
            #plt.yscale("log")
            plt.grid(True, which="both", linestyle="--", alpha=0.6)
            plt.legend()
            plt.tight_layout()

            filename = os.path.join(output_folder, f"not_noisy_{etype}_vs_m_k_{k}.png")
            plt.savefig(filename, dpi=300)
            plt.close()
            print(f"[OK] Guardado {filename}")




# ------------------ EJECUCIÓN ------------------

lista_m = [10, 20, 40, 50, 60, 100, 150, 200, 250, 300]
k = 4
direc = "Your_route/PCE_SHOTS/Not_Noisy/MaxCut/PCE_Shots_Estimation/Results"

#generar_graficas_varios_m(lista_m, k, direc)
plot_errors_vs_m_separado(lista_m, k, direc)
