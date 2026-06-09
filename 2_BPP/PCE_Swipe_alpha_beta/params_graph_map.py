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
def compute_row_metrics(x_values):
    """
    BPP equivalent of TSP embedding_values metrics.

    x_values format:
        item_id -> [value for each bin]

    Metrics:
      - gap = top1 - top2 per item
      - row_max = max value per item
    """
    gaps = []
    row_maxs = []

    if not isinstance(x_values, dict):
        return {
            "mean_gap": np.nan,
            "min_gap": np.nan,
            "mean_row_max": np.nan,
            "min_row_max": np.nan,
        }

    for _, vals in x_values.items():
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
            "min_row_max": np.nan,
        }

    return {
        "mean_gap": np.mean(gaps),
        "min_gap": np.min(gaps),
        "mean_row_max": np.mean(row_maxs),
        "min_row_max": np.min(row_maxs),
    }


# ====================================================
# 2) LOAD RESULTS
# ====================================================
def parse_alpha_beta_from_folder(folder_name):
    """
    Expected folder format:
        alpha_15.0_beta_0.0
    """
    try:
        parts = folder_name.split("_")
        alpha = float(parts[parts.index("alpha") + 1])
        beta = float(parts[parts.index("beta") + 1])
        return alpha, beta
    except Exception:
        return np.nan, np.nan


def iter_json_files(experiment_path):
    """
    Supports both layouts:
      1) base/alpha_X_beta_Y/Resultados/*.json
      2) base/**/*.json
    """
    alpha_folders = [
        p for p in experiment_path.iterdir()
        if p.is_dir() and p.name.lower().startswith("alpha_")
    ]

    if alpha_folders:
        for folder in alpha_folders:
            alpha_folder, beta_folder = parse_alpha_beta_from_folder(folder.name)
            resultados_dir = folder / "Resultados"
            if not resultados_dir.exists():
                continue
            json_files = list(resultados_dir.glob("*.json")) + list(resultados_dir.glob("*.JSON"))
            for jf in json_files:
                yield jf, alpha_folder, beta_folder
    else:
        json_files = list(experiment_path.rglob("*.json")) + list(experiment_path.rglob("*.JSON"))
        for jf in json_files:
            alpha_folder, beta_folder = np.nan, np.nan
            for parent in jf.parents:
                if parent.name.lower().startswith("alpha_"):
                    alpha_folder, beta_folder = parse_alpha_beta_from_folder(parent.name)
                    break
            yield jf, alpha_folder, beta_folder


def normalize_status_initial(value):
    """
    Source of truth for BPP status.

    Allowed values expected in JSON:
        - infeasible
        - combinatorial
        - perfect

    Also accepts the common typo "prefect" just in case it appears
    in older files.
    """
    status = str(value or "infeasible").strip().lower()

    if status == "prefect":
        status = "perfect"

    if status not in {"infeasible", "combinatorial", "perfect"}:
        print(f"⚠️ status_initial desconocido: {value!r}. Se marca como infeasible.")
        status = "infeasible"

    return status

def load_bpp_results_from_path(path):
    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"❌ No existe el directorio: {experiment_path}")

    print(f"📂 Leyendo resultados BPP en: {experiment_path}")

    records = []

    for jf, alpha_folder, beta_folder in iter_json_files(experiment_path):
        try:
            with open(jf, "r") as f:
                data = json.load(f)

            results = data.get("resultados", [])
            if not results:
                results = [data]

            for res in results:
                alpha = res.get("alpha", alpha_folder)
                beta = res.get("beta", beta_folder)

                # status_initial is the only source of truth:
                # infeasible / combinatorial / perfect
                status = normalize_status_initial(res.get("status_initial"))

                # TSP equivalent:
                #   initial cycle distance  -> num_bins_used
                #   refined cycle distance  -> num_bins_used_post
                init_bins = res.get("num_bins_used")
                ref_bins = res.get("num_bins_used_post")

                # Defensive fallbacks only for plotting bins if one of the two
                # fields is absent in a valid solution. The status is NOT inferred
                # from these fields.
                if status == "perfect" and ref_bins is None:
                    ref_bins = init_bins
                if status == "combinatorial" and init_bins is None:
                    init_bins = ref_bins

                x_values = res.get("x_values", {})
                metrics = compute_row_metrics(x_values)

                records.append([
                    float(alpha) if alpha is not None and not pd.isna(alpha) else np.nan,
                    float(beta) if beta is not None and not pd.isna(beta) else np.nan,
                    init_bins,
                    ref_bins,
                    status,
                    metrics["mean_gap"],
                    metrics["min_gap"],
                    metrics["mean_row_max"],
                    metrics["min_row_max"],
                ])

        except Exception as e:
            print(f"⚠️ JSON ignorado: {jf} ({e})")

    if not records:
        raise RuntimeError("⚠️ No se encontraron resultados BPP válidos.")

    df = pd.DataFrame(
        records,
        columns=[
            "alpha",
            "beta",
            "init_bins",
            "ref_bins",
            "status",
            "mean_gap",
            "min_gap",
            "mean_row_max",
            "min_row_max",
        ],
    )

    df["perfect"] = df["status"] == "perfect"
    df["combinatorial"] = df["status"] == "combinatorial"
    df["valid"] = df["status"].isin(["perfect", "combinatorial"])

    print("\n📊 Status counts:")
    print(df["status"].value_counts(dropna=False))

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
    vmax=None,
):
    cmap = mpl.colormaps[cmap_name].copy()
    cmap.set_bad(color="white")

    arr = np.ma.masked_invalid(arr)

    fig, ax = plt.subplots(figsize=(12, 6))

    c = ax.imshow(
        arr,
        origin="lower",
        aspect="auto",
        cmap=cmap,
        vmin=vmin,
        vmax=vmax,
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
            combinatorial_rate=("combinatorial", "mean"),
            valid_rate=("valid", "mean"),
            init_bins_mean=("init_bins", "mean"),
            ref_bins_mean=("ref_bins", "mean"),
        )
        .reset_index()
        .sort_values(
            ["valid_rate", "mean_gap", "mean_row_max"],
            ascending=False,
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
            f"combinatorial_rate={row['combinatorial_rate']:.4f}, "
            f"valid_rate={row['valid_rate']:.4f}, "
            f"init_bins_mean={row['init_bins_mean']:.4f}, "
            f"ref_bins_mean={row['ref_bins_mean']:.4f}\n"
        )

    f.write("\n")


