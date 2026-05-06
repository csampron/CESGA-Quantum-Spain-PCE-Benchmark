### ========================================================= ###
### Módulo: Quantum Graph Encoding & Local Refinement
### ========================================================= ###
###
### Este módulo proporciona funciones para:
### 1. Calcular el número de qubits necesarios para un problema PCE.
### 2. Resolver ecuaciones cuadráticas o generales de combinatoria para el mapeo de variables.
### 3. Construir codificaciones de Hamiltonianos mediante operadores de Pauli correlacionados.
### 4. Generar particiones iniciales a partir de mapas de expectativas (exp_map).
### 5. Refinamiento local de particiones para mejorar el tamaño del corte (max-cut).
###
### ========================================================= ###

from typing import Tuple
import math
from itertools import combinations
from qiskit.quantum_info import SparsePauliOp
from .op_graph import calc_cut_size


def num_qubits(num_variables, order_compression):
    """
    Calcula el número de qubits necesarios para un problema dado
    según el número de variables y el orden de compresión PCE.

    Parámetros:
    -----------
    num_variables : int
        Número de variables del problema (por ejemplo, número de nodos en un grafo)
    order_compression : int
        Orden de compresión de PCE (por ejemplo 2 para cuadrático)

    Retorna:
    --------
    int
        Número de qubits requeridos
    """
    if order_compression == 2:
        # Para el caso cuadrático se resuelve una ecuación cuadrática
        qubits = math.ceil(max(solve_quadratic(1, -1, -2 / 3 * num_variables)))
    else:
        # Para orden mayor se usa un método general
        qubits = math.ceil(solve_for_k(num_variables, order_compression))
    return qubits


def solve_quadratic(a: float, b: float, c: float) -> Tuple[float, float]:
    """
    Resuelve la ecuación cuadrática a*x^2 + b*x + c = 0.

    Retorna:
    --------
    tuple
        Las dos soluciones (reales o complejas)
    """
    discriminant = b ** 2 - 4 * a * c
    if discriminant >= 0:
        x_1 = (-b + math.sqrt(discriminant)) / (2 * a)
        x_2 = (-b - math.sqrt(discriminant)) / (2 * a)
    else:
        x_1 = complex((-b / (2 * a)), math.sqrt(-discriminant) / (2 * a))
        x_2 = complex((-b / (2 * a)), -math.sqrt(-discriminant) / (2 * a))
    return x_1, x_2


def solve_for_k(m: float, k: int, max_n: int = 100, tol: float = 1e-6):
    """
    Resuelve m = 3 * comb(n, k) para n, dado k y m.
    Permite valores reales de n usando la función gamma para
    extender factorial a números no enteros.

    Parámetros:
    -----------
    m : float
        Número de términos (por ejemplo, número de combinaciones ponderadas)
    k : int
        Orden del operador
    max_n : int
        Límite superior inicial para la búsqueda
    tol : float
        Tolerancia para la búsqueda numérica

    Retorna:
    --------
    float o None
        Valor de n que satisface la ecuación o None si no se encuentra
    """
    def comb_continuous(n, k):
        return math.gamma(n + 1) / (math.gamma(k + 1) * math.gamma(n - k + 1))
    
    def f(n):
        return 3 * comb_continuous(n, k) - m
    
    # Búsqueda del intervalo inicial
    a, b = k, max_n
    if f(a) > 0:
        return None
    
    while f(b) < 0 and b < 1e6:
        b *= 2  # ampliar el intervalo si es necesario
    
    # Búsqueda binaria
    for _ in range(100):
        mid = (a + b) / 2
        if abs(f(mid)) < tol:
            return mid
        if f(mid) < 0:
            a = mid
        else:
            b = mid
    return (a + b) / 2


### ========================================================= ###
### FUNCIONES DE CODIFICACIÓN DE HAMILTONIANOS
### ========================================================= ###

def build_pauli_correlation_encoding(pauli, node_list, n, k):
    """
    Construye una lista de operadores de Pauli correlacionados 
    (Pauli correlation encoding) para un Hamiltoniano.

    Parámetros:
    -----------
    pauli : str
        Operador de Pauli a usar ('X', 'Y' o 'Z').
    node_list : list
        Lista de nodos (índices o pares) que determinan cuántos términos generar.
    n : int
        Número total de qubits.
    k : int
        Tamaño de las combinaciones de qubits a correlacionar.

    Retorna:
    --------
    list[SparsePauliOp]
        Lista de operadores de Pauli dispersos, cada uno representando un término del Hamiltoniano.
    """
    pauli_correlation_encoding = []

    for idx, c in enumerate(combinations(range(n), k)):
        if idx >= len(node_list):
            break
        paulis = ["I"] * n
        paulis[c[0]], paulis[c[1]] = pauli, pauli
        pauli_correlation_encoding.append(("".join(paulis)[::-1], 1))

    hamiltonian = [SparsePauliOp.from_list([(pauli, weight)]) 
                   for pauli, weight in pauli_correlation_encoding]
    return hamiltonian


### ========================================================= ###
### FUNCIONES DE PARTICIÓN Y REFINAMIENTO LOCAL
### ========================================================= ###

import numpy as np

