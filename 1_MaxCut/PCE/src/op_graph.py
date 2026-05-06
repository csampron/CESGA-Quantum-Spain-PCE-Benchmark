### ========================================================= ###
### Módulo: op_graph
### ========================================================= ###
###
### Funciones para trabajar con grafos en el contexto de
### optimización cuántica (PCE + VQE).
###
### Funcionalidades:
### - calc_cut_size: calcula el tamaño del corte entre dos particiones
### - load_graph: carga un grafo desde un archivo de texto con pesos en aristas
###
### ========================================================= ###

import networkx as nx

def calc_cut_size(graph, partition0, partition1):
    """
    Calcula el tamaño del corte (cut size) de un grafo dado
    según dos particiones de sus nodos.

    Parámetros:
    -----------
    graph : networkx.Graph o networkx.MultiGraph
        Grafo cuyos cortes se van a calcular
    partition0 : list o set
        Lista de nodos pertenecientes a la primera partición
    partition1 : list o set
        Lista de nodos pertenecientes a la segunda partición

    Retorna:
    --------
    float
        Suma de los pesos de las aristas que cruzan entre particiones
    """
    cut_size = 0.0
    for edge0, edge1, data in graph.edges(data=True):
        if (edge0 in partition0 and edge1 in partition1) or \
           (edge0 in partition1 and edge1 in partition0):
            cut_size += data.get("weight", 1.0)
    return cut_size


def load_graph(nombre_archivo):
    """
    Carga un grafo desde un archivo de texto con el formato:
        n e
        u v peso

    Ejemplo de archivo:
        5 6
        0 1 1.0
        0 2 2.5
        ...

    Parámetros:
    -----------
    nombre_archivo : str
        Ruta al archivo que contiene la descripción del grafo

    Retorna:
    --------
    G : networkx.MultiGraph
        Grafo con pesos en las aristas
    n_i : int
        Número de nodos en el grafo
    """
    G = nx.MultiGraph()
    with open(nombre_archivo, 'r') as archivo:
        # Leer primera línea con número de nodos y aristas
        first_line = archivo.readline().strip().split()
        if len(first_line) < 2:
            raise ValueError("Formato inválido: la primera línea debe contener 'n e'.")

        n_i, e_i = map(int, first_line[:2])

        # Leer el resto de líneas (aristas)
        for linea in archivo:
            parts = linea.strip().split()
            if len(parts) < 2:
                continue  # Línea vacía o incorrecta
            u, v = int(parts[0]), int(parts[1])
            peso = float(parts[2]) if len(parts) > 2 else 1.0
            G.add_edge(u, v, weight=peso)

    return G, n_i
