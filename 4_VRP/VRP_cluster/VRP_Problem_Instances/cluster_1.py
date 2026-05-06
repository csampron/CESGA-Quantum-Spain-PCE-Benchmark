import networkx as nx
import math
import os

def load_graph(path):
    """
    Lee un archivo CVRP en formato TSPLIB (EUC_2D),
    asumiendo:
    - demanda = 1 por cliente
    - vehículos ilimitados
    - nodo 1 es el depot (hangar)

    Devuelve:
    G         : grafo completo ponderado (networkx)
    n_nodes   : número total de nodos
    depot     : nodo depot
    capacity  : capacidad del vehículo
    demand    : dict nodo -> demanda
    """

    coords = {}
    capacity = None

    with open(path, "r") as f:
        lines = f.readlines()

    # --------------------------------------------------
    # Leer CAPACITY
    # --------------------------------------------------
    for line in lines:
        if line.strip().startswith("CAPACITY"):
            capacity = int(line.split(":")[1].strip())
            break

    if capacity is None:
        raise ValueError("No se encontró CAPACITY en el archivo VRP.")

    # --------------------------------------------------
    # Leer coordenadas
    # --------------------------------------------------
    start = None
    for i, line in enumerate(lines):
        if line.strip().startswith("NODE_COORD_SECTION"):
            start = i + 1
            break

    if start is None:
        raise ValueError("No se encontró NODE_COORD_SECTION.")

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

    # --------------------------------------------------
    # Construir grafo completo
    # --------------------------------------------------
    G = nx.Graph()

    for node, (x, y) in coords.items():
        G.add_node(node, pos=(x, y))

    nodes = list(coords.keys())
    for i in range(len(nodes)):
        for j in range(i + 1, len(nodes)):
            n1, n2 = nodes[i], nodes[j]
            x1, y1 = coords[n1]
            x2, y2 = coords[n2]
            dist = int(math.sqrt((x1 - x2)**2 + (y1 - y2)**2))
            G.add_edge(n1, n2, weight=dist)

    # --------------------------------------------------
    # Demanda (1 por cliente, 0 en depot)
    # --------------------------------------------------
    depot = 1
    demand = {node: (0 if node == depot else 1) for node in nodes}

    return G, len(nodes), depot, capacity, demand





# -----------------------------
# Funciones auxiliares básicas
# -----------------------------

def euclidean(p1, p2):
    """
    Calcula la distancia euclídea entre dos puntos (x, y).
    Esto se usa para:
    - Encontrar el nodo más lejano del depot (seed)
    - Encontrar el nodo más cercano al centro geométrico (GC)
    """
    return math.sqrt((p1[0] - p2[0])**2 + (p1[1] - p2[1])**2)


def geometric_center(G, nodes):
    """
    Calcula el centro geométrico (promedio de coordenadas) de un conjunto de nodos.
    Se recalcula cada vez que se añade o mueve un nodo.
    GC guía la selección del siguiente nodo a añadir a un cluster.
    """
    xs, ys = 0.0, 0.0
    for v in nodes:
        x, y = G.nodes[v]["pos"]
        xs += x
        ys += y
    return (xs / len(nodes), ys / len(nodes))


def farthest_from_depot(G, depot, candidates):
    """
    Devuelve el nodo más lejano al depot dentro de los nodos candidatos.
    Este nodo será el seed inicial de un nuevo cluster.
    """
    depot_pos = G.nodes[depot]["pos"]
    return max(
        candidates,
        key=lambda v: euclidean(G.nodes[v]["pos"], depot_pos)
    )


def closest_to_point(G, point, candidates):
    """
    Devuelve el nodo candidato más cercano a un punto dado (normalmente el GC).
    Este nodo será considerado para añadirse al cluster actual.
    """
    return min(
        candidates,
        key=lambda v: euclidean(G.nodes[v]["pos"], point)
    )

# -----------------------------
# Fase 1: Cluster Construction
# -----------------------------

