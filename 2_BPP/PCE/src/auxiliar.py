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

import math
import numpy as np

from typing import Tuple
from itertools import combinations
from qiskit.quantum_info import SparsePauliOp


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
### FUNCIONES DE PARTICIÓN Y REFINAMIENTO LOCAL
### ========================================================= ###

from itertools import product
import numpy as np


def build_bpp_solution_from_expmap(
    node_exp_map,
    alpha,
    weights,
    Capacity,
    threshold=0.5
):
    N = len(weights)
    max_bins = N

    # ============================================================
    # 1. Reconstruir matriz x_ij desde exp_map
    # ============================================================

    if isinstance(node_exp_map, dict):
        exp_array = np.array(
            [node_exp_map[i] for i in range(N * max_bins)],
            dtype=float
        )
    else:
        exp_array = np.asarray(node_exp_map[:N * max_bins], dtype=float)

    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    x_matrix = x_relaxed.reshape(N, max_bins)
    x_binary = (x_matrix >= threshold).astype(int)

    # ============================================================
    # 2. Candidatos por objeto
    # ============================================================

    item_candidates = {
        i: [j for j in range(max_bins) if x_binary[i, j] == 1]
        for i in range(N)
    }

    unassigned_items = [
        i for i, cand in item_candidates.items()
        if len(cand) == 0
    ]

    ambiguous_items = [
        i for i, cand in item_candidates.items()
        if len(cand) > 1
    ]

    x_values = {
        i: [float(x_matrix[i, j]) for j in range(max_bins)]
        for i in range(N)
    }

    x_binary_values = {
        i: [int(x_binary[i, j]) for j in range(max_bins)]
        for i in range(N)
    }

    candidate_info = {
        "item_candidates": item_candidates,
        "unassigned_items": unassigned_items,
        "ambiguous_items": ambiguous_items,
        "x_binary": x_binary_values
    }

    # ============================================================
    # 3. Si algún objeto no tiene candidato, la solución no existe
    # ============================================================

    if len(unassigned_items) > 0:
        report = {
            "feasible": False,
            "assignment_feasible": False,
            "capacity_feasible": False,
            "reason": "items_without_candidate_bins",
            "num_combinations": 0,
            "feasible_solutions": 0,
            "unassigned_items": unassigned_items,
            "ambiguous_items": ambiguous_items,
            "violations": []
        }

        return None, report, "infeasible", candidate_info, x_values

    # ============================================================
    # 4. Número de combinaciones compatibles con la binarización
    # ============================================================

    num_combinations = 1
    for i in range(N):
        num_combinations *= len(item_candidates[i])

    # ============================================================
    # 5. Enumerar todas las combinaciones candidatas
    # ============================================================

    candidate_lists = [item_candidates[i] for i in range(N)]

    best_bins = None
    best_assignment = None
    best_score = None
    feasible_solutions = 0
    best_violations = None

    for assignment_tuple in product(*candidate_lists):
        bins_dict = {j: [] for j in range(max_bins)}

        for i, j in enumerate(assignment_tuple):
            bins_dict[j].append(i)

        bin_list = [
            bins_dict[j]
            for j in range(max_bins)
            if len(bins_dict[j]) > 0
        ]

        # --------------------------------------------------------
        # Validar capacidad
        # --------------------------------------------------------

        capacity_feasible = True
        violations = []

        for idx, b in enumerate(bin_list):
            total_weight = sum(int(weights[i]) for i in b)

            if total_weight > Capacity:
                capacity_feasible = False
                violations.append({
                    "bin_index": idx,
                    "total_weight": total_weight,
                    "capacity": Capacity,
                    "items": b,
                    "weights": [int(weights[i]) for i in b]
                })

        if not capacity_feasible:
            if best_violations is None:
                best_violations = violations
            continue

        feasible_solutions += 1

        # --------------------------------------------------------
        # Criterio:
        # 1) menor número de bins
        # 2) mayor confianza del embedding
        # --------------------------------------------------------

        num_bins_used = len(bin_list)

        confidence = sum(
            x_matrix[i, assignment_tuple[i]]
            for i in range(N)
        )

        score = (
            num_bins_used,
            -confidence
        )

        if best_score is None or score < best_score:
            best_score = score
            best_bins = bin_list
            best_assignment = assignment_tuple

    # ============================================================
    # 6. Ninguna combinación fue factible
    # ============================================================

    if best_bins is None:

        reconstruction_info = {
            "num_combinations": num_combinations,
            "feasible_solutions": feasible_solutions,
            "unassigned_items": unassigned_items,
            "ambiguous_items": ambiguous_items,
            "selected_assignment": None,
            "num_bins_used": None
        }

        return (
            None,
            reconstruction_info,
            "infeasible",
            candidate_info,
            x_values
        )

    # ============================================================
    # 7. Status final
    # ============================================================

    if len(ambiguous_items) == 0:
        status = "perfect"
    else:
        status = "combinatorial"

    reconstruction_info = {
        "num_combinations": num_combinations,
        "feasible_solutions": feasible_solutions,
        "unassigned_items": unassigned_items,
        "ambiguous_items": ambiguous_items,
        "selected_assignment": list(best_assignment),
        "num_bins_used": len(best_bins)
    }

    return (
        best_bins,
        reconstruction_info,
        status,
        candidate_info,
        x_values
    )



def postprocess_bins(bins, pesos, Capacity):
    """
    Postprocesado seguro:
    - Si bins is None, no hace nada.
    - Si bins existe, se asume que ya es factible.
    - Solo mueve singleton bins si el movimiento preserva capacidad.
    - Devuelve únicamente bins_post.
    """

    if bins is None:
        return None

    bins = [b[:] for b in bins]

    improved = True

    while improved:
        improved = False

        singleton_bins = [b for b in bins if len(b) == 1]

        for sb in singleton_bins:
            item = sb[0]
            weight_item = int(pesos[item])

            for b in bins:
                if b is sb:
                    continue

                current_weight = sum(int(pesos[i]) for i in b)

                if current_weight + weight_item <= Capacity:
                    b.append(item)
                    bins.remove(sb)
                    improved = True
                    break

            if improved:
                break

    return bins