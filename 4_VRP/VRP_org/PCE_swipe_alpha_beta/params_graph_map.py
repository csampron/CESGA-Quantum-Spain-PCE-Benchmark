import matplotlib.pyplot as plt
from pathlib import Path
import pandas as pd
import json
import numpy as np


# ====================================================
# LOAD RESULTS (FEASIBLE FILTER ONLY)
# ====================================================

def load_vrp_results_from_path(path):

    base_path = Path(path)

    if not base_path.exists():
        raise FileNotFoundError(base_path)

    print(f"📂 Leyendo: {base_path}")

    records = []

    for k_folder in base_path.iterdir():

        if not k_folder.is_dir() or not k_folder.name.startswith("k_"):
            continue

        k_val = int(k_folder.name.split("_")[1])

        for folder in k_folder.iterdir():

            if not folder.is_dir() or not folder.name.startswith("alpha_"):
                continue

            try:
                parts = folder.name.split("_")
                alpha = float(parts[1])
                beta = float(parts[3])

                result_dir = folder / "Resultados"
                if not result_dir.exists():
                    result_dir = folder

                json_files = list(result_dir.glob("*.json")) + list(result_dir.glob("*.JSON"))

                if not json_files:
                    continue

                # -----------------------------
                # acumuladores SOLO FEASIBLE
                # -----------------------------

                init_routes_counts = []
                init_costs = []
                ref_costs = []

                total = 0
                feasible = 0

                for jf in json_files:

                    with open(jf) as f:
                        data = json.load(f)

                    results = data.get("resultados", [])
                    if not results:
                        results = [data]

                    for res in results:

                        total += 1

                        if not res.get("initial_feasible", False):
                            continue

                        feasible += 1

                        # rutas iniciales
                        init_routes = res.get("initial_routes", {})
                        init_routes_counts.append(len(init_routes))

                        # costes
                        if res.get("initial_cost") is not None:
                            init_costs.append(res["initial_cost"])

                        if res.get("refined_cost") is not None:
                            ref_costs.append(res["refined_cost"])

                # -----------------------------
                # IMPORTANTÍSIMO: NaN si no hay datos
                # -----------------------------

                records.append([

                    k_val,
                    alpha,
                    beta,

                    np.mean(init_routes_counts) if init_routes_counts else np.nan,
                    np.std(init_routes_counts) if init_routes_counts else np.nan,

                    np.mean(init_costs) if init_costs else np.nan,
                    np.std(init_costs) if init_costs else np.nan,

                    np.mean(ref_costs) if ref_costs else np.nan,
                    np.std(ref_costs) if ref_costs else np.nan,

                    feasible / total if total > 0 else np.nan
                ])

            except Exception as e:
                print(f"skip {folder.name}: {e}")

    return pd.DataFrame(records, columns=[

        "k",
        "alpha",
        "beta",

        "mean_init_routes",
        "std_init_routes",

        "mean_init_cost",
        "std_init_cost",

        "mean_ref_cost",
        "std_ref_cost",

        "feasible_rate_init"
    ])


# ====================================================
# HEATMAP (NaN = blanco)
# ====================================================

def plot_heatmap(arr, x_vals, y_vals, title, xlabel, ylabel, cmap, out_path):

    fig, ax = plt.subplots(figsize=(12, 6))

    arr = np.ma.masked_invalid(arr)

    cmap = plt.cm.get_cmap(cmap).copy()
    cmap.set_bad(color="white")

    im = ax.imshow(arr, origin="lower", aspect="auto", cmap=cmap)

    ax.set_xticks(range(len(x_vals)))
    ax.set_xticklabels([f"{x:.2f}" for x in x_vals])

    ax.set_yticks(range(len(y_vals)))
    ax.set_yticklabels([f"{y:.2f}" for y in y_vals])

    ax.set_xlabel(xlabel)
    ax.set_ylabel(ylabel)
    ax.set_title(title)

    fig.colorbar(im, ax=ax)

    plt.tight_layout()
    plt.savefig(out_path, dpi=300)
    plt.close()


# ====================================================
# MAIN
# ====================================================

def plot_vrp_results(base_path):

    base_path = Path(base_path)
    df = load_vrp_results_from_path(base_path)

    for k_val in sorted(df["k"].unique()):

        df_k = df[df["k"] == k_val]

        alpha_vals = np.sort(df_k["alpha"].unique())
        beta_vals = np.sort(df_k["beta"].unique())

        def pivot(col):
            return df_k.pivot(index="beta", columns="alpha", values=col)\
                       .reindex(index=beta_vals, columns=alpha_vals)

        out_dir = base_path / f"k_{k_val}"
        out_dir.mkdir(exist_ok=True)

        # ---------------------------
        # ROUTES
        # ---------------------------
        plot_heatmap(
            pivot("mean_init_routes").to_numpy(),
            alpha_vals, beta_vals,
            "Mean number of  feasible initial routes",
            "alpha", "beta",
            "viridis",
            out_dir / "VRP_2_vehicles_m_mean_init_routes.png"
        )

        plot_heatmap(
            pivot("std_init_routes").to_numpy(),
            alpha_vals, beta_vals,
            "Std of  feasible initial routes (feasible only)",
            "alpha", "beta",
            "plasma",
            out_dir / "VRP_2_vehicles_m_std_init_routes.png"
        )

        # ---------------------------
        # COSTS
        # ---------------------------
        plot_heatmap(
            pivot("mean_init_cost").to_numpy(),
            alpha_vals, beta_vals,
            "Mean initial cost of feasible routes",
            "alpha", "beta",
            "viridis",
            out_dir / "VRP_2_vehicles_m_mean_init_cost.png"
        )

        plot_heatmap(
            pivot("mean_ref_cost").to_numpy(),
            alpha_vals, beta_vals,
            "Mean refined cost of feasible routes",
            "alpha", "beta",
            "plasma",
            out_dir / "VRP_2_vehicles_m_mean_ref_cost.png"
        )

        # ---------------------------
        # FEASIBILITY
        # ---------------------------
        plot_heatmap(
            pivot("feasible_rate_init").to_numpy(),
            alpha_vals, beta_vals,
            "Rate of feasible routes",
            "alpha", "beta",
            "cividis",
            out_dir / "VRP_2_vehicles_m_feasible.png"
        )

    print("✔ Done")

# ====================================================
# 4) RUN
# ====================================================

if __name__ == "__main__":

    base_path = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/VRP_org_2_vehicles/PCE_barrido_alpha_beta/Experimentos/VRP_m_6_inst_1/10_05_2026_10_22"
    plot_vrp_results(base_path)