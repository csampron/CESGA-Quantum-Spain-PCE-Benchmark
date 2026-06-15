from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime


# ====================================================
# THRESHOLDS
# ====================================================
DEAD_ROW_THRESHOLD = 0.40
WEAK_ROW_THRESHOLD = 0.50
AMBIGUOUS_GAP_THRESHOLD = 0.05


# ====================================================
# AUX METRICS
# ====================================================
def compute_row_metrics(embedding_values):

    gaps = []
    row_maxs = []

    dead_rows = 0
    weak_rows = 0
    ambiguous_rows = 0

    for _, vals in embedding_values.items():

        arr = np.array(vals, dtype=float)

        if len(arr) < 2:
            continue

        sorted_vals = np.sort(arr)[::-1]

        top1 = sorted_vals[0]
        top2 = sorted_vals[1]
        gap = top1 - top2

        gaps.append(gap)
        row_maxs.append(top1)

        if top1 < DEAD_ROW_THRESHOLD:
            dead_rows += 1

        if top1 < WEAK_ROW_THRESHOLD:
            weak_rows += 1

        if gap < AMBIGUOUS_GAP_THRESHOLD:
            ambiguous_rows += 1

    if len(gaps) == 0:
        return {
            "mean_gap": np.nan,
            "min_gap": np.nan,
            "mean_row_max": np.nan,
            "min_row_max": np.nan,
            "dead_rows": np.nan,
            "weak_rows": np.nan,
            "ambiguous_rows": np.nan,
        }

    return {
        "mean_gap": np.mean(gaps),
        "min_gap": np.min(gaps),
        "mean_row_max": np.mean(row_maxs),
        "min_row_max": np.min(row_maxs),
        "dead_rows": dead_rows,
        "weak_rows": weak_rows,
        "ambiguous_rows": ambiguous_rows,
    }


# ====================================================
# LOAD RESULTS
# ====================================================
def load_tsp_results_from_path(path):

    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"No existe el directorio: {experiment_path}")

    print(f"Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():

        if folder.is_dir() and folder.name.lower().startswith("alpha_"):

            try:
                parts = folder.name.split("_")

                # Expected:
                # alpha_10.0_beta_0.2_A_1_50.0_A_2_5.0
                alpha = float(parts[1])
                beta = float(parts[3])
                A_1 = float(parts[6])
                A_2 = float(parts[9])

                resultados_dir = folder / "Resultados"

                if not resultados_dir.exists():
                    continue

                json_files = (
                    list(resultados_dir.glob("*.json")) +
                    list(resultados_dir.glob("*.JSON"))
                )

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
                            A_1,
                            A_2,
                            status,
                            init_dist,
                            ref_dist,
                            metrics["mean_gap"],
                            metrics["min_gap"],
                            metrics["mean_row_max"],
                            metrics["min_row_max"],
                            metrics["dead_rows"],
                            metrics["weak_rows"],
                            metrics["ambiguous_rows"],
                        ])

            except Exception as e:
                print(f"Carpeta ignorada: {folder.name} ({e})")

    if not records:
        raise RuntimeError("No se encontraron resultados válidos.")

    df = pd.DataFrame(
        records,
        columns=[
            "alpha",
            "beta",
            "A_1",
            "A_2",
            "status",
            "init_dist",
            "ref_dist",
            "mean_gap",
            "min_gap",
            "mean_row_max",
            "min_row_max",
            "dead_rows",
            "weak_rows",
            "ambiguous_rows",
        ]
    )

    df["perfect"] = df["status"] == "perfect"
    df["greedy"] = df["status"] == "greedy"
    df["valid"] = df["status"].isin(["perfect", "greedy"])

    return df


# ====================================================
# SUMMARY HELPERS
# ====================================================
def aggregate_regions(df):

    return (
        df.groupby(["alpha", "beta", "A_1", "A_2"])
        .agg(
            runs=("status", "count"),
            perfect_rate=("perfect", "mean"),
            greedy_rate=("greedy", "mean"),
            valid_rate=("valid", "mean"),
            mean_gap=("mean_gap", "mean"),
            min_gap=("min_gap", "mean"),
            mean_row_max=("mean_row_max", "mean"),
            min_row_max=("min_row_max", "mean"),
            dead_rows=("dead_rows", "mean"),
            weak_rows=("weak_rows", "mean"),
            ambiguous_rows=("ambiguous_rows", "mean"),
            init_dist_mean=("init_dist", "mean"),
            init_dist_std=("init_dist", "std"),
            ref_dist_mean=("ref_dist", "mean"),
            ref_dist_std=("ref_dist", "std"),
        )
        .reset_index()
    )


