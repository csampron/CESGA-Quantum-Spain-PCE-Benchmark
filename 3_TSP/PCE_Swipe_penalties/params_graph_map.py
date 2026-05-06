import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime

# ====================================================
# 1) LOAD RESULTS FROM JSON FILES (TSP VERSION α vs A, usando initial_distance)
# ====================================================
def load_tsp_results_from_path(path):
    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"❌ No existe el directorio: {experiment_path}")

    print(f"📂 Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():
        if folder.is_dir() and folder.name.lower().startswith("alpha_"):
            try:
                # carpeta: alpha_{alpha}_A_{A}
                parts = folder.name.split("_")
                a = float(parts[1])
                A = float(parts[3])

                resultados_dir = folder / "Resultados"
                if not resultados_dir.exists():
                    print(f"⚠️ No existe la carpeta {resultados_dir}, se ignora.")
                    continue

                json_files = list(resultados_dir.glob("*.json")) + list(resultados_dir.glob("*.JSON"))
                if not json_files:
                    print(f"⚠️ No hay JSON en {resultados_dir}, se ignora.")
                    continue

                tour_length_list = []

                for jf in json_files:
                    with open(jf, "r") as f:
                        data = json.load(f)

                        # Para TSP, usamos 'initial_distance' como métrica
                        results = data.get("resultados", [])
                        if not results:
                            # Si el JSON es directamente un dict individual (ejecutar_experimentos)
                            results = [data]

                        distances = [
                            res.get("initial_distance", np.inf)
                            for res in results
                            if res.get("initial_distance") is not None
                        ]

                        if not distances:
                            continue

                        tour_length_list.extend(distances)

                if not tour_length_list:
                    print(f"⚠️ No hay tours válidos en {resultados_dir}, se ignora.")
                    continue

                mean_val = pd.Series(tour_length_list).mean()
                std_val  = pd.Series(tour_length_list).std(ddof=0)
                min_val  = min(tour_length_list)

                records.append([a, A, mean_val, std_val, min_val])

            except Exception as e:
                print(f"⚠️ Carpeta ignorada: {folder.name} ({e})")

    if not records:
        raise RuntimeError("⚠️ No se encontraron resultados válidos en este path.")

    df = pd.DataFrame(records, columns=["alpha", "A", "mean", "std", "min_distance"])
    return df

# ====================================================
# 2) HEATMAP FUNCTION (ROBUST FOR α vs A)
# ====================================================
def plot_heatmap(arr, x_vals, y_vals, title, xlabel, ylabel, cmap, out_path):
    fig, ax = plt.subplots(figsize=(8,6))
    c = ax.imshow(arr, origin="lower", aspect="auto", cmap=cmap)
    ax.set_xticks(np.arange(len(x_vals)))
    ax.set_xticklabels([f"{x:.2f}" for x in x_vals])
    ax.set_yticks(np.arange(len(y_vals)))
    ax.set_yticklabels([f"{y:.1f}" for y in y_vals])
    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    fig.colorbar(c, ax=ax)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)

# ====================================================
# 3) SAVE BEST SUMMARY (JSON + TXT)
# ====================================================
def save_best_summary(path, min_val, best_rows, alpha_vals, A_vals):
    path = Path(path)

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "best_initial_distance": float(min_val),
        "num_best_combinations": int(len(best_rows)),
        "best_combinations": [
            {"alpha": float(row["alpha"]), "A": float(row["A"])}
            for _, row in best_rows.iterrows()
        ],
        "alpha_unique": int(len(alpha_vals)),
        "A_unique": int(len(A_vals)),
    }

    # ---- JSON ----
    json_path = path / "best_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    # ---- TXT ----
    txt_path = path / "best_summary.txt"
    with open(txt_path, "w") as f:
        f.write("🎯 Mejor tour inicial\n")
        f.write(f"Distancia mínima inicial: {min_val}\n\n")
        f.write("Combinaciones alpha/A:\n")
        for row in summary["best_combinations"]:
            f.write(f"  alpha={row['alpha']}, A={row['A']}\n")
        f.write("\n")
        f.write(f"alpha únicos: {len(alpha_vals)}\n")
        f.write(f"A únicos: {len(A_vals)}\n")
        f.write(f"timestamp: {summary['timestamp']}\n")

    print(f"💾 Resumen guardado en:\n  - {json_path}\n  - {txt_path}")

# ====================================================
# 4) MAIN PLOT FUNCTION α vs A (initial_distance)
# ====================================================
def plot_tsp_results(base_path):
    base_path = Path(base_path)
    df = load_tsp_results_from_path(base_path)

    # Mejor tour inicial global
    min_val = df["min_distance"].min()
    best_rows = df[df["min_distance"] == min_val].sort_values(by=["alpha", "A"])

    print(f"\n🎯 Mejor tour inicial tiene distancia {min_val} y se obtuvo con:")
    for _, row in best_rows.iterrows():
        print(f"    alpha={row['alpha']}, A={row['A']}")

    # Pivot tables (filas=A, columnas=alpha)
    pivot_mean = df.pivot(index="A", columns="alpha", values="mean")
    pivot_std  = df.pivot(index="A", columns="alpha", values="std")

    arr_mean = pivot_mean.to_numpy()
    arr_std  = pivot_std.to_numpy()

    A_vals = pivot_mean.index.to_numpy()
    alpha_vals = pivot_mean.columns.to_numpy()

    print(f"\nalpha únicos: {len(alpha_vals)} | A únicos: {len(A_vals)}")

    # Guardar resumen del mejor resultado
    save_best_summary(base_path, min_val, best_rows, alpha_vals, A_vals)

    # Heatmaps
    plot_heatmap(
        arr_mean,
        x_vals=alpha_vals,
        y_vals=A_vals,
        title="Distancia promedio inicial del tour",
        xlabel="Alpha",
        ylabel="A",
        cmap="viridis",
        out_path=base_path / "tour_initial_distance_mean.png",
    )

    plot_heatmap(
        arr_std,
        x_vals=alpha_vals,
        y_vals=A_vals,
        title="Desviación estándar de la distancia inicial del tour",
        xlabel="Alpha",
        ylabel="A",
        cmap="plasma",
        out_path=base_path / "tour_initial_distance_std.png",
    )

    print("\n✅ Heatmaps generados correctamente.")

# ====================================================
# EJEMPLO DE USO
# ====================================================
if __name__ == "__main__":
    base_path = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_TSP/PCE_TSP_barrido_alpha_B/Experimentos/TSP_m_15/13_01_2026_22_51/k_2"
    plot_tsp_results(base_path)
