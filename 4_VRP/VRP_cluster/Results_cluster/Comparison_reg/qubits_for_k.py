#!/usr/bin/env python3
import os
import math
import matplotlib.pyplot as plt
from typing import Tuple

# ------------------------------------------------
#  Funciones matemáticas
# ------------------------------------------------

def solve_quadratic(a: float, b: float, c: float) -> Tuple[float, float]:
    disc = b**2 - 4*a*c
    if disc >= 0:
        x1 = (-b + math.sqrt(disc)) / (2*a)
        x2 = (-b - math.sqrt(disc)) / (2*a)
    else:
        real = -b / (2*a)
        imag = math.sqrt(-disc) / (2*a)
        x1 = complex(real, imag)
        x2 = complex(real, -imag)
    return x1, x2

def solve_for_k(m: float, k: int, max_n: int = 100, tol: float = 1e-6):
    def comb_continuous(n, k):
        return math.gamma(n + 1) / (math.gamma(k + 1) * math.gamma(n - k + 1))
    def f(n):
        return 3 * comb_continuous(n, k) - m
    a, b = k, max_n
    if f(a) > 0:
        return None
    while f(b) < 0 and b < 1e6:
        b *= 2
    for _ in range(100):
        mid = (a + b) / 2
        if abs(f(mid)) < tol:
            return mid
        if f(mid) < 0:
            a = mid
        else:
            b = mid
    return (a + b) / 2

def num_qubits(num_variables, order_compression):
    if order_compression == 2:
        qubits = math.ceil(max(solve_quadratic(1, -1, -2 / 3 * num_variables)))
    else:
        qubits = math.ceil(solve_for_k(num_variables, order_compression))
    return qubits

# ------------------------------------------------
#  Parámetros
# ------------------------------------------------

num_variables = [3, 4, 5, 6]
order_compression_sets = [
    [1, 2, 3, 4, 5],
    [2, 3, 4, 5]
]

# Colores fijos para k=2,3,4,5
COLOR_K = {
    2: "steelblue",
    3: "seagreen",
    4: "crimson",
    5: "darkorange"
}

output_dir = "Your_route/z_VRP/A_DIFFERENTIAL_COMPARISON"
os.makedirs(output_dir, exist_ok=True)

# ------------------------------------------------
#  Calcular resultados
# ------------------------------------------------

results = {k: [num_qubits(n**2, k) for n in num_variables] for k in range(1,6)}

# ------------------------------------------------
#  Generar gráficas
# ------------------------------------------------
for idx, order_compression in enumerate(order_compression_sets, start=1):
    plt.figure(figsize=(8,6))
    for k in order_compression:
        if k not in results:
            continue
        plt.plot(
            num_variables,
            results[k],
            marker="o",
            label=f"order={k}",
            color=COLOR_K.get(k, "gray")
        )
    plt.xlabel("num_variables")
    plt.ylabel("qubits resultantes")
    plt.title(f"Número de qubits para distintos órdenes de compresión (figura {idx})")
    plt.grid(True)
    plt.legend()
    filepath = os.path.join(output_dir, f"Evolucion_cubits_VRP_fig{idx}.png")
    plt.savefig(filepath, dpi=300)
    plt.close()
    print(f"Imagen guardada en: {filepath}")
