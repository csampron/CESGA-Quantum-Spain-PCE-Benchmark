import os
import math
import matplotlib.pyplot as plt
from typing import Tuple, Optional

# ------------------------------------------------
#  Funciones matemáticas
# ------------------------------------------------

def solve_quadratic(a: float, b: float, c: float) -> Tuple[float, float]:
    disc = b**2 - 4*a*c
    if disc >= 0:
        return (
            (-b + math.sqrt(disc)) / (2*a),
            (-b - math.sqrt(disc)) / (2*a),
        )
    real = -b / (2*a)
    imag = math.sqrt(-disc) / (2*a)
    return complex(real, imag), complex(real, -imag)


def solve_for_k(
    m: float,
    k: int,
    max_n: int = 200,
    tol: float = 1e-6,
    max_iter: int = 100
) -> Optional[float]:

    def log_comb(n: float, k: int) -> float:
        return (
            math.lgamma(n + 1)
            - math.lgamma(k + 1)
            - math.lgamma(n - k + 1)
        )

    def f(n: float) -> float:
        return math.log(3) + log_comb(n, k) - math.log(m)

    a, b = k, max_n

    if f(b) < 0:
        return None

    for _ in range(max_iter):
        mid = 0.5 * (a + b)
        val = f(mid)

        if abs(val) < tol:
            return mid
        if val < 0:
            a = mid
        else:
            b = mid

    return 0.5 * (a + b)


def num_qubits(num_variables: int, order_compression: int) -> Optional[int]:
    if order_compression == 1:
        return num_variables //3

    if order_compression == 2:
        roots = solve_quadratic(1, -1, -2/3 * num_variables)
        return math.ceil(max(roots))

    value = solve_for_k(num_variables, order_compression)
    if value is None:
        return None

    return math.ceil(value)

# ------------------------------------------------
#  Parámetros
# ------------------------------------------------

num_variables = [3,4,5,6,7,8,9,10,12,14]


ORDERS_FULL = [1, 2, 3, 4, 5]
ORDERS_PARTIAL = [2, 3, 4, 5]

# ------------------------------------------------
#  Paleta fija por order (CLAVE)
# ------------------------------------------------

COLORS_K = {
    1: "rebeccapurple",
    2: "steelblue",
    3: "indianred",
    4: "seagreen",
    5: "darkorange",
}

# ------------------------------------------------
#  Cálculo de resultados
# ------------------------------------------------

def compute_results(order_list):
    results = {}
    for k in order_list:
        vals = []
        for n in num_variables:
            q = num_qubits(n**2 + n, k)
            vals.append(q)
        results[k] = vals
    return results


results_full = compute_results(ORDERS_FULL)
results_partial = compute_results(ORDERS_PARTIAL)

# ------------------------------------------------
#  Función de plot (colores garantizados)
# ------------------------------------------------

def plot_results(order_list, results, filename):
    plt.figure(figsize=(8, 6))

    for k in order_list:
        x = []
        y = []
        for n, q in zip(num_variables, results[k]):
            if q is not None:
                x.append(n)
                y.append(q)

        plt.plot(
            x,
            y,
            marker="o",
            label=f"order={k}",
            color=COLORS_K[k]
        )

    plt.xlabel("Number of objects")
    plt.ylabel("Required qubits")
    plt.title("Number of qubits for different orders of compression")
    plt.legend()
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()

# ------------------------------------------------
#  Generación de figuras
# ------------------------------------------------

output_dir = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/A_DIFFERENTIAL_COMPARISON"
os.makedirs(output_dir, exist_ok=True)

plot_results(
    ORDERS_FULL,
    results_full,
    os.path.join(output_dir, "1_Evolucion_cubits_BPP.png")
)

plot_results(
    ORDERS_PARTIAL,
    results_partial,
    os.path.join(output_dir, "2_Evolucion_cubits_BPP.png")
)

print("✅ Imágenes generadas con colores coherentes")
