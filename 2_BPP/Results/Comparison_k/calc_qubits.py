import math
from typing import Tuple

# ==============================
# Funciones proporcionadas
# ==============================
def solve_quadratic(a: float, b: float, c: float) -> Tuple[float, float]:
    discriminant = b ** 2 - 4 * a * c
    if discriminant >= 0:
        x_1 = (-b + math.sqrt(discriminant)) / (2 * a)
        x_2 = (-b - math.sqrt(discriminant)) / (2 * a)
    else:
        x_1 = complex((-b / (2 * a)), math.sqrt(-discriminant) / (2 * a))
        x_2 = complex((-b / (2 * a)), -math.sqrt(-discriminant) / (2 * a))
    return x_1, x_2

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

# ==============================
# Script principal
# ==============================
print("num_items | k | m      | qubits")
print("---------------------------------")
for num_items in range(3, 15):  # 3 a 14
    m = num_items**2 + num_items
    for k in [2, 3]:
        qubits = num_qubits(m, k)
        if qubits == num_items:
            qubits += 1
        print(f"{num_items:9d} | {k} | {m:6d} | {qubits:6d}")
