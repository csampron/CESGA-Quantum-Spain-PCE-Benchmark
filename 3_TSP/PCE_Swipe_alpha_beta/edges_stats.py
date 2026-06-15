import os
import sys
from pathlib import Path
import numpy as np

sys.path.append(os.getenv("HOME"))

from src.op_graph import load_graph


# ====================================================
# CONFIG
# ====================================================
SIZES = [4, 5, 6, 7, 8, 9, 10, 15, 22, 25]

EDGE_THRESHOLD = 1000.0

GRAPHS_DIR = Path(
    "/mnt/netapp1/Store_CESGA/home/cesga/falonso/"
    "z_TSP/TSP_fixed_cero_unfold/"
    "PCE_TSP_barrido_alpha_beta/src/graphs"
)


# ====================================================
# AUX
# ====================================================
def get_max_incident_weight_node(G):
    """
    Devuelve el nodo con mayor suma de pesos incidentes,
    su suma total y su grado ponderado/no ponderado.
    """

    best_node = None
    best_sum = -np.inf
    best_degree = None

    for node in G.nodes():

        incident_weights = [
            data["weight"]
            for _, _, data in G.edges(node, data=True)
        ]

        incident_sum = float(np.sum(incident_weights))
        degree = len(incident_weights)

        if incident_sum > best_sum:
            best_sum = incident_sum
            best_node = node
            best_degree = degree

    return best_node, best_sum, best_degree


# ====================================================
# MAIN
# ====================================================
def analyze_graphs(edge_threshold=1000.0):

    txt_file = GRAPHS_DIR / f"edge_summary_{int(edge_threshold)}.txt"

    with open(txt_file, "w") as f:

        f.write("====================================================\n")
        f.write("TSP EDGE ANALYSIS\n")
        f.write("====================================================\n\n")

        f.write(f"Threshold = {edge_threshold}\n\n")

        for n in SIZES:

            graph_file = GRAPHS_DIR / f"tsp_{n}.tsp"

            if not graph_file.exists():
                print(f"⚠️ No existe {graph_file}")
                continue

            G, num_ver, mean_edge_weight, max_edge_weight = load_graph(
                str(graph_file)
            )

            weights = np.array(
                [d["weight"] for _, _, d in G.edges(data=True)],
                dtype=float
            )

            num_edges = len(weights)

            edges_above_threshold = int(np.sum(weights >= edge_threshold))

            frac_above = (
                edges_above_threshold / num_edges
                if num_edges > 0 else 0.0
            )

            total_weight_sum = float(np.sum(weights))

            max_edge_times_n_minus_1 = float(
                max_edge_weight * (num_ver - 1)
            )

            max_edge_times_n_minus_1_sq = float(
                max_edge_weight * (num_ver - 1) ** 2
            )

            (
                max_incident_node,
                max_incident_weight_sum,
                max_incident_degree
            ) = get_max_incident_weight_node(G)

            print(
                f"N={n:2d} | "
                f"edges={num_edges:4d} | "
                f"mean={mean_edge_weight:10.2f} | "
                f"max={max_edge_weight:10.2f} | "
                f"sum={total_weight_sum:12.2f} | "
                f"max*(N-1)={max_edge_times_n_minus_1:12.2f} | "
                f"max incident={max_incident_weight_sum:12.2f} | "
                f">={edge_threshold}: {edges_above_threshold:4d}"
            )

            f.write("--------------------------------------------\n")
            f.write(f"Size: {n}\n")
            f.write(f"Vertices: {num_ver}\n")
            f.write(f"Edges: {num_edges}\n")
            f.write(f"Mean edge weight: {mean_edge_weight:.4f}\n")
            f.write(f"Max edge weight: {max_edge_weight:.4f}\n")
            f.write(f"Total weight sum: {total_weight_sum:.4f}\n")
            f.write(
                f"Max edge * (N-1): "
                f"{max_edge_times_n_minus_1:.4f}\n"
            )
            f.write(
                f"Max edge * (N-1)^2: "
                f"{max_edge_times_n_minus_1_sq:.4f}\n"
            )
            f.write(
                f"Node with max incident weight sum: "
                f"{max_incident_node}\n"
            )
            f.write(
                f"Max incident weight sum: "
                f"{max_incident_weight_sum:.4f}\n"
            )
            f.write(
                f"Degree of max incident node: "
                f"{max_incident_degree}\n"
            )
            f.write(
                f"Edges >= {edge_threshold}: "
                f"{edges_above_threshold}\n"
            )
            f.write(
                f"Fraction >= {edge_threshold}: "
                f"{frac_above:.4f}\n\n"
            )

    print(f"\n💾 Resumen guardado en:\n{txt_file}")


# ====================================================
# RUN
# ====================================================
if __name__ == "__main__":
    analyze_graphs(edge_threshold=EDGE_THRESHOLD)