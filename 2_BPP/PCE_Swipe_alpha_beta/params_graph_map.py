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
        raise FileNotFoundError(f":x: No existe el directorio: {experiment_path}")

    print(f":open_file_folder: Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():
        if folder.is_dir() and folder.name.lower().startswith("alpha_"):
            try:
                parts = folder.name.split("_")
                alpha = float(parts[1])
                beta  = float(parts[3])

                resultados_dir = folder / "Resultados"
                if not resultados_dir.exists():
                    print(f":warning: No existe la carpeta {resultados_dir}, se ignora.")
                    continue

                json_files = list(resultados_dir.glob("*.json")) + list(resultados_dir.glob("*.JSON"))
                if not json_files:
                    print(f":warning: No hay JSON en {resultados_dir}, se ignora.")
                    continue

                num_bins_used_list = []
                num_bins_used_post_list = []

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

                        if "num_bins_used_post" in best:
                            num_bins_used_post_list.append(best["num_bins_used_post"])

                if not num_bins_used_list:
                    print(f":warning: No hay soluciones factibles iniciales en {resultados_dir}, se ignora.")
                    continue

                records.append([
                    alpha,
                    beta,
                    np.mean(num_bins_used_list),
                    np.std(num_bins_used_list),
                    min(num_bins_used_list),
                    np.mean(num_bins_used_post_list) if num_bins_used_post_list else np.nan,
                    np.std(num_bins_used_post_list) if num_bins_used_post_list else np.nan,
                    min(num_bins_used_post_list) if num_bins_used_post_list else np.nan,
                ])

            except Exception as e:
                print(f":warning: Carpeta ignorada: {folder.name} ({e})")

    if not records:
        raise RuntimeError(":warning: No se encontraron resultados válidos en este path.")

    df = pd.DataFrame(
        records,
        columns=[
            "alpha", "beta",
            "mean_pre", "std_pre", "min_pre",
            "mean_post", "std_post", "min_post"
        ]
    )
    return df


# ====================================================
# 2) HEATMAP FUNCTION
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
def save_best_summary(path, df, min_pre, min_post, best_pre, best_post):
    path = Path(path)

    summary = {
        "timestamp": datetime.now().isoformat(timespec="seconds"),
        "best_pre_bins": int(min_pre),
        "best_post_bins": int(min_post),
        "num_best_pre": int(len(best_pre)),
        "num_best_post": int(len(best_post)),
    }

    json_path = path / "best_summary.json"
    with open(json_path, "w") as f:
        json.dump(summary, f, indent=2)

    txt_path = path / "best_summary.txt"
    with open(txt_path, "w") as f:
        f.write(":dart: BEST RESULTS\n\n")

        f.write("PRE:\n")
        f.write(f"Min bins: {min_pre}\n")
        for _, r in best_pre.iterrows():
            f.write(f"  alpha={r.alpha}, beta={r.beta}\n")

        f.write("\nPOST:\n")
        f.write(f"Min bins: {min_post}\n")
        for _, r in best_post.iterrows():
            f.write(f"  alpha={r.alpha}, beta={r.beta}\n")

    print(f":floppy_disk: Resumen guardado en:\n  - {json_path}\n  - {txt_path}")


# ====================================================
# 4) MAIN
# ====================================================
def plot_bpp_results(base_path):
    base_path = Path(base_path)
    df = load_bpp_results_from_path(base_path)

    # -----------------------
    # PRE
    # -----------------------
    min_pre = df["min_pre"].min()
    best_pre = df[df["min_pre"] == min_pre]

    # -----------------------
    # POST
    # -----------------------
    min_post = df["min_post"].min()
    best_post = df[df["min_post"] == min_post]

    print(f"\n:dart: BEST PRE: {min_pre}")
    print(f":dart: BEST POST: {min_post}")

    pivot_pre_mean = df.pivot(index="beta", columns="alpha", values="mean_pre")
    pivot_pre_std  = df.pivot(index="beta", columns="alpha", values="std_pre")

    pivot_post_mean = df.pivot(index="beta", columns="alpha", values="mean_post")
    pivot_post_std  = df.pivot(index="beta", columns="alpha", values="std_post")

    alpha_vals = pivot_pre_mean.columns.to_numpy()
    beta_vals = pivot_pre_mean.index.to_numpy()

    save_best_summary(base_path, df, min_pre, min_post, best_pre, best_post)

    # -----------------------
    # HEATMAPS PRE
    # -----------------------
    plot_heatmap(
        pivot_pre_mean.to_numpy(),
        alpha_vals, beta_vals,
        "Mean number of bins (pre)",
        "Alpha", "Beta",
        "viridis",
        base_path / "num_bins_pre_mean.png",
    )

    plot_heatmap(
        pivot_pre_std.to_numpy(),
        alpha_vals, beta_vals,
        "Std number of bins (pre)",
        "Alpha", "Beta",
        "plasma",
        base_path / "num_bins_pre_std.png",
    )

    # -----------------------
    # HEATMAPS POST
    # -----------------------
    plot_heatmap(
        pivot_post_mean.to_numpy(),
        alpha_vals, beta_vals,
        "Mean number of bins (post)",
        "Alpha", "Beta",
        "viridis",
        base_path / "num_bins_post_mean.png",
    )

    plot_heatmap(
        pivot_post_std.to_numpy(),
        alpha_vals, beta_vals,
        "Std number of bins (post)",
        "Alpha", "Beta",
        "plasma",
        base_path / "num_bins_post_std.png",
    )

    print("\n:white_check_mark: Heatmaps generados correctamente.")


# ====================================================
# RUN
# ====================================================
if __name__ == "__main__":
    base_path = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj_reg/PCE_Barrido_qubits+1/Experimentos/m_6/11_02_2026_10_21/k_2"
    plot_bpp_results(base_path)