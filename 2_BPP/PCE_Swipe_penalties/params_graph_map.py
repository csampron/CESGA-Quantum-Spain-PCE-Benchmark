from pathlib import Path
import pandas as pd
import json
import numpy as np
from datetime import datetime
import re


# ====================================================
# THRESHOLDS EMBEDDING
# ====================================================

DEAD_ROW_THRESHOLD = 0.40
WEAK_ROW_THRESHOLD = 0.50
AMBIGUOUS_GAP_THRESHOLD = 0.05


# ====================================================
# AUX METRICS
# ====================================================

def compute_row_metrics(x_values):
    gaps = []
    row_maxs = []

    dead_rows = 0
    weak_rows = 0
    ambiguous_rows = 0

    for _, vals in x_values.items():
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
# SAFE HELPERS
# ====================================================

def safe_mean(series):
    series = pd.to_numeric(series, errors="coerce").dropna()
    return series.mean() if len(series) > 0 else np.nan


def safe_std(series):
    series = pd.to_numeric(series, errors="coerce").dropna()
    return series.std() if len(series) > 1 else np.nan


# ====================================================
# LOAD RESULTS
# ====================================================

def parse_folder_name(folder_name):
    """
    Espera carpetas tipo:
    alpha_35.0_beta_0.0_lambda_2_50.0_lambda_3_100.0
    """

    match = re.search(
        r"alpha_(.*?)_beta_(.*?)_lambda_2_(.*?)_lambda_3_(.*)",
        folder_name
    )

    if match is None:
        raise ValueError(f"Nombre de carpeta no reconocido: {folder_name}")

    alpha = float(match.group(1))
    beta = float(match.group(2))
    lambda_2 = float(match.group(3))
    lambda_3 = float(match.group(4))

    return alpha, beta, lambda_2, lambda_3


