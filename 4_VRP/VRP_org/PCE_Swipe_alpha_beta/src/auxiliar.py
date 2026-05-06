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
def get_vrp_routes_from_expmap_obj(node_exp_map, graph, alpha, A, max_clients_per_vehicle):

    import numpy as np

    n_nodes = graph.number_of_nodes()  # Número de nodos (incluyendo el depósito)
    depot = 0  # Nodo depósito
    n_steps = n_nodes + 1  # Número máximo de pasos en la ruta (incluye regreso al depósito)

    # -------------------------------------------------
    # 1. Flatten y relajación
    # -------------------------------------------------
    # node_exp_map puede ser dict o lista, se convierte en array de numpy
    if isinstance(node_exp_map, dict):
        exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    else:
        exp_array = np.array(node_exp_map)

    # Se aplica tanh(alpha * valor) para relajar y normalizar
    z_relaxed = np.tanh(alpha * exp_array)
    # Se escala de [-1,1] a [0,1] para obtener x_relaxed, que indica la "probabilidad" de usar esa arista/paso
    x_relaxed = (z_relaxed + 1.0) / 2.0

    # Función de índice lineal para acceder al vector aplanado: (vehículo, nodo, paso)
    def idx_avs(a, v, s):
        return a * (n_nodes * n_steps) + v * n_steps + s

    # -------------------------------------------------
    # 2. Detectar vehículos activos
    # -------------------------------------------------
    vehicle_active = {}
    for a in range(A):
        # Se revisa si el vehículo a empieza en el depósito o tiene actividad en otros nodos
        activation = x_relaxed[idx_avs(a, depot, 0)]
        activity_score = sum(x_relaxed[idx_avs(a, i, s)] 
                             for i in range(1, n_nodes) 
                             for s in range(n_steps))
        # Se considera activo si inicia en el depósito o tiene actividad significativa
        vehicle_active[a] = (activation > 0.5) or (activity_score > 1.0)

    # -------------------------------------------------
    # 3. Inicialización rutas activas
    # -------------------------------------------------
    # Creamos rutas vacías para vehículos activos, comenzando en el depósito
    routes = {a: [depot] for a in range(A) if vehicle_active[a]}
    # Inicializamos carga de clientes atendidos por vehículo
    load = {a: 0 for a in routes.keys()}
    # Conjunto de nodos ya asignados (empezando por depósito)
    assigned_nodes = set([depot])

    # -------------------------------------------------
    # 4. Asignación greedy
    # -------------------------------------------------
    # Iteramos por cada paso s
    for s in range(1, n_steps):
        candidates = []
        for a in routes.keys():
            if load[a] >= max_clients_per_vehicle:  # Capacidad máxima
                continue
            for v in range(1, n_nodes):  # Solo clientes (excluyendo depósito)
                if v not in assigned_nodes:
                    # Se agrega candidato: valor de x_relaxed para este paso, vehículo y nodo
                    candidates.append((x_relaxed[idx_avs(a, v, s)], a, v))
        if not candidates:
            break  # Si no hay más candidatos, terminamos

        # Ordenamos candidatos descendente por valor de x_relaxed (greedy)
        candidates.sort(reverse=True, key=lambda t: t[0])

        # Asignamos los clientes según orden greedy, respetando capacidad
        for _, a, v in candidates:
            if v in assigned_nodes or load[a] >= max_clients_per_vehicle:
                continue
            routes[a].append(v)
            load[a] += 1
            assigned_nodes.add(v)

        if len(assigned_nodes) == n_nodes:
            break  # Todos los nodos han sido asignados

    # -------------------------------------------------
    # 5. Cerrar rutas
    # -------------------------------------------------
    # Se agregan los depósitos al final de cada ruta si no están
    final_routes = {}
    for a, route in routes.items():
        if len(route) > 1:  # Solo rutas con al menos un cliente
            if route[-1] != depot:
                route.append(depot)
            final_routes[a] = route

    # -------------------------------------------------
    # 6. Coste total
    # -------------------------------------------------
    # Se calcula el coste total sumando pesos de aristas en cada ruta
    total_cost = 0.0
    for route in final_routes.values():
        for i in range(len(route) - 1):
            u, v = route[i], route[i + 1]
            if u != v:
                total_cost += graph[u][v]["weight"]

    # -------------------------------------------------
    # 7. Debug x_values
    # -------------------------------------------------
    # Guardamos valores de x_relaxed para cada nodo y vehículo por paso (para análisis/debug)
    x_values = {
        f"{a}_{v}": [float(x_relaxed[idx_avs(a, v, s)]) for s in range(n_steps)]
        for a in range(A)
        for v in range(n_nodes)
    }

    return final_routes, total_cost, x_values


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