def write_region_table(f, title, table, max_rows=25):

    f.write(f"{title}\n")
    f.write("--------------------------------------------\n")

    if len(table) == 0:
        f.write("No rows\n\n")
        return

    for _, row in table.head(max_rows).iterrows():

        f.write(
            f"alpha={row['alpha']}, beta={row['beta']}, "
            f"A_1={row['A_1']}, A_2={row['A_2']} | "
            f"runs={int(row['runs'])}, "
            f"perfect_rate={row['perfect_rate']:.4f}, "
            f"greedy_rate={row['greedy_rate']:.4f}, "
            f"valid_rate={row['valid_rate']:.4f}, "
            f"mean_gap={row['mean_gap']:.4f}, "
            f"min_gap={row['min_gap']:.4f}, "
            f"mean_row_max={row['mean_row_max']:.4f}, "
            f"min_row_max={row['min_row_max']:.4f}, "
            f"dead_rows={row['dead_rows']:.4f}, "
            f"weak_rows={row['weak_rows']:.4f}, "
            f"ambiguous_rows={row['ambiguous_rows']:.4f}, "
            f"init_mean={row['init_dist_mean']:.4f}, "
            f"ref_mean={row['ref_dist_mean']:.4f}\n"
        )

    f.write("\n")


# ====================================================
# SAVE SUMMARY
# ====================================================
def save_status_summary_txt(df, out_path):

    out_path = Path(out_path)
    txt_file = out_path / "status_summary_multibarrido.txt"

    regions = aggregate_regions(df)

    perfect_regions = regions[regions["perfect_rate"] > 0].sort_values(
        ["perfect_rate", "valid_rate", "ref_dist_mean", "mean_gap"],
        ascending=[False, False, True, False]
    )

    greedy_regions = regions[regions["greedy_rate"] > 0].sort_values(
        ["greedy_rate", "valid_rate", "ref_dist_mean", "mean_gap"],
        ascending=[False, False, True, False]
    )

    valid_regions = regions[regions["valid_rate"] > 0].sort_values(
        ["valid_rate", "perfect_rate", "greedy_rate", "ref_dist_mean", "mean_gap"],
        ascending=[False, False, False, True, False]
    )

    clean_regions = regions.sort_values(
        ["dead_rows", "weak_rows", "ambiguous_rows", "mean_gap"],
        ascending=[True, True, True, False]
    )

    with open(txt_file, "w") as f:

        f.write("====================================================\n")
        f.write("TSP MULTI-SWEEP SUMMARY\n")
        f.write(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("====================================================\n\n")

        f.write("GLOBAL STATS\n")
        f.write("--------------------------------------------\n")
        f.write(f"Total rows: {len(df)}\n")
        f.write(f"Perfect rate: {df['perfect'].mean():.4f}\n")
        f.write(f"Greedy rate: {df['greedy'].mean():.4f}\n")
        f.write(f"Feasible rate: {df['valid'].mean():.4f}\n\n")

        f.write("GLOBAL METRICS\n")
        f.write("--------------------------------------------\n")
        f.write(f"Mean gap: {df['mean_gap'].mean():.4f}\n")
        f.write(f"Min gap mean: {df['min_gap'].mean():.4f}\n")
        f.write(f"Mean row max: {df['mean_row_max'].mean():.4f}\n")
        f.write(f"Min row max mean: {df['min_row_max'].mean():.4f}\n")
        f.write(f"Dead rows mean: {df['dead_rows'].mean():.4f}\n")
        f.write(f"Weak rows mean: {df['weak_rows'].mean():.4f}\n")
        f.write(f"Ambiguous rows mean: {df['ambiguous_rows'].mean():.4f}\n\n")

        write_region_table(
            f,
            "BEST PERFECT REGIONS",
            perfect_regions
        )

        write_region_table(
            f,
            "BEST GREEDY REGIONS",
            greedy_regions
        )

        write_region_table(
            f,
            "BEST VALID REGIONS",
            valid_regions
        )

        write_region_table(
            f,
            "GEOMETRICALLY CLEANEST REGIONS",
            clean_regions
        )

        f.write("PARAMETER RANGES WITH VALID SOLUTIONS\n")
        f.write("--------------------------------------------\n")

        valid_df = df[df["valid"]]

        if len(valid_df) == 0:
            f.write("No valid solutions found.\n")
        else:
            for col in ["alpha", "beta", "A_1", "A_2"]:
                vals = np.sort(valid_df[col].unique())
                f.write(f"{col}: {vals.tolist()}\n")

    print(f"Resumen guardado en: {txt_file}")


# ====================================================
# MAIN
# ====================================================
def analyze_multisweep(base_path):

    base_path = Path(base_path)

    df = load_tsp_results_from_path(base_path)

    save_status_summary_txt(df, base_path)

    print("Análisis finalizado.")


# ====================================================
# RUN
# ====================================================
if __name__ == "__main__":

    base_path = (
        "Your_route/PCE_Swipe_penalties/"
        "Experimentos_k4/TSP_m_15/job_1/k_4"
    )

    analyze_multisweep(base_path)