def save_status_summary_txt(df, out_path):
    out_path = Path(out_path)
    txt_file = out_path / "status_summary.txt"

    with open(txt_file, "w") as f:
        f.write("====================================================\n")
        f.write("BPP EMBEDDING SUMMARY — ALPHA / BETA\n")
        f.write(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("====================================================\n\n")

        f.write("GLOBAL STATS\n")
        f.write("--------------------------------------------\n")
        f.write(f"Total rows: {len(df)}\n")
        f.write(f"Perfect rate: {df['perfect'].mean():.4f}\n")
        f.write(f"Combinatorial rate: {df['combinatorial'].mean():.4f}\n")
        f.write(f"Feasible rate: {df['valid'].mean():.4f}\n\n")

        write_metric_block(f, "GLOBAL EMBEDDING METRICS", df)
        write_metric_block(f, "PERFECT REGIONS METRICS", df[df["perfect"]])
        write_metric_block(f, "COMBINATORIAL REGIONS METRICS", df[df["combinatorial"]])
        write_metric_block(f, "VALID REGIONS METRICS", df[df["valid"]])

    print(f"💾 status_summary.txt guardado en: {txt_file}")


# ====================================================
# 6) MAIN
# ====================================================
def plot_bpp_results(base_path):
    base_path = Path(base_path)

    df = load_bpp_results_from_path(base_path)

    alpha_vals = np.sort(df["alpha"].dropna().unique())
    beta_vals = np.sort(df["beta"].dropna().unique())

    if len(alpha_vals) == 0 or len(beta_vals) == 0:
        raise RuntimeError("⚠️ No se pudieron inferir valores de alpha/beta.")

    full_index = pd.MultiIndex.from_product(
        [beta_vals, alpha_vals],
        names=["beta", "alpha"],
    )

    # ====================================================
    # EMBEDDING METRIC PIVOTS
    # ====================================================
    pivot_mean_gap = build_complete_pivot(
        df.groupby(["beta", "alpha"])["mean_gap"].mean(),
        full_index,
    )

    pivot_min_gap = build_complete_pivot(
        df.groupby(["beta", "alpha"])["min_gap"].mean(),
        full_index,
    )

    pivot_mean_rowmax = build_complete_pivot(
        df.groupby(["beta", "alpha"])["mean_row_max"].mean(),
        full_index,
    )

    pivot_min_rowmax = build_complete_pivot(
        df.groupby(["beta", "alpha"])["min_row_max"].mean(),
        full_index,
    )

    # ====================================================
    # RATES
    # ====================================================
    pivot_perfect_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["perfect"].mean(),
        full_index,
    )

    pivot_combinatorial_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["combinatorial"].mean(),
        full_index,
    )

    pivot_feasible_rate = build_complete_pivot(
        df.groupby(["beta", "alpha"])["valid"].mean(),
        full_index,
    )

    # ====================================================
    # BINS PIVOTS
    # ====================================================
    df_perfect = df[df["status"] == "perfect"]
    df_combinatorial = df[df["status"] == "combinatorial"]

    pivot_perfect_mean = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["init_bins"].mean(),
        full_index,
    )

    pivot_perfect_std = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["init_bins"].std(),
        full_index,
    )

    pivot_combinatorial_mean = build_complete_pivot(
        df_combinatorial.groupby(["beta", "alpha"])["init_bins"].mean(),
        full_index,
    )

    pivot_combinatorial_std = build_complete_pivot(
        df_combinatorial.groupby(["beta", "alpha"])["init_bins"].std(),
        full_index,
    )

    pivot_perfect_refined_mean = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["ref_bins"].mean(),
        full_index,
    )

    pivot_perfect_refined_std = build_complete_pivot(
        df_perfect.groupby(["beta", "alpha"])["ref_bins"].std(),
        full_index,
    )

    pivot_combinatorial_refined_mean = build_complete_pivot(
        df_combinatorial.groupby(["beta", "alpha"])["ref_bins"].mean(),
        full_index,
    )

    pivot_combinatorial_refined_std = build_complete_pivot(
        df_combinatorial.groupby(["beta", "alpha"])["ref_bins"].std(),
        full_index,
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
        if len(values) == 0:
            return None, None
        return values.min(), values.max()

    bins_mean_vmin, bins_mean_vmax = shared_min_max(
        pivot_perfect_mean,
        pivot_combinatorial_mean,
        pivot_perfect_refined_mean,
        pivot_combinatorial_refined_mean,
    )

    bins_std_vmin, bins_std_vmax = shared_min_max(
        pivot_perfect_std,
        pivot_combinatorial_std,
        pivot_perfect_refined_std,
        pivot_combinatorial_refined_std,
    )

    gap_vmin, gap_vmax = shared_min_max(
        pivot_mean_gap,
        pivot_min_gap,
    )

    rowmax_vmin, rowmax_vmax = shared_min_max(
        pivot_mean_rowmax,
        pivot_min_rowmax,
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
        vmax=1,
    )

    plot_heatmap(
        pivot_combinatorial_rate.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Combinatorial Rate",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "combinatorial_rate.png",
        vmin=0,
        vmax=1,
    )

    plot_heatmap(
        pivot_feasible_rate.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Feasible Rate",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "feasible_rate.png",
        vmin=0,
        vmax=1,
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
        base_path / "mean_gap.png",
        vmin=gap_vmin,
        vmax=gap_vmax,
    )

    plot_heatmap(
        pivot_min_gap.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Min Gap",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "min_gap.png",
        vmin=gap_vmin,
        vmax=gap_vmax,
    )

    plot_heatmap(
        pivot_mean_rowmax.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Rowmax",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "mean_rowmax.png",
        vmin=rowmax_vmin,
        vmax=rowmax_vmax,
    )

    plot_heatmap(
        pivot_min_rowmax.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Min Rowmax",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "min_rowmax.png",
        vmin=rowmax_vmin,
        vmax=rowmax_vmax,
    )

    # ====================================================
    # HEATMAPS — NUMBER OF BINS USED
    # ====================================================
    plot_heatmap(
        pivot_perfect_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Initial Number of Bins Used",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "perfect_mean.png",
        vmin=bins_mean_vmin,
        vmax=bins_mean_vmax,
    )

    plot_heatmap(
        pivot_perfect_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Std Initial Number of Bins Used",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "perfect_std.png",
        vmin=bins_std_vmin,
        vmax=bins_std_vmax,
    )

    plot_heatmap(
        pivot_perfect_refined_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Mean Refined Number of Bins Used",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "perfect_refined_mean.png",
        vmin=bins_mean_vmin,
        vmax=bins_mean_vmax,
    )

    plot_heatmap(
        pivot_perfect_refined_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Std Refined Number of Bins Used",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "perfect_refined_std.png",
        vmin=bins_std_vmin,
        vmax=bins_std_vmax,
    )

    plot_heatmap(
        pivot_combinatorial_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Combinatorial Mean Initial Number of Bins Used",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "combinatorial_mean.png",
        vmin=bins_mean_vmin,
        vmax=bins_mean_vmax,
    )

    plot_heatmap(
        pivot_combinatorial_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Combinatorial Std Initial Number of Bins Used",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "combinatorial_std.png",
        vmin=bins_std_vmin,
        vmax=bins_std_vmax,
    )

    plot_heatmap(
        pivot_combinatorial_refined_mean.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Combinatorial Mean Refined Number of Bins Used",
        "Alpha",
        "Beta",
        "viridis",
        base_path / "combinatorial_refined_mean.png",
        vmin=bins_mean_vmin,
        vmax=bins_mean_vmax,
    )

    plot_heatmap(
        pivot_combinatorial_refined_std.to_numpy(float),
        alpha_vals,
        beta_vals,
        "Combinatorial Std Refined Number of Bins Used",
        "Alpha",
        "Beta",
        "plasma",
        base_path / "combinatorial_refined_std.png",
        vmin=bins_std_vmin,
        vmax=bins_std_vmax,
    )

    df.to_csv(base_path / "bpp_results_flat.csv", index=False)
    save_status_summary_txt(df, base_path)

    print(f"💾 bpp_results_flat.csv guardado en: {base_path / 'bpp_results_flat.csv'}")
    print("\n✅ Heatmaps BPP generados correctamente.")



# ====================================================
# RUN
# ====================================================
if __name__ == "__main__":
   
    base_path = (
        "Your_path"
        "z_BPP/PCE_v2/PCE_alpha_beta/"
        "Experimentos_k3/BPP_m_12/job_1/k_3"
    )

    plot_bpp_results(base_path)