def cluster_construction(G, depot, capacity, demand):
    """
    Construye clusters iniciales siguiendo la lógica de Shin & Han:
    1. Selecciona el nodo más lejano al depot como seed.
    2. Crea un cluster e inicia la capacidad disponible.
    3. Añade nodos no clusterizados más cercanos al centro geométrico (GC)
       hasta que no quepa ninguno más.
    4. Repite hasta que todos los nodos estén asignados.
    
    Devuelve una lista de clusters, cada uno con:
    - 'nodes': lista de nodos
    - 'capacity_left': capacidad restante del vehículo
    """
    unvisited = set(G.nodes)
    unvisited.remove(depot)  # Depot no se clusteriza

    clusters = []

    while unvisited:
        # 1️⃣ Seleccionamos el seed (más lejano al depot)
        seed = farthest_from_depot(G, depot, unvisited)

        # 2️⃣ Creamos el cluster y actualizamos capacidad
        cluster = []
        remaining_capacity = capacity

        cluster.append(seed)
        remaining_capacity -= demand[seed]
        unvisited.remove(seed)

        # 3️⃣ Calculamos el centro geométrico inicial
        GC = geometric_center(G, cluster)

        # 4️⃣ Añadimos nodos cercanos al GC hasta llenar capacidad
        while unvisited:
            v = closest_to_point(G, GC, unvisited)

            if demand[v] <= remaining_capacity:
                cluster.append(v)
                remaining_capacity -= demand[v]
                unvisited.remove(v)
                GC = geometric_center(G, cluster)  # Recalcular GC
            else:
                break

        # 5️⃣ Guardamos el cluster creado
        clusters.append({
            "nodes": cluster,
            "capacity_left": remaining_capacity
        })

    return clusters

# -----------------------------
# Fase 2: Cluster Adjustment
# -----------------------------

def cluster_adjustment(G, clusters, demand):
    """
    Ajusta los clusters iniciales para mejorar compacidad:
    - Un nodo vk se mueve de su cluster original ci a otro cluster cj
      si:
        1. Está más cerca del GC de cj que del GC de ci
        2. Cabe en la capacidad restante de cj
    - Se recalculan los GC tras cada movimiento.
    
    Devuelve True si al menos un nodo fue movido.
    """
    moved = False

    # Precalcular centros geométricos
    GCs = [geometric_center(G, c["nodes"]) for c in clusters]

    # Revisar cada nodo de cada cluster
    for i, ci in enumerate(clusters):
        for vk in ci["nodes"][:]:  # Copia para poder modificar durante iteración
            for j, cj in enumerate(clusters):
                if i == j:
                    continue  # No comparar con su propio cluster

                # Verificar capacidad
                if demand[vk] > cj["capacity_left"]:
                    continue

                # Distancia al GC original vs GC candidato
                dist_i = euclidean(G.nodes[vk]["pos"], GCs[i])
                dist_j = euclidean(G.nodes[vk]["pos"], GCs[j])

                if dist_j < dist_i:
                    # ✅ Mover nodo
                    ci["nodes"].remove(vk)
                    ci["capacity_left"] += demand[vk]

                    cj["nodes"].append(vk)
                    cj["capacity_left"] -= demand[vk]

                    # Recalcular centros
                    GCs[i] = geometric_center(G, ci["nodes"])
                    GCs[j] = geometric_center(G, cj["nodes"])

                    moved = True
                    break  # Pasar al siguiente nodo

    return moved

# -----------------------------
# Función principal de clustering
# -----------------------------

def clustering_phase(G, depot, capacity, demand):
    """
    Combina cluster construction y cluster adjustment:
    1. Construye clusters iniciales
    2. Itera cluster_adjustment hasta convergencia
    3. Devuelve lista de clusters optimizados
    """
    # Construcción inicial
    clusters = cluster_construction(G, depot, capacity, demand)

    # Ajuste iterativo
    while True:
        moved = cluster_adjustment(G, clusters, demand)
        if not moved:
            break

    # Solo devolver las listas de nodos de cada cluster (sin capacidad)
    return [c["nodes"] for c in clusters]




