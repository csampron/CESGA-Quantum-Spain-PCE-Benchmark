import os
import matplotlib.pyplot as plt
import networkx as nx
import numpy as np

def read_tsp_file(filepath):
    """
    Lee un archivo .tsp/.vrp en formato TSPLIB (TSP o CVRP)
    y devuelve un diccionario {node_id: (x, y)}.
    """
    coords = {}
    with open(filepath, 'r') as f:
        lines = f.readlines()

    node_section = False

    for line in lines:
        line = line.strip()

        if line.startswith("NODE_COORD_SECTION"):
            node_section = True
            continue

        # Si empieza otra sección, dejamos de leer coordenadas
        if node_section and (
            line.startswith("DEMAND_SECTION")
            or line.startswith("DEPOT_SECTION")
            or line.startswith("EOF")
        ):
            break

        if node_section:
            parts = line.split()
            if len(parts) != 3:
                continue  # seguridad extra

            node_id = int(parts[0])
            x = float(parts[1])
            y = float(parts[2])
            coords[node_id] = (x, y)

    return coords


def draw_tsp_graph_to_dir(coords, output_dir, filename="grafo_tsp.png", show_plot=True):
    """
    Dibuja el grafo TSP con pesos de arista y guarda la imagen en 'output_dir'.
    """
    os.makedirs(output_dir, exist_ok=True)
    output_path = os.path.join(output_dir, filename)

    G = nx.Graph()
    
    # Añadir nodos
    for node, (x, y) in coords.items():
        G.add_node(node, pos=(x, y))
    
    # Añadir aristas con peso (distancia euclidiana)
    nodes = list(coords.keys())
    for i in range(len(nodes)):
        for j in range(i+1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            x1, y1 = coords[n1]
            x2, y2 = coords[n2]
            dist = np.sqrt((x2 - x1)**2 + (y2 - y1)**2)
            G.add_edge(n1, n2, weight=dist)
    
    # Dibujar el grafo
    pos = nx.get_node_attributes(G, 'pos')
    plt.figure(figsize=(8,6))
    nx.draw(G, pos, with_labels=True, node_size=500, node_color='lightblue')
    
    # Mostrar pesos de aristas (redondeados a 1 decimal)
    edge_labels = nx.get_edge_attributes(G, 'weight')
    edge_labels_rounded = {k: f"{v:.1f}" for k,v in edge_labels.items()}
    nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels_rounded)
    
    plt.title(f"Grafo TSP: {filename} con pesos de arista (distancia euclidiana)")
    
    # Guardar imagen
    plt.savefig(output_path, dpi=300)
    print(f"✅ La gráfica se ha guardado en: '{output_path}'")

    # Mostrar grafo
    if show_plot:
        plt.show()
    else:
        plt.close()

# ===========================
# Configuración
# ===========================

ms = [10, 12, 14]     # valores de m
instances = [1]      # dos instancias por m

tsp_dir = "Your_route/z_VRP/VRP_cluster/graphs"
output_dir = "./graficas_tsp"

# ===========================
# Ejecutar lectura y dibujo
# ===========================

for m in ms:
    for k in instances:
        vrp_file = f"vrp_{m}_{k}.vrp"
        vrp_path = os.path.join(tsp_dir, vrp_file)

        if not os.path.exists(vrp_path):
            print(f"⚠️ No existe: {vrp_file}")
            continue

        print(f"📂 Procesando {vrp_file}")

        coords = read_tsp_file(vrp_path)

        draw_tsp_graph_to_dir(
            coords,
            output_dir,
            filename=f"grafo_vrp_{m}_{k}.png",
            show_plot=False
        )
