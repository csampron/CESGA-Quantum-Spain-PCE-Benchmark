import networkx as nx
import math

def calc_cut_size(graph, partition0, partition1):
    """Calculate the cut size of the given partitions of the graph."""
 
    cut_size = 0.0
    for edge0, edge1, data in graph.edges(data = True):
        if edge0 in partition0 and edge1 in partition1 or edge0 in partition1 and edge1 in partition0:
            cut_size += data.get("weight", 1.0)
    return cut_size



def load_vrp_graph(path):
    """
    Lee un archivo CVRP estilo TSPLIB y devuelve un grafo completo con:
    - nodos reindexados desde 0 (0 = depósito)
    - nodo 0 = depósito
    - capacidad de cada vehículo (CAPACITY)
    - demanda de cada nodo (por defecto 1)

    Returns
    -------
    G : nx.Graph
        Grafo completo con atributos 'pos' en nodos y 'weight' en aristas
    n_nodes : int
        Número de nodos
    depot : int
        Nodo depósito (0)
    capacity : int
        Capacidad de cada vehículo
    demand : dict {v: int}
        Demanda de cada nodo (1 para todos)
    """
    coords = {}
    capacity = None

    with open(path, "r") as f:
        lines = f.readlines()

    # --- 1. Leer CAPACITY ---
    for line in lines:
        line = line.strip()
        if line.startswith("CAPACITY"):
            capacity = int(line.split(":")[1].strip())
            break
    if capacity is None:
        raise ValueError("No se encontró CAPACITY en el archivo CVRP.")

    # --- 2. Encontrar NODE_COORD_SECTION ---
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("NODE_COORD_SECTION"):
            start = i + 1
            break
    if start is None:
        raise ValueError("No se encontró NODE_COORD_SECTION")

    # --- 3. Leer coordenadas ---
    for line in lines[start:]:
        line = line.strip()
        if line == "" or line.startswith("EOF"):
            break
        parts = line.split()
        node = int(parts[0]) - 1  # 🔥 Reindexado a 0
        x = float(parts[1])
        y = float(parts[2])
        coords[node] = (x, y)

    # --- 4. Construir grafo completo ---
    G = nx.Graph()
    for node, (x, y) in coords.items():
        G.add_node(node, pos=(x, y))

    nodes = list(coords.keys())
    for i in nodes:
        for j in nodes:
            if i == j:
                continue
            x1, y1 = coords[i]
            x2, y2 = coords[j]
            dist = math.sqrt((x1 - x2)**2 + (y1 - y2)**2)
            G.add_edge(i, j, weight=dist)

    depot = 0  # nodo depósito
    demand = {v: 1 for v in nodes}  # demanda uniforme = 1

    return G, len(nodes), depot, capacity, demand