def get_tsp_tour_from_expmap_org(node_exp_map, graph, alpha, allow_repeats=False):
    """
    Reconstruye un tour a partir de un exp_map relajado.

    Parameters
    ----------
    node_exp_map : dict[int, float] o np.ndarray
        Diccionario o array linealizado de variables x_ij relajadas.
    graph : nx.Graph
        Grafo completo con nodos 1..n.
    alpha : float
        Escala de la relajación tanh.
    allow_repeats : bool, default False
        - True  -> permite que algunas ciudades se repitan (tour relajado)
        - False -> fuerza un tour factible (cada ciudad una sola vez)

    Returns
    -------
    tour : list[int]
        Lista de nodos del tour (1-index, compatible con NetworkX).
    dist : float
        Distancia total del tour.
    x_values : dict[int, list[float]]
        Diccionario {nodo_real: [x_ij por posición j]}.

    Raises
    ------
    ValueError
        Si se detectan nodos repetidos y allow_repeats=False.
    """
    nodes_list = list(graph.nodes())
    m = len(nodes_list)

    # Convertir dict -> array lineal
    if isinstance(node_exp_map, dict):
        exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    else:
        exp_array = np.array(node_exp_map)

    # Variables relajadas x_ij en [-1,1] -> [0,1]
    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    def idx_ij(i, j):
        return i * m + j

    # Construcción del tour
    tour = []
    if allow_repeats:
        # Tour relajado: pueden repetirse nodos
        for j in range(m):
            best_i = np.argmax([x_relaxed[idx_ij(i, j)] for i in range(m)])
            tour.append(nodes_list[best_i])

        # Verificación: self-loops
        if len(set(tour)) < len(tour):
            repeated = [x for x in tour if tour.count(x) > 1]
            print(f"WARNING: Tour relajado con nodos repetidos {repeated}")

    else:
        # Tour factible: cada ciudad aparece una sola vez
        assigned_cities = set()
        for j in range(m):
            available = [i for i in range(m) if nodes_list[i] not in assigned_cities]
            best_i = max(available, key=lambda i: x_relaxed[idx_ij(i, j)])
            tour.append(nodes_list[best_i])
            assigned_cities.add(nodes_list[best_i])

        # Seguridad adicional
        if len(set(tour)) < len(tour):
            repeated = [x for x in tour if tour.count(x) > 1]
            raise ValueError(f"Tour no factible generado: nodos repetidos {repeated}")

    # Calcular distancia total
    dist = 0
    for j in range(m):
        c1 = tour[j]
        c2 = tour[(j + 1) % m]
        dist += graph[c1][c2]["weight"]

    # Valores de x_ij por nodo real
    x_values = {nodes_list[i]: [x_relaxed[idx_ij(i, j)] for j in range(m)] for i in range(m)}

    return tour, dist, x_values


def get_tsp_tour_from_expmap(node_exp_map, graph, alpha, allow_repeats=False):
    import numpy as np

    nodes_list = list(graph.nodes())
    m = len(nodes_list)

    # Convertir dict -> array
    if isinstance(node_exp_map, dict):
        exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    else:
        exp_array = np.array(node_exp_map)

    # Variables relajadas x_ij en [0,1]
    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    def idx_ij(i, j):
        return i * m + j

    depot = 1
    depot_idx = nodes_list.index(depot)

    tour = []

    if allow_repeats:
        # --- sin cambios ---
        for j in range(m):
            best_i = np.argmax([x_relaxed[idx_ij(i, j)] for i in range(m)])
            tour.append(nodes_list[best_i])

    else:
        assigned_cities = set()

        # 🔒 1️⃣ Forzar depot en la primera posición
        tour.append(depot)
        assigned_cities.add(depot)

        # 2️⃣ Resto de posiciones
        for j in range(1, m):
            available = [
                i for i in range(m)
                if nodes_list[i] not in assigned_cities
            ]
            best_i = max(available, key=lambda i: x_relaxed[idx_ij(i, j)])
            chosen = nodes_list[best_i]

            tour.append(chosen)
            assigned_cities.add(chosen)

        # Seguridad
        if len(set(tour)) < len(tour):
            repeated = [x for x in tour if tour.count(x) > 1]
            raise ValueError(f"Tour no factible generado: nodos repetidos {repeated}")

    # Calcular distancia (ciclo TSP)
    dist = 0
    for j in range(m):
        c1 = tour[j]
        c2 = tour[(j + 1) % m]
        dist += graph[c1][c2]["weight"]

    x_values = {
        nodes_list[i]: [x_relaxed[idx_ij(i, j)] for j in range(m)]
        for i in range(m)
    }

    return tour, dist, x_values


        
def two_opt_refinement(tour, graph):
    improved = True
    n = len(tour)
    best_tour = tour[:]

    def length(t):
        return sum(graph[t[i]][t[(i+1)%n]]["weight"] for i in range(n))

    best_len = length(best_tour)

    while improved:
        improved = False
        for i in range(n-2):
            for j in range(i+2, n):
                if j == n-1 and i == 0:
                    continue
                new_tour = best_tour[:]
                new_tour[i+1:j+1] = reversed(best_tour[i+1:j+1])
                new_len = length(new_tour)
                if new_len < best_len:
                    best_len = new_len
                    best_tour = new_tour
                    improved = True

    return best_tour, best_len

