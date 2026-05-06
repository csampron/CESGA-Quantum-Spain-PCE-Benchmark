import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime

# ====================================================
# 1) LOAD RESULTS FROM JSON FILES (BPP VERSION α vs β)
# ====================================================
def load_bpp_results_from_path(path):
    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"❌ No existe el directorio: {experiment_path}")

    print(f"📂 Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():
        if folder.is_dir() and folder.name.lower().startswith("alpha_"):
            try:
                parts = folder.name.split("_")
                alpha = float(parts[1])
                beta  = float(parts[3])

                resultados_dir = folder / "Resultados"
                if not resultados_dir.exists():
                    print(f"⚠️ No existe la carpeta {resultados_dir}, se ignora.")
                    continue

                json_files = list(resultados_dir.glob("*.json")) + list(resultados_dir.glob("*.JSON"))
                if not json_files:
                    print(f"⚠️ No hay JSON en {resultados_dir}, se ignora.")
                    continue

                num_bins_used_list = []

                for jf in json_files:
                    with open(jf, "r") as f:
                        data = json.load(f)

                        feasibles = [
                            res for res in data.get("resultados", [])
                            if res.get("feasibility_initial", {}).get("feasible", False)
                        ]

                        if not feasibles:
                            continue

                        best = min(feasibles, key=lambda x: x.get("num_bins_used", np.inf))
                        num_bins_used_list.append(best["num_bins_used"])

                if not num_bins_used_list:
                    print(f"⚠️ No hay soluciones factibles iniciales en {resultados_dir}, se ignora.")
                    continue

                mean_val = np.mean(num_bins_used_list)
                std_val  = np.std(num_bins_used_list, ddof=0)
                min_val  = min(num_bins_used_list)

                records.append([alpha, beta, mean_val, std_val, min_val])

            except Exception as e:
                print(f"⚠️ Carpeta ignorada: {folder.name} ({e})")

    if not records:
        raise RuntimeError("⚠️ No se encontraron resultados válidos en este path.")

    df = pd.DataFrame(
        records,
        columns=["alpha", "beta", "mean", "std", "min_bins"]
    )
    return df


# ====================================================
# 2) HEATMAP FUNCTION (α vs β)
# ====================================================
def plot_heatmap(arr, x_vals, y_vals, title, xlabel, ylabel, cmap, out_path):
    fig, ax = plt.subplots(figsize=(14, 6))
    c = ax.imshow(arr, origin="lower", aspect="auto", cmap=cmap)

    ax.set_xticks(np.arange(len(x_vals)))
    ax.set_xticklabels([f"{x:.2f}" for x in x_vals])
    ax.set_yticks(np.arange(len(y_vals)))
    ax.set_yticklabels([f"{y:.3f}" for y in y_vals])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    fig.colorbar(c, ax=ax)
    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ====================================================
# 3) SAVE BEST SUMMARY
# ====================================================
def save_best_summary(path, min_bins_value, best_rows, alpha_vals, beta_vals):
    path = Path(path)

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "best_num_bins": int(min_bins_value),
        "num_best_combinations": int(len(best_rows)),
        "best_combinations": [
            {"alpha": float(row["alpha"]), "beta": float(row["beta"])}
            for _, row in best_rows.iterrows()
        ],
        "alpha_unique": int(len(alpha_vals)),
        "beta_unique": int(len(beta_vals)),
    }

    json_path = path / "best_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    txt_path = path / "best_summary.txt"
    with open(txt_path, "w") as f:
        f.write("🎯 Mejor solución encontrada\n")
        f.write(f"Bins mínimos: {min_bins_value}\n\n")
        f.write("Combinaciones alpha/beta:\n")
        for row in summary["best_combinations"]:
            f.write(f"  alpha={row['alpha']}, beta={row['beta']}\n")

        f.write("\n")
        f.write(f"alpha únicos: {len(alpha_vals)}\n")
        f.write(f"beta únicos: {len(beta_vals)}\n")
        f.write(f"timestamp: {summary['timestamp']}\n")

    print(f"💾 Resumen guardado en:\n  - {json_path}\n  - {txt_path}")


# ====================================================
# 4) MAIN PLOT FUNCTION α vs β
# ====================================================
def plot_bpp_results(base_path):
    base_path = Path(base_path)
    df = load_bpp_results_from_path(base_path)

    min_bins_value = df["min_bins"].min()
    best_rows = df[df["min_bins"] == min_bins_value].sort_values(by=["alpha", "beta"])

    print(f"\n🎯 Mejor solución tiene {min_bins_value} bins y se obtuvo con:")
    for _, row in best_rows.iterrows():
        print(f"    alpha={row['alpha']}, beta={row['beta']}")

    pivot_mean = df.pivot(index="beta", columns="alpha", values="mean")
    pivot_std  = df.pivot(index="beta", columns="alpha", values="std")

    arr_mean = pivot_mean.to_numpy()
    arr_std  = pivot_std.to_numpy()

    beta_vals  = pivot_mean.index.to_numpy()
    alpha_vals = pivot_mean.columns.to_numpy()

    print(f"\nalpha únicos: {len(alpha_vals)} | beta únicos: {len(beta_vals)}")

    save_best_summary(base_path, min_bins_value, best_rows, alpha_vals, beta_vals)

    plot_heatmap(
        arr_mean,
        x_vals=alpha_vals,
        y_vals=beta_vals,
        title="Mean number of bins",
        xlabel="Alpha",
        ylabel="Beta",
        cmap="viridis",
        out_path=base_path / "num_bins_mean.png",
    )

    plot_heatmap(
        arr_std,
        x_vals=alpha_vals,
        y_vals=beta_vals,
        title="Desviación estándar (num_bins_used)",
        xlabel="Alpha",
        ylabel="Beta",
        cmap="plasma",
        out_path=base_path / "num_bins_std.png",
    )

    print("\n✅ Heatmaps generados correctamente.")


# ====================================================
# EJEMPLO DE USO
# ====================================================
if __name__ == "__main__":
    base_path = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj_reg/PCE_Barrido_qubits+1/Experimentos/m_7/11_02_2026_10_33/k_2"
    plot_bpp_results(base_path)