def load_bpp_results_from_path(path):

    experiment_path = Path(path)

    if not experiment_path.exists():
        raise FileNotFoundError(f"No existe el directorio: {experiment_path}")

    print(f"Leyendo resultados en: {experiment_path}")

    records = []

    for folder in experiment_path.iterdir():

        if folder.is_dir() and folder.name.lower().startswith("alpha_"):

            try:
                alpha, beta, lambda_2, lambda_3 = parse_folder_name(folder.name)

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

                        status = res.get("status_initial", "infeasible")

                        num_bins_used = res.get("num_bins_used")
                        num_bins_used_post = res.get("num_bins_used_post")

                        reconstruction_info = res.get("reconstruction_info", {})

                        num_combinations = reconstruction_info.get(
                            "num_combinations",
                            np.nan
                        )

                        feasible_solutions = reconstruction_info.get(
                            "feasible_solutions",
                            np.nan
                        )

                        ambiguous_items = reconstruction_info.get(
                            "ambiguous_items",
                            []
                        )

                        unassigned_items = reconstruction_info.get(
                            "unassigned_items",
                            []
                        )

                        x_values = res.get("x_values", {})
                        metrics = compute_row_metrics(x_values)

                        records.append([
                            alpha,
                            beta,
                            lambda_2,
                            lambda_3,
                            status,
                            num_bins_used,
                            num_bins_used_post,
                            num_combinations,
                            feasible_solutions,
                            len(ambiguous_items),
                            len(unassigned_items),
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
            "lambda_2",
            "lambda_3",
            "status",
            "num_bins_used",
            "num_bins_used_post",
            "num_combinations",
            "feasible_solutions",
            "ambiguous_items",
            "unassigned_items",
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
    df["combinatorial"] = df["status"] == "combinatorial"
    df["infeasible"] = df["status"] == "infeasible"
    df["feasible"] = df["status"].isin(["perfect", "combinatorial"])

    return df


# ====================================================
# AGGREGATE
# ====================================================

def aggregate_regions(df):

    group_cols = [
        "alpha",
        "beta",
        "lambda_2",
        "lambda_3",
    ]

    rows = []

    for keys, g in df.groupby(group_cols):

        perfect_g = g[g["perfect"]]
        combinatorial_g = g[g["combinatorial"]]

        row = {
            "alpha": keys[0],
            "beta": keys[1],
            "lambda_2": keys[2],
            "lambda_3": keys[3],

            "runs": len(g),

            "feasible_rate": g["feasible"].mean(),

            "perfect_rate": g["perfect"].mean(),
            "perfect_mean": safe_mean(perfect_g["num_bins_used"]),
            "perfect_std": safe_std(perfect_g["num_bins_used"]),
            "perfect_refined_mean": safe_mean(
                perfect_g["num_bins_used_post"]
            ),
            "perfect_refined_std": safe_std(
                perfect_g["num_bins_used_post"]
            ),

            "combinatorial_rate": g["combinatorial"].mean(),
            "combinatorial_mean": safe_mean(
                combinatorial_g["num_bins_used"]
            ),
            "combinatorial_std": safe_std(
                combinatorial_g["num_bins_used"]
            ),
            "combinatorial_refined_mean": safe_mean(
                combinatorial_g["num_bins_used_post"]
            ),
            "combinatorial_refined_std": safe_std(
                combinatorial_g["num_bins_used_post"]
            ),

            "mean_gap": g["mean_gap"].mean(),
            "min_gap": g["min_gap"].mean(),
            "mean_row_max": g["mean_row_max"].mean(),
            "min_row_max": g["min_row_max"].mean(),
            "dead_rows": g["dead_rows"].mean(),
            "weak_rows": g["weak_rows"].mean(),
            "ambiguous_rows": g["ambiguous_rows"].mean(),

            "num_combinations_mean": g["num_combinations"].mean(),
            "num_combinations_max": g["num_combinations"].max(),
            "feasible_solutions_mean": g["feasible_solutions"].mean(),
            "ambiguous_items_mean": g["ambiguous_items"].mean(),
            "unassigned_items_mean": g["unassigned_items"].mean(),
        }

        rows.append(row)

    return pd.DataFrame(rows)


# ====================================================
# WRITE TABLE
# ====================================================

def write_region_table(f, title, table, max_rows=25):

    f.write(f"{title}\n")
    f.write("--------------------------------------------\n")

    if len(table) == 0:
        f.write("No rows\n\n")
        return

    for _, row in table.head(max_rows).iterrows():

        f.write(
            f"alpha={row['alpha']}, beta={row['beta']}, "
            f"lambda_2={row['lambda_2']}, "
            f"lambda_3={row['lambda_3']} | "
            f"runs={int(row['runs'])}, "
            f"feasible_rate={row['feasible_rate']:.4f}, "
            f"perfect_rate={row['perfect_rate']:.4f}, "
            f"combinatorial_rate={row['combinatorial_rate']:.4f}, "
            f"perfect_mean={row['perfect_mean']:.4f}, "
            f"perfect_std={row['perfect_std']:.4f}, "
            f"perfect_refined_mean={row['perfect_refined_mean']:.4f}, "
            f"perfect_refined_std={row['perfect_refined_std']:.4f}, "
            f"combinatorial_mean={row['combinatorial_mean']:.4f}, "
            f"combinatorial_std={row['combinatorial_std']:.4f}, "
            f"combinatorial_refined_mean="
            f"{row['combinatorial_refined_mean']:.4f}, "
            f"combinatorial_refined_std="
            f"{row['combinatorial_refined_std']:.4f}, "
            f"mean_gap={row['mean_gap']:.4f}, "
            f"min_gap={row['min_gap']:.4f}, "
            f"mean_row_max={row['mean_row_max']:.4f}, "
            f"min_row_max={row['min_row_max']:.4f}, "
            f"dead_rows={row['dead_rows']:.4f}, "
            f"weak_rows={row['weak_rows']:.4f}, "
            f"ambiguous_rows={row['ambiguous_rows']:.4f}, "
            f"num_combinations_mean="
            f"{row['num_combinations_mean']:.4f}, "
            f"num_combinations_max="
            f"{row['num_combinations_max']:.4f}\n"
        )

    f.write("\n")


# ====================================================
# SAVE SUMMARY
# ====================================================

def save_status_summary_txt(df, out_path):

    out_path = Path(out_path)
    txt_file = out_path / "status_summary_multibarrido_bpp.txt"
    csv_file = out_path / "status_summary_multibarrido_bpp.csv"

    regions = aggregate_regions(df)
    regions.to_csv(csv_file, index=False)

    # ------------------------------------------------------------
    # Ranking general
    # ------------------------------------------------------------

    best_regions = regions.sort_values(
        [
            "perfect_rate",
            "feasible_rate",
            "perfect_mean",
            "perfect_std",
            "perfect_refined_mean",
            "ambiguous_rows",
            "mean_gap",
        ],
        ascending=[
            False,
            False,
            True,
            True,
            True,
            True,
            False,
        ]
    )

    # ------------------------------------------------------------
    # Todas las regiones con perfect_rate > 0,
    # priorizando perfect_rate y después perfect_mean
    # ------------------------------------------------------------

    perfect_regions = regions[regions["perfect_rate"] > 0].sort_values(
        [
            "perfect_rate",
            "perfect_mean",
            "perfect_std",
            "perfect_refined_mean",
            "ambiguous_rows",
            "mean_gap",
        ],
        ascending=[
            False,
            True,
            True,
            True,
            True,
            False,
        ]
    )

    # ------------------------------------------------------------
    # Regiones que alcanzan el máximo perfect_rate
    # y, dentro de ellas, menor perfect_mean
    # ------------------------------------------------------------

    max_perfect_rate = regions["perfect_rate"].max()

    best_perfect_rate_regions = regions[
        regions["perfect_rate"] == max_perfect_rate
    ].sort_values(
        [
            "perfect_mean",
            "perfect_std",
            "perfect_refined_mean",
            "ambiguous_rows",
            "mean_gap",
        ],
        ascending=[
            True,
            True,
            True,
            True,
            False,
        ]
    )

    # ------------------------------------------------------------
    # Regiones con el menor perfect_mean existente
    # ------------------------------------------------------------

    valid_perfect = regions[
        regions["perfect_rate"] > 0
    ].copy()

    min_perfect_mean = valid_perfect["perfect_mean"].min()

    best_min_bin_regions = valid_perfect[
        valid_perfect["perfect_mean"] == min_perfect_mean
    ].sort_values(
        [
            "perfect_rate",
            "perfect_std",
            "perfect_refined_mean",
            "ambiguous_rows",
            "mean_gap",
        ],
        ascending=[
            False,
            True,
            True,
            True,
            False,
        ]
    )

    # ------------------------------------------------------------
    # Regiones combinatoriales
    # ------------------------------------------------------------

    combinatorial_regions = regions[
        regions["combinatorial_rate"] > 0
    ].sort_values(
        [
            "combinatorial_rate",
            "feasible_rate",
            "combinatorial_refined_mean",
            "combinatorial_std",
            "mean_gap",
        ],
        ascending=[
            False,
            False,
            True,
            True,
            False,
        ]
    )

    # ------------------------------------------------------------
    # Regiones geométricamente limpias
    # ------------------------------------------------------------

    clean_regions = regions.sort_values(
        [
            "dead_rows",
            "weak_rows",
            "ambiguous_rows",
            "mean_gap",
        ],
        ascending=[
            True,
            True,
            True,
            False,
        ]
    )

    with open(txt_file, "w") as f:

        f.write("====================================================\n")
        f.write("BPP MULTI-SWEEP SUMMARY\n")
        f.write(f"Timestamp: {datetime.now().isoformat(timespec='seconds')}\n")
        f.write("====================================================\n\n")

        f.write("GLOBAL STATS\n")
        f.write("--------------------------------------------\n")
        f.write(f"Total rows: {len(df)}\n")
        f.write(f"Feasible rate: {df['feasible'].mean():.4f}\n")
        f.write(f"Perfect rate: {df['perfect'].mean():.4f}\n")
        f.write(f"Combinatorial rate: {df['combinatorial'].mean():.4f}\n")
        f.write(f"Infeasible rate: {df['infeasible'].mean():.4f}\n\n")

        f.write("GLOBAL BIN METRICS\n")
        f.write("--------------------------------------------\n")
        f.write(
            "Perfect num bins mean: "
            f"{safe_mean(df[df['perfect']]['num_bins_used']):.4f}\n"
        )
        f.write(
            "Perfect num bins std: "
            f"{safe_std(df[df['perfect']]['num_bins_used']):.4f}\n"
        )
        f.write(
            "Perfect refined num bins mean: "
            f"{safe_mean(df[df['perfect']]['num_bins_used_post']):.4f}\n"
        )
        f.write(
            "Perfect refined num bins std: "
            f"{safe_std(df[df['perfect']]['num_bins_used_post']):.4f}\n"
        )

        f.write(
            "Combinatorial num bins mean: "
            f"{safe_mean(df[df['combinatorial']]['num_bins_used']):.4f}\n"
        )
        f.write(
            "Combinatorial num bins std: "
            f"{safe_std(df[df['combinatorial']]['num_bins_used']):.4f}\n"
        )
        f.write(
            "Combinatorial refined num bins mean: "
            f"{safe_mean(df[df['combinatorial']]['num_bins_used_post']):.4f}\n"
        )
        f.write(
            "Combinatorial refined num bins std: "
            f"{safe_std(df[df['combinatorial']]['num_bins_used_post']):.4f}\n\n"
        )

        f.write("GLOBAL EMBEDDING METRICS\n")
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
            "BEST REGIONS",
            best_regions
        )

        write_region_table(
            f,
            "BEST PERFECT REGIONS",
            perfect_regions
        )

        f.write("BEST REGIONS AMONG MAX PERFECT RATE\n")
        f.write("--------------------------------------------\n")
        f.write(f"Maximum perfect_rate found: {max_perfect_rate:.4f}\n\n")

        

        write_region_table(
            f,
            "REGIONS WITH MAX PERFECT RATE SORTED BY PERFECT_MEAN",
            best_perfect_rate_regions
        )

        f.write("BEST REGIONS AMONG LOWEST PERFECT_MEAN\n")
        f.write("--------------------------------------------\n")
        f.write(f"Lowest perfect_mean found: {min_perfect_mean:.4f}\n\n")

        write_region_table(
            f,
            "BEST REGIONS BY LOWEST PERFECT_MEAN",
            best_min_bin_regions    
        )

        write_region_table(
            f,
            "BEST COMBINATORIAL REGIONS",
            combinatorial_regions
        )

        write_region_table(
            f,
            "GEOMETRICALLY CLEANEST REGIONS",
            clean_regions
        )

        f.write("PARAMETER RANGES WITH FEASIBLE SOLUTIONS\n")
        f.write("--------------------------------------------\n")

        feasible_df = df[df["feasible"]]

        if len(feasible_df) == 0:
            f.write("No feasible solutions found.\n")
        else:
            for col in [
                "alpha",
                "beta",
                "lambda_2",
                "lambda_3",
            ]:
                vals = np.sort(feasible_df[col].dropna().unique())
                f.write(f"{col}: {vals.tolist()}\n")

        f.write("\nPARAMETER RANGES WITH PERFECT SOLUTIONS\n")
        f.write("--------------------------------------------\n")

        perfect_df = df[df["perfect"]]

        if len(perfect_df) == 0:
            f.write("No perfect solutions found.\n")
        else:
            for col in [
                "alpha",
                "beta",
                "lambda_2",
                "lambda_3",
            ]:
                vals = np.sort(perfect_df[col].dropna().unique())
                f.write(f"{col}: {vals.tolist()}\n")

    print(f"Resumen TXT guardado en: {txt_file}")
    print(f"Resumen CSV guardado en: {csv_file}")


# ====================================================
# MAIN
# ====================================================

def analyze_multisweep_bpp(base_path):

    base_path = Path(base_path)

    df = load_bpp_results_from_path(base_path)

    save_status_summary_txt(df, base_path)

    print("Análisis BPP finalizado.")


# ====================================================
# RUN
# ====================================================

if __name__ == "__main__":

    base_path = (
        "Your_path"
        "z_BPP/PCE_v2/PCE_multibarrido/"
        "Experimentos_prueba_k3/BPP_m_10/job_1/k_3"
    )

    analyze_multisweep_bpp(base_path)