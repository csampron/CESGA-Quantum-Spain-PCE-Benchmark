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

def build_bpp_solution_from_expmap(node_exp_map, alpha, weights, Capacity, y_threshold=0.0):
    """
    Reconstruye la solución BPP usando x_ij y y_j relajados en (-1,1) directamente.
    - node_exp_map incluye N^2 x_ij + N y_j
    - Se filtran bins activos según y_threshold (en rango [-1,1])
    """

    N = len(weights)
    max_bins = N

    # Extraer valores de node_exp_map
    exp_values = np.array([node_exp_map[i] for i in range(N**2 + N)])

    # Valores relajados z ∈ (-1,1)
    z = np.tanh(alpha * exp_values)

    # x_ij y y_j (sin transformar a [0,1])
    x_vals = z[:N*N].reshape(N, N)
    y_vals = z[N*N:]

    # x_ij y y_j (transformados a [0,1])
    x_vals = np.int((z[:N*N].reshape(N, N)/2) + 0.5)
    y_vals = np.int((z[N*N:]/2) + 0.5)

    # -------------------------
    # 1) Filtrar bins activos según y_threshold
    # -------------------------
    active_bins = [j for j in range(max_bins) if y_vals[j] > y_threshold]

    # Caso extremo: ningún bin supera el threshold
    if len(active_bins) == 0:
        active_bins = [int(np.argmax(y_vals))]

    # Crear estructura para bins activos
    bins = {j: [] for j in active_bins}

    # -------------------------
    # 2) Asignar cada ítem al bin activo con mayor x_ij
    # -------------------------
    for i in range(N):
        j_best = max(active_bins, key=lambda j: x_vals[i, j])
        bins[j_best].append(i)

    # Limpiar bins vacíos
    bin_list = [bins[j] for j in sorted(bins.keys()) if len(bins[j]) > 0]

    # -------------------------
    # 3) Chequeo de factibilidad
    # -------------------------
    feasible = True
    violations = []
    for idx, b in enumerate(bin_list):
        total_weight = sum(int(weights[i]) for i in b)
        if total_weight > Capacity:
            feasible = False
            violations.append({
                "bin_index": idx,
                "total_weight": total_weight,
                "capacity": Capacity,
                "items": b
            })

    report = {"feasible": feasible, "violations": violations}

    return bin_list, report





def postprocess_bins(bins, pesos, Capacity):
    # Copia profunda para no alterar la original
    bins = [b[:] for b in bins]
    improved = True

    while improved:
        improved = False

        # Identificar bins con un solo ítem
        singleton_bins = [b for b in bins if len(b) == 1]

        for sb in singleton_bins:
            item = sb[0]
            weight_item = int(pesos[item])

            moved = False  # Para marcar si logramos moverlo legítimamente

            for b in bins:
                if b is sb:
                    continue

                current_weight = sum(int(pesos[i]) for i in b)

                # Verificar capacidad ANTES de mover
                if current_weight + weight_item <= Capacity:
                    # --- Movimiento seguro ---
                    b.append(item)
                    bins.remove(sb)
                    improved = True
                    moved = True
                    break

            # Si este singleton no pudo moverse, seguimos al siguiente
            if improved:
                break

    # ----- Chequeo final de factibilidad -----
    feasible = True
    violations = []

    for idx, b in enumerate(bins):
        total_weight = sum(int(pesos[i]) for i in b)
        if total_weight > Capacity:
            feasible = False
            violations.append({
                "bin_index": idx,
                "total_weight": total_weight,
                "capacity": Capacity,
                "items": b,
                "weights": [pesos[i] for i in b]
            })
            print(f"⚠️ Postprocesado: Bin {idx} excede la capacidad! Peso total: {total_weight}, Capacidad: {Capacity}")

    report = {"feasible": feasible, "violations": violations}
    return bins, report
