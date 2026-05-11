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


def get_vrp_candidate_routes(
    node_exp_map,
    graph,
    alpha,
    A=2,
    threshold=0.45
):
    """
    Extrae TODOS los ciclos cerrados alcanzables desde el depot
    a partir de las variables binarias x_{aij}.

    NO selecciona solución VRP final.
    NO repara.
    NO fuerza factibilidad.
    """

    import numpy as np

    # =========================================================
    # 1. Parámetros
    # =========================================================

    n_nodes = graph.number_of_nodes()
    depot = 0

    # =========================================================
    # 2. Flatten
    # =========================================================

    if isinstance(node_exp_map, dict):

        exp_array = np.array(
            [node_exp_map[i] for i in range(len(node_exp_map))]
        )

    else:

        exp_array = np.array(node_exp_map)

    # =========================================================
    # 3. Relaxed variables
    # =========================================================

    z_relaxed = np.tanh(alpha * exp_array)

    x_relaxed = (z_relaxed + 1.0) / 2.0

    # =========================================================
    # 4. Compact indexing
    # =========================================================

    def idx_aij(a, i, j):

        if i == j:
            raise ValueError("Self-loops no permitidos")

        offset = j if j < i else j - 1

        return (
            a * (n_nodes * (n_nodes - 1))
            + i * (n_nodes - 1)
            + offset
        )

    # =========================================================
    # 5. Binary graph
    # =========================================================

    adjacency = {a: {} for a in range(A)}

    x_binary = {}

    for a in range(A):

        adjacency[a] = {i: [] for i in range(n_nodes)}

        for i in range(n_nodes):

            for j in range(n_nodes):

                if i == j:
                    continue

                value = x_relaxed[idx_aij(a, i, j)]

                binary = int(value >= threshold)

                x_binary[(a, i, j)] = binary

                if binary == 1:

                    adjacency[a][i].append(j)

    # =========================================================
    # 6. DFS extraction of ALL depot cycles
    # =========================================================

    candidate_routes = {}

    for a in range(A):

        routes_a = []

        def dfs(current, path, visited):

            # --------------------------------------------
            # ciclo válido
            # --------------------------------------------

            if len(path) > 1 and current == depot:

                routes_a.append(path[:])
                return

            # --------------------------------------------
            # explorar vecinos
            # --------------------------------------------

            for nxt in adjacency[a][current]:

                # volver al depot permitido
                if nxt == depot:

                    dfs(
                        depot,
                        path + [depot],
                        visited
                    )

                # evitar ciclos internos
                elif nxt not in visited:

                    dfs(
                        nxt,
                        path + [nxt],
                        visited | {nxt}
                    )

        # empezar desde depot
        dfs(
            depot,
            [depot],
            {depot}
        )

        # eliminar [0,0]
        routes_a = [
            r for r in routes_a
            if len(r) > 2
        ]

        candidate_routes[a] = routes_a

    # =========================================================
    # 7. Debug info
    # =========================================================

    x_values = {
        f"x_{a}_{i}_{j}": float(
            x_relaxed[idx_aij(a, i, j)]
        )
        for a in range(A)
        for i in range(n_nodes)
        for j in range(n_nodes)
        if i != j
    }

    return candidate_routes, x_values


def route_load(route, depot=0):
    """
    Como todos los nodos tienen demanda 1,
    la carga es simplemente el número
    de clientes visitados.
    """
    return len([n for n in route if n != depot])


def build_vrp_solution_from_candidates(
    candidate_routes,
    G,
    vehicle_capacity,
    A=2
):
    """
    Selecciona una combinación de rutas candidatas
    maximizando cobertura sin solapamiento
    y respetando capacidad.

    Suposiciones:
    - todos los clientes tienen demanda = 1
    - todos los vehículos tienen la misma capacidad
    - el depósito es el nodo 0
    """

    all_nodes = set(G.nodes())

    depot = 0

    # clientes reales
    customer_nodes = all_nodes - {depot}

    used = set()

    solution = {}

    total_cost = 0.0

    for a in range(A):

        best_route = None
        best_score = -1e18

        for route in candidate_routes.get(a, []):

            # clientes de la ruta
            customers = set(route) - {depot}

            # -------------------------
            # CHECK CAPACITY
            # -------------------------
            load = route_load(route, depot)

            if load > vehicle_capacity:
                continue

            # -------------------------
            # evitar solapamiento
            # -------------------------
            overlap = len(customers & used)

            if overlap > 0:
                continue

            # -------------------------
            # nueva cobertura
            # -------------------------
            new_nodes = len(customers - used)

            # -------------------------
            # coste de ruta
            # -------------------------
            cost = 0.0

            for i in range(len(route) - 1):

                u = route[i]
                v = route[i + 1]

                if G.has_edge(u, v):
                    cost += G[u][v]["weight"]

            # -------------------------
            # score heurístico
            # -------------------------
            score = new_nodes - 0.001 * cost

            if score > best_score:
                best_score = score
                best_route = route

        # -------------------------
        # asignar mejor ruta
        # -------------------------
        if best_route is None:

            solution[a] = [depot]

        else:

            solution[a] = best_route

            customers = set(best_route) - {depot}

            used |= customers

            # coste acumulado
            for i in range(len(best_route) - 1):

                u = best_route[i]
                v = best_route[i + 1]

                if G.has_edge(u, v):
                    total_cost += G[u][v]["weight"]

    # -------------------------
    # FACTIBILIDAD GLOBAL
    # -------------------------
    feasible = (used >= customer_nodes)

    return solution, total_cost, feasible



def vrp_postprocess(routes, G):
    """
    Limpia rutas:
    - elimina duplicados consecutivos
    - asegura inicio/fin en depósito
    """
    depot = 0
    clean_routes = {}

    for a, route in routes.items():
        cleaned = [route[0]]

        for v in route[1:]:
            if v != cleaned[-1]:
                cleaned.append(v)

        if cleaned[-1] != depot:
            cleaned.append(depot)

        clean_routes[a] = cleaned

    return clean_routes


def two_opt_route(route, G):
    """
    2-opt robusto para una ruta VRP.
    """

    if len(route) <= 3:
        # 0->i->0 no mejora
        return route, sum(
            G[route[i]][route[i+1]]["weight"]
            for i in range(len(route)-1)
            if route[i] != route[i+1]
        )

    best_route = route[:]
    n = len(route)

    def route_length(r):
        total = 0.0
        for i in range(len(r)-1):
            u, v = r[i], r[i+1]
            if u != v:
                total += G[u][v]["weight"]
        return total

    best_len = route_length(best_route)
    improved = True

    while improved:
        improved = False
        for i in range(1, n-2):
            for j in range(i+1, n-1):
                new_route = best_route[:]
                new_route[i:j+1] = reversed(best_route[i:j+1])

                new_len = route_length(new_route)

                if new_len < best_len:
                    best_route = new_route
                    best_len = new_len
                    improved = True

    return best_route, best_len

def refine_vrp_routes(routes, G):
    """
    Aplica 2-opt a todas las rutas.
    """
    refined_routes = {}
    total_cost = 0.0

    for a, route in routes.items():
        r, c = two_opt_route(route, G)
        refined_routes[a] = r
        total_cost += c

    return refined_routes, total_cost