def generate_cluster_tsp_files(G, clusters, instance_name, output_dir, depot=1):
    """
    Genera archivos .tsp para cada cluster de una instancia VRP.
    Incluye el depot en cada archivo para que el TSP sea válido.
    
    Parámetros:
    -----------
    G : networkx.Graph
        Grafo completo con coordenadas de todos los nodos.
    clusters : list[list[int]]
        Lista de clusters, cada uno es una lista de nodos (clientes).
    instance_name : str
        Nombre de la instancia VRP (ej. "vrp_4_1").
    output_dir : str
        Carpeta donde se guardarán los archivos TSP.
    depot : int
        Nodo que representa el depot (por defecto 1).
        
    Retorna:
    --------
    cluster_info : list[dict]
        Lista con información de cada cluster:
        - cluster_id
        - tsp_path
        - nodes (lista de nodos incluyendo el depot)
    """

    os.makedirs(output_dir, exist_ok=True)
    cluster_info = []

    for idx, cluster_nodes in enumerate(clusters):
        # ✅ Aseguramos que el depot está incluido
        tsp_nodes = [depot] + cluster_nodes

        tsp_path = os.path.join(
            output_dir,
            f"{instance_name}_cluster_{idx}.tsp"
        )

        # Escribir archivo TSP
        with open(tsp_path, "w") as f:
            f.write(f"NAME : {instance_name}_cluster_{idx}\n")
            f.write("TYPE : TSP\n")
            f.write(f"DIMENSION : {len(tsp_nodes)}\n")
            f.write("EDGE_WEIGHT_TYPE : EUC_2D\n")
            f.write("NODE_COORD_SECTION\n")

            for node in tsp_nodes:
                x, y = G.nodes[node]["pos"]
                f.write(f"{node} {x} {y}\n")

            f.write("EOF\n")

        # Guardar info estructurada del cluster
        cluster_info.append({
            "cluster_id": idx,
            "tsp_path": tsp_path,
            "nodes": tsp_nodes
        })

        print(f"   → Cluster {idx}: {len(tsp_nodes)} nodos (incluyendo depot)")

    return cluster_info




import os

def generate_all_cluster_tsps(
    vrp_dir,
    output_base_dir,
    sizes,
    instances=(1, 2)
):
    """
    Recorre todos los tamaños e instancias VRP,
    genera clusters y crea los archivos TSP correspondientes.

    vrp_dir         : carpeta donde están los .vrp
    output_base_dir : carpeta raíz para los TSP generados
    sizes           : iterable con tamaños (ej. range(4, 9))
    instances       : instancias por tamaño (default: (1, 2))
    """

    for n in sizes:
        for inst in instances:
            instance_name = f"vrp_{n}_{inst}"
            vrp_path = os.path.join(vrp_dir, f"{instance_name}.vrp")
            output_dir = os.path.join(output_base_dir, instance_name)

            print(f"\n🔹 Procesando {instance_name}")

            # 1️⃣ Cargar VRP
            G, _, depot, capacity, demand = load_graph(vrp_path)

            # 2️⃣ Clustering
            clusters = clustering_phase(G, depot, capacity, demand)

            print(f"   → {len(clusters)} clusters encontrados")

            # 3️⃣ Generar TSPs (uno por cluster, o un archivo conjunto)
            cluster_info = generate_cluster_tsp_files(
                G=G,
                clusters=clusters,
                instance_name=instance_name,
                output_dir=output_dir
            )

            print(f"   → TSPs generados en {output_dir}")

    print("\n✅ Generación completa")


generate_all_cluster_tsps(
    vrp_dir="/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/VRP_cluster/VARIOS/graphs",
    output_base_dir="/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_VRP/VRP_cluster/VARIOS/graphs_clusters",
    sizes=(4,5,6,7,8),   # de 4 a 8 nodos
    instances=(1,2)
)

