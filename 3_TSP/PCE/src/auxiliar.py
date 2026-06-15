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

def get_tsp_tour_from_expmap(
    node_exp_map,
    graph,
    alpha,
    threshold= (0.5 - 1e-6)
):
    import numpy as np

    # ============================================================
    # 1. Nodos
    # ============================================================

    nodes_list = list(graph.nodes())

    fixed_node = nodes_list[0]
    free_cities = [n for n in nodes_list if n != fixed_node]

    m = len(free_cities)
    node_to_idx = {n: i for i, n in enumerate(free_cities)}

    # ============================================================
    # 2. Embedding relajado
    # ============================================================

    if isinstance(node_exp_map, dict):
        exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    else:
        exp_array = np.array(node_exp_map)

    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    def idx_ij(i, j):
        return i * m + j

    # ============================================================
    # 3. matriz x_ij
    # ============================================================

    x_matrix = np.zeros((m, m))

    for i in range(m):
        for j in range(m):
            x_matrix[i, j] = x_relaxed[idx_ij(i, j)]

    x_values = {
        free_cities[i]: [x_matrix[i, j] for j in range(m)]
        for i in range(m)
    }

    # ============================================================
    # 4. binarización
    # ============================================================

    x_binary = (x_matrix >= threshold).astype(int)

    # ============================================================
    # 5. candidatos
    # ============================================================

    position_candidates = {}

    for j in range(m):
        position_candidates[j] = [
            free_cities[i]
            for i in range(m)
            if x_binary[i, j] == 1
        ]

    # ============================================================
    # 6. métricas estructurales
    # ============================================================

    node_occurrences = {n: 0 for n in free_cities}

    empty_positions = []
    ambiguous_positions = []
    missing_nodes = []
    duplicate_nodes = []

    for j in range(m):
        if len(position_candidates[j]) == 0:
            empty_positions.append(j)
        if len(position_candidates[j]) > 1:
            ambiguous_positions.append(j)

        for n in position_candidates[j]:
            node_occurrences[n] += 1

    for n, occ in node_occurrences.items():
        if occ == 0:
            missing_nodes.append(n)
        elif occ > 1:
            duplicate_nodes.append(n)

    initial_feasible = (
        len(empty_positions) == 0 and
        len(ambiguous_positions) == 0 and
        len(missing_nodes) == 0 and
        len(duplicate_nodes) == 0
    )

    # ============================================================
    # 7. reconstrucción
    # ============================================================

    initial_tour = [None] * m
    used_nodes = set()

    greedy_used = False

    # 7.1 asignaciones directas
    for j in range(m):
        if len(position_candidates[j]) == 1:
            node = position_candidates[j][0]
            initial_tour[j] = node
            used_nodes.add(node)

    # 7.2 greedy
    for j in range(m):

        if initial_tour[j] is not None:
            continue

        candidates = [
            n for n in position_candidates[j]
            if n not in used_nodes
        ]

        if len(candidates) == 0:
            return (
                None,
                None,
                "infeasible",
                {
                    "position_candidates": position_candidates,
                    "empty_positions": empty_positions,
                    "ambiguous_positions": ambiguous_positions,
                    "missing_nodes": missing_nodes,
                    "duplicate_nodes": duplicate_nodes
                },
                x_values
            )

        best_node = max(
            candidates,
            key=lambda n: x_matrix[node_to_idx[n], j]
        )

        initial_tour[j] = best_node
        used_nodes.add(best_node)

        greedy_used = True

    # ============================================================
    # 8. validación final
    # ============================================================

    if set(initial_tour) != set(free_cities):
        return (
            None,
            None,
            "infeasible",
            {
                "position_candidates": position_candidates,
                "empty_positions": empty_positions,
                "ambiguous_positions": ambiguous_positions,
                "missing_nodes": missing_nodes,
                "duplicate_nodes": duplicate_nodes
            },
            x_values
        )

    # ============================================================
    # 9. tour completo
    # ============================================================

    full_tour = [fixed_node] + initial_tour + [fixed_node]

    dist = 0.0
    for i in range(len(full_tour) - 1):
        c1 = full_tour[i]
        c2 = full_tour[i + 1]
        dist += graph[c1][c2]["weight"]

    # ============================================================
    # 10. status final
    # ============================================================

    if initial_feasible:
        status = "perfect"
    elif greedy_used:
        status = "greedy"
    else:
        status = "infeasible"

    # ============================================================
    # 11. output
    # ============================================================

    candidate_info = {
        "position_candidates": position_candidates,
        "empty_positions": empty_positions,
        "ambiguous_positions": ambiguous_positions,
        "missing_nodes": missing_nodes,
        "duplicate_nodes": duplicate_nodes
    }

    return (
        full_tour,
        dist,
        status,
        candidate_info,
        x_values
    )


        
def two_opt_refinement(tour, graph):

    # ---------------------------------------------------------
    # FIX 1: eliminar duplicado final si existe
    # ---------------------------------------------------------
    if tour[0] == tour[-1]:
        tour = tour[:-1]

    fixed = tour[0]
    subtour = tour[1:]

    n = len(tour)

    best_tour = tour[:]

    def length(t):

        for node in t:
            if node not in graph:
                raise ValueError(f"Node {node} not in graph: {node}")

        return sum(
            graph[t[i]][t[(i+1) % len(t)]]["weight"]
            for i in range(len(t))
        )

    best_len = length(best_tour)

    improved = True

    while improved:
        improved = False

        for i in range(1, n-2):          # no tocar fixed node
            for j in range(i+1, n-1):

                new_tour = best_tour[:]
                new_tour[i:j] = reversed(new_tour[i:j])

                new_len = length(new_tour)

                if new_len < best_len:
                    best_tour = new_tour
                    best_len = new_len
                    improved = True

    return best_tour, best_len


