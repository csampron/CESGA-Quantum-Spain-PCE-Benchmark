import matplotlib.pyplot as plt
import matplotlib as mpl
from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime


# ====================================================
# 1) AUX METRICS
# ====================================================
def compute_row_metrics(embedding_values):

    gaps = []
    row_maxs = []

    for _, vals in embedding_values.items():

        arr = np.array(vals, dtype=float)

        if len(arr) < 2:
            continue

        sorted_vals = np.sort(arr)[::-1]

        top1 = sorted_vals[0]
        top2 = sorted_vals[1]

        gaps.append(top1 - top2)
        row_maxs.append(top1)

    if len(gaps) == 0:
        return {
            "mean_gap": np.nan,
            "min_gap": np.nan,
            "mean_row_max": np.nan,
            "min_row_max": np.nan
        }

    return {
        "mean_gap": np.mean(gaps),
        "min_gap": np.min(gaps),
        "mean_row_max": np.mean(row_maxs),
        "min_row_max": np.min(row_maxs)
    }


# ====================================================
# 2) LOAD RESULTS
# ====================================================
def load_tsp_results_from_path(path):

    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"❌ No existe el directorio: {experiment_path}")

    print(f"📂 Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():

        # Expected format:
        # alpha_2_beta_0.0
        if folder.is_dir() and folder.name.lower().startswith("alpha_"):

            try:
                parts = folder.name.split("_")

                alpha = float(parts[1])
                beta = float(parts[3])

                resultados_dir = folder / "Resultados"

                if not resultados_dir.exists():
                    continue

                json_files = (
                    list(resultados_dir.glob("*.json")) +
                    list(resultados_dir.glob("*.JSON"))
                )

                if not json_files:
                    continue

                for jf in json_files:

                    with open(jf, "r") as f:
                        data = json.load(f)

                    results = data.get("resultados", [])

                    if not results:
                        results = [data]

                    for res in results:

                        status = res.get("status", "infeasible")

                        init_dist = res.get("initial_distance")
                        ref_dist = res.get("refined_distance")

                        embedding_values = res.get("embedding_values", {})
                        metrics = compute_row_metrics(embedding_values)

                        records.append([
                            alpha,
                            beta,
                            init_dist,
                            ref_dist,
                            status,
                            metrics["mean_gap"],
                            metrics["min_gap"],
                            metrics["mean_row_max"],
                            metrics["min_row_max"]
                        ])

            except Exception as e:
                print(f"⚠️ Carpeta ignorada: {folder.name} ({e})")

    if not records:
        raise RuntimeError("⚠️ No se encontraron resultados válidos.")

    df = pd.DataFrame(
        records,
        columns=[
            "alpha",
            "beta",
            "init_dist",
            "ref_dist",
            "status",
            "mean_gap",
            "min_gap",
            "mean_row_max",
            "min_row_max"
        ]
    )

    df["perfect"] = df["status"] == "perfect"
    df["greedy"] = df["status"] == "greedy"
    df["valid"] = df["status"].isin(["perfect", "greedy"])

    return df


# ====================================================
# 3) HEATMAP
# ====================================================
def plot_heatmap(
    arr,
    x_vals,
    y_vals,
    title,
    xlabel,
    ylabel,
    cmap_name,
    out_path,
    vmin=None,
    vmax=None
):
    cmap = mpl.cm.get_cmap(cmap_name).copy()
    cmap.set_bad(color="white")

    arr = np.ma.masked_invalid(arr)

    fig, ax = plt.subplots(figsize=(12, 6))

    c = ax.imshow(
        arr,
        origin="lower",
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax
    )

    ax.set_xticks(np.arange(len(x_vals)))
    ax.set_xticklabels([f"{x:.2f}" for x in x_vals])

    ax.set_yticks(np.arange(len(y_vals)))
    ax.set_yticklabels([f"{y:.2f}" for y in y_vals])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    fig.colorbar(c, ax=ax)

    fig.savefig(out_path, dpi=300, bbox_inches="tight")
    plt.close(fig)


# ====================================================
# 4) BUILD COMPLETE PIVOT
# ====================================================
def build_complete_pivot(series, full_index):
    return series.reindex(full_index).unstack()


# ====================================================
# 5) TXT SUMMARY
# ====================================================
def write_metric_block(f, title, subdf):

    f.write(f"{title}\n")
    f.write("--------------------------------------------\n")

    if len(subdf) == 0:
        f.write("No rows\n\n")
        return

    f.write(f"Rows: {len(subdf)}\n")
    f.write(f"Mean gap: {subdf['mean_gap'].mean():.4f}\n")
    f.write(f"Min gap mean: {subdf['min_gap'].mean():.4f}\n")
    f.write(f"Mean row max: {subdf['mean_row_max'].mean():.4f}\n")
    f.write(f"Min row max mean: {subdf['min_row_max'].mean():.4f}\n")

    f.write("\nBest regions by mean_gap:\n")

    best_regions = (
        subdf.groupby(["alpha", "beta"])
        .agg(
            runs=("status", "count"),
            mean_gap=("mean_gap", "mean"),
            min_gap=("min_gap", "mean"),
            mean_row_max=("mean_row_max", "mean"),
            min_row_max=("min_row_max", "mean"),
            perfect_rate=("perfect", "mean"),
            greedy_rate=("greedy", "mean"),
            valid_rate=("valid", "mean"),
            init_dist_mean=("init_dist", "mean"),
            ref_dist_mean=("ref_dist", "mean"),
        )
        .reset_index()
        .sort_values(
            ["valid_rate", "mean_gap", "mean_row_max"],
            ascending=False
        )
    )

    for _, row in best_regions.head(10).iterrows():
        f.write(
            f"alpha={row['alpha']}, beta={row['beta']} | "
            f"runs={int(row['runs'])}, "
            f"mean_gap={row['mean_gap']:.4f}, "
            f"min_gap={row['min_gap']:.4f}, "
            f"mean_row_max={row['mean_row_max']:.4f}, "
            f"min_row_max={row['min_row_max']:.4f}, "
            f"perfect_rate={row['perfect_rate']:.4f}, "
            f"greedy_rate={row['greedy_rate']:.4f}, "
            f"valid_rate={row['valid_rate']:.4f}, "
            f"init_dist_mean={row['init_dist_mean']:.4f}, "
            f"ref_dist_mean={row['ref_dist_mean']:.4f}\n"
        )

    f.write("\n")


def save_status_summary_txt(df, out_path):

    out_path = Path(out_path)
    txt_file = out_path / "status_summary.txt"

    with open(txt_file, "w") as f:

        f.write("====================================================\n")
        f.write("TSP EMBEDDING SUMMARY — ALPHA / BETA\n")
        f.write(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("====================================================\n\n")

        f.write("GLOBAL STATS\n")
        f.write("--------------------------------------------\n")
        f.write(f"Total rows: {len(df)}\n")
        f.write(f"Perfect rate: {df['perfect'].mean():.4f}\n")
        f.write(f"Greedy rate: {df['greedy'].mean():.4f}\n")
        f.write(f"Feasible rate: {df['valid'].mean():.4f}\n\n")

        write_metric_block(f, "GLOBAL EMBEDDING METRICS", df)
        write_metric_block(f, "PERFECT REGIONS METRICS", df[df["perfect"]])
        write_metric_block(f, "GREEDY REGIONS METRICS", df[df["greedy"]])
        write_metric_block(f, "VALID REGIONS METRICS", df[df["valid"]])

    print(f"💾 status_summary.txt guardado en: {txt_file}")


# ====================================================
# 6) MAIN
# ====================================================
def plot_tsp_results(base_path):

    base_path = Path(base_path)

    df = load_tsp_results_from_path(base_path)

    alpha_vals = np.sort(df["alpha"].unique())
    beta_vals = np.sort(df["beta"].unique())

    full_index = pd.MultiIndex.from_product(
        [beta_vals, alpha_vals],
        names=["beta", "alpha"]
    )

    # ====================================================
    # EMBEDDING METRIC PIVOTS
    # ====================================================
    pivot_mean_gap = build_complete_pivot(
        df.groupby(["beta", "alpha"])["mean_gap"].mean(),
        full_index
    )

    pivot_min_gap = build_complete_pivot(
        df.groupby(["beta", "alpha"])["min_gap"].mean(),
        full_index
    )

    pivot_mean_rowmax = build_complete_pivot(
        df.groupby(["beta", "alpha"])["mean_row_max"].mean(),
        full_index
    )

    pivot_min_rowmax = build_complete_pivot(
        df.groupby(["beta", "alpha"])["min_row_max"].mean(),
        full_index
    )

    # ====================================================
    # RATES
    # ====================================================
    pivot_perfect_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["perfect"].mean(),
        full_index
    )

    pivot_greedy_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["greedy"].mean(),
        full_index
    )

    pivot_feasible_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["valid"].mean(),
        full_index
    )

    # ====================================================
    # DISTANCE PIVOTS
    # ====================================================
    df_perfect = df[df["status"] == "perfect"]
    df_greedy = df[df["status"] == "greedy"]

    pivot_perfect_mean = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["init_dist"].mean(),
        full_index
    )

    pivot_perfect_std = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["init_dist"].std(),
        full_index
    )
    

    pivot_greedy_mean = build_complete_pivot(
        df_greedy.groupby(["beta", "alpha"])["init_dist"].mean(),
        full_index
    )

    pivot_greedy_std = build_complete_pivot(
        df_greedy.groupby(["beta", "alpha"])["init_dist"].std(),
        full_index
    )   

    # Optional refined-distance plots
    pivot_perfect_refined_mean = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["ref_dist"].mean(),
        full_index
    )

    pivot_perfect_refined_std = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["ref_dist"].std(),
        full_index
    )

    # Optional refined-distance plots
    pivot_greedy_refined_mean = build_complete_pivot(
        df_greedy.groupby(["beta", "alpha"])["ref_dist"].mean(),
        full_index
    )

    pivot_greedy_refined_std = build_complete_pivot(
        df_greedy.groupby(["beta", "alpha"])["ref_dist"].std(),
        full_index
    )
    

    # ====================================================
    # COMMON COLOR SCALES
    # ====================================================

    def shared_min_max(*pivots):
        values = np.concatenate([
            p.to_numpy(float).ravel()
            for p in pivots
        ])
        values = values[~np.isnan(values)]
        return values.min(), values.max()


    # Distances: lower bound from refined mean/std,
    # upper bound from initial distance
    dist_mean_vmin = np.nanmin([
        pivot_perfect_refined_mean.to_numpy(float),
        pivot_greedy_refined_mean.to_numpy(float)
    ])

    dist_std_vmin = np.nanmin([
        pivot_perfect_refined_std.to_numpy(float),
        pivot_greedy_refined_std.to_numpy(float)
    ])

    dist_vmax = df["init_dist"].max()


    # Same scale: mean_gap vs min_gap
    gap_vmin, gap_vmax = shared_min_max(
        pivot_mean_gap,
        pivot_min_gap
    )


    # Same scale: mean_row_max vs min_row_max
    rowmax_vmin, rowmax_vmax = shared_min_max(
        pivot_mean_rowmax,
        pivot_min_rowmax
    )

    # ====================================================
    # HEATMAPS — RATE
    # ====================================================

    plot_heatmap(
        pivot_perfect_rate.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Perfect Rate",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "perfect_rate.png",
        vmin=0,
        vmax=1
    )

    plot_heatmap(
        pivot_greedy_rate.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Greedy Rate",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "greedy_rate.png",
        vmin=0,
        vmax=1
    )


    # ====================================================
    # HEATMAPS — METRICS
    # ====================================================

    plot_heatmap(
        pivot_mean_gap.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Gap",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "mean_gap.png"
    )

    plot_heatmap(
        pivot_min_gap.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Min Gap",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "min_gap.png"
    )

    plot_heatmap(
        pivot_mean_rowmax.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Rowmax",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "mean_rowmax.png"
    )

    plot_heatmap(
        pivot_min_rowmax.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Min Rowmax",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "min_rowmax.png"
    )

    # ====================================================
    # HEATMAPS — DISTANCES
    # ====================================================
    plot_heatmap(
        pivot_perfect_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Initial Cycle Distance",  #"Perfect Mean Initial Distance",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "perfect_mean.png",
        vmin=dist_mean_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_perfect_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Std Initial Cycle Distance", #"Perfect Std Initial Distance",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "perfect_std.png",
        vmin=dist_std_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_perfect_refined_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Refined Cycle Distance", #"Perfect Mean Refined Distance",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "perfect_refined_mean.png",
        vmin=dist_mean_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_perfect_refined_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Std Refined Cycle Distance", #"Perfect Std Refined Distance",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "perfect_refined_std.png",
        vmin=dist_std_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_greedy_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Greedy Mean Initial Distance",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "greedy_mean.png",
        vmin=dist_mean_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_greedy_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Greedy Std Initial Distance",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "greedy_std.png",
        vmin=dist_std_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_greedy_refined_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Greedy Mean Refined Distance",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "greedy_refined_mean.png",
        vmin=dist_mean_vmin,
        vmax=dist_vmax
    )

    plot_heatmap(
        pivot_greedy_refined_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Greedy Std Refined Distance",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "greedy_refined_std.png",
        vmin=dist_std_vmin,
        vmax=dist_vmax
    )

    save_status_summary_txt(df, base_path)

    print("\n✅ Heatmaps generados correctamente.")


# ====================================================
# RUN
# ====================================================
if __name__ == "__main__":

    base_path = (
        "Your_route/PCE_Swipe_alpha_beta/"
        "Experimentos_k3/TSP_m_15/job_1/k_3"
    )

    plot_tsp_results(base_path)