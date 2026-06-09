from pathlib import Path
import pandas as pd
import numpy as np


def load_all_summary_csvs(base_path):
    base_path = Path(base_path)

    csv_files = list(base_path.rglob("status_summary_multibarrido_bpp.csv"))

    if not csv_files:
        raise RuntimeError(f"No se encontraron CSVs en {base_path}")

    dfs = []

    for csv_file in csv_files:
        df = pd.read_csv(csv_file)

        # Extraer info del path, por ejemplo BPP_m_4 y k_3
        parts = csv_file.parts

        size = None
        k_val = None

        for p in parts:
            if p.startswith("BPP_m_"):
                size = int(p.replace("BPP_m_", ""))

            if p.startswith("k_"):
                k_val = int(p.replace("k_", ""))

        df["size"] = size
        df["k"] = k_val
        df["source_file"] = str(csv_file)

        dfs.append(df)

    return pd.concat(dfs, ignore_index=True)


def summarize_lambda_regions(df):
    """
    Busca regiones buenas de lambda_2/lambda_3 agregando sobre tamaños, k, alpha y beta.
    """

    # Nos quedamos con regiones que tienen soluciones perfectas
    valid = df[df["perfect_rate"] > 0].copy()

    if len(valid) == 0:
        raise RuntimeError("No hay regiones con perfect_rate > 0.")

    grouped = (
        valid.groupby(["lambda_2", "lambda_3"])
        .agg(
            runs=("runs", "sum"),

            num_sizes=("size", "nunique"),
            num_k=("k", "nunique"),

            perfect_rate_mean=("perfect_rate", "mean"),
            perfect_rate_min=("perfect_rate", "min"),
            feasible_rate_mean=("feasible_rate", "mean"),
            feasible_rate_min=("feasible_rate", "min"),

            perfect_mean_mean=("perfect_mean", "mean"),
            perfect_mean_min=("perfect_mean", "min"),
            perfect_mean_max=("perfect_mean", "max"),

            perfect_refined_mean=("perfect_refined_mean", "mean"),

            ambiguous_rows_mean=("ambiguous_rows", "mean"),
            weak_rows_mean=("weak_rows", "mean"),
            dead_rows_mean=("dead_rows", "mean"),

            mean_gap_mean=("mean_gap", "mean"),
            min_gap_mean=("min_gap", "mean"),
        )
        .reset_index()
    )

    ranked = grouped.sort_values(
        [
            "perfect_rate_min",
            "perfect_rate_mean",
            "perfect_mean_mean",
            "perfect_mean_max",
            "ambiguous_rows_mean",
            "mean_gap_mean",
        ],
        ascending=[
            False,
            False,
            True,
            True,
            True,
            False,
        ]
    )

    return ranked


def summarize_lambda_regions_by_size(df):
    """
    Tabla por tamaño para ver si una pareja lambda_2/lambda_3 falla en algún N.
    """

    valid = df[df["perfect_rate"] > 0].copy()

    grouped = (
        valid.groupby(["size", "lambda_2", "lambda_3"])
        .agg(
            perfect_rate_mean=("perfect_rate", "mean"),
            perfect_rate_max=("perfect_rate", "max"),
            feasible_rate_mean=("feasible_rate", "mean"),
            perfect_mean_mean=("perfect_mean", "mean"),
            perfect_refined_mean=("perfect_refined_mean", "mean"),
            ambiguous_rows_mean=("ambiguous_rows", "mean"),
            mean_gap_mean=("mean_gap", "mean"),
        )
        .reset_index()
        .sort_values(
            [
                "size",
                "perfect_rate_mean",
                "perfect_mean_mean",
                "ambiguous_rows_mean",
            ],
            ascending=[
                True,
                False,
                True,
                True,
            ]
        )
    )

    return grouped


def analyze_lambda_ranges(base_path, output_name="lambda_range_summary"):
    base_path = Path(base_path)

    df = load_all_summary_csvs(base_path)

    global_summary = summarize_lambda_regions(df)
    by_size_summary = summarize_lambda_regions_by_size(df)

    global_csv = base_path / f"{output_name}_global.csv"
    by_size_csv = base_path / f"{output_name}_by_size.csv"
    txt_file = base_path / f"{output_name}.txt"

    global_summary.to_csv(global_csv, index=False)
    by_size_summary.to_csv(by_size_csv, index=False)

    with open(txt_file, "w") as f:
        f.write("====================================================\n")
        f.write("BPP LAMBDA RANGE SUMMARY\n")
        f.write("====================================================\n\n")

        f.write("BEST GLOBAL LAMBDA_2 / LAMBDA_3 REGIONS\n")
        f.write("--------------------------------------------\n")

        for _, row in global_summary.head(30).iterrows():
            f.write(
                f"lambda_2={row['lambda_2']}, "
                f"lambda_3={row['lambda_3']} | "
                f"num_sizes={int(row['num_sizes'])}, "
                f"num_k={int(row['num_k'])}, "
                f"perfect_rate_min={row['perfect_rate_min']:.4f}, "
                f"perfect_rate_mean={row['perfect_rate_mean']:.4f}, "
                f"feasible_rate_min={row['feasible_rate_min']:.4f}, "
                f"perfect_mean_mean={row['perfect_mean_mean']:.4f}, "
                f"perfect_mean_max={row['perfect_mean_max']:.4f}, "
                f"ambiguous_rows_mean={row['ambiguous_rows_mean']:.4f}, "
                f"mean_gap_mean={row['mean_gap_mean']:.4f}\n"
            )

        f.write("\n\nBEST LAMBDA REGIONS BY SIZE\n")
        f.write("--------------------------------------------\n")

        for size, g in by_size_summary.groupby("size"):
            f.write(f"\nSIZE {size}\n")
            f.write("--------------------------------------------\n")

            for _, row in g.head(10).iterrows():
                f.write(
                    f"lambda_2={row['lambda_2']}, "
                    f"lambda_3={row['lambda_3']} | "
                    f"perfect_rate_mean={row['perfect_rate_mean']:.4f}, "
                    f"perfect_rate_max={row['perfect_rate_max']:.4f}, "
                    f"feasible_rate_mean={row['feasible_rate_mean']:.4f}, "
                    f"perfect_mean_mean={row['perfect_mean_mean']:.4f}, "
                    f"perfect_refined_mean={row['perfect_refined_mean']:.4f}, "
                    f"ambiguous_rows_mean={row['ambiguous_rows_mean']:.4f}, "
                    f"mean_gap_mean={row['mean_gap_mean']:.4f}\n"
                )

    print(f"Guardado resumen global en: {global_csv}")
    print(f"Guardado resumen por tamaño en: {by_size_csv}")
    print(f"Guardado resumen TXT en: {txt_file}")


if __name__ == "__main__":

    base_path = (
        "Your_path"
        "z_BPP/PCE_v2/PCE_multibarrido/Experimentos_k4"
    )

    analyze_lambda_ranges(base_path)