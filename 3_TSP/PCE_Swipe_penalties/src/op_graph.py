import networkx as nx
import numpy as np
import math

def calc_cut_size(graph, partition0, partition1):
    """Calculate the cut size of the given partitions of the graph."""
 
    cut_size = 0.0
    for edge0, edge1, data in graph.edges(data = True):
        if edge0 in partition0 and edge1 in partition1 or edge0 in partition1 and edge1 in partition0:
            cut_size += data.get("weight", 1.0)
    return cut_size

def load_graph(path):
    """
    Lee un archivo TSP en formato TSPLIB (NODE_COORD_SECTION con EUC_2D)
    y crea un grafo completo ponderado con networkx.

    Devuelve:
    - G
    - número de nodos
    - media de pesos de aristas
    """
    coords = {}

    with open(path, "r") as f:
        lines = f.readlines()

    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("NODE_COORD_SECTION"):
            start = i + 1
            break

    if start is None:
        raise ValueError(
            "No se encontró la sección NODE_COORD_SECTION en el archivo TSP."
        )

    for line in lines[start:]:
        line = line.strip()

        if line == "" or line.startswith("EOF"):
            break

        parts = line.split()

        if len(parts) >= 3:
            node = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            coords[node] = (x, y)

    G = nx.Graph()

    for node, (x, y) in coords.items():
        G.add_node(node, pos=(x, y))

    nodes = list(coords.keys())
    edge_weights = []

    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):

            n1, n2 = nodes[i], nodes[j]

            x1, y1 = coords[n1]
            x2, y2 = coords[n2]

            dist = int(math.sqrt((x1 - x2)**2 + (y1 - y2)**2) + 0.5)

            G.add_edge(n1, n2, weight=dist)
            edge_weights.append(dist)

    mean_edge_weight = float(np.mean(edge_weights))
    max_edge_weight = float(np.max(edge_weights))

    return G, len(nodes), mean_edge_weight, max_edge_weight

