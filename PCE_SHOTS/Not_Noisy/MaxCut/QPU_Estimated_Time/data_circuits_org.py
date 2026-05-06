import os
import math
import matplotlib.pyplot as plt
from typing import Tuple, Optional
import numpy as np

from qiskit import ClassicalRegister

# Permitir imports desde HOME
sys.path.append(os.getenv("HOME"))

from cunqa.qpu import get_QPUs, run
from cunqa.qiskit_deps.transpiler import transpiler

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
        return num_variables

    if order_compression == 2:
        roots = solve_quadratic(1, -1, -2/3 * num_variables)
        return math.ceil(max(roots))

    value = solve_for_k(num_variables, order_compression)

    if value is None:
        return None

    return math.ceil(value)


# ------------------------------------------------
#  NUEVO: cálculo de parámetros del circuito
# ------------------------------------------------

def compute_data(m, k, n_shots, family_name):

    qubits = num_qubits(m, k)

    if qubits is None:
        return None

    layers = int(np.ceil(1.5 * (qubits ** (np.floor(k / 2)))))
    num_layers = math.ceil(layers)

    from circuit_builder import Circuit

    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement='Taylor_efficient',
        rotation='Taylor_efficient',
        connectivity='brickwork_single_rotating',
        mode='custom'
    )

    qc = qc_builder.compile_circuit()

    qc_z = qc.copy()
    qc_x = qc.copy()
    qc_y = qc.copy()

    # --- Preparar circuitos con medidas ---
    cr_z = ClassicalRegister(qubits)
    qc_z.add_register(cr_z)
    qc_z.measure(range(qubits), range(qubits))

    
    for q in range(qubits):
        qc_x.h(q)
    cr_x = ClassicalRegister(qubits)
    qc_x.add_register(cr_x)
    qc_x.measure(range(qubits), range(qubits))

    
    for q in range(qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    cr_y = ClassicalRegister(qubits)
    qc_y.add_register(cr_y)
    qc_y.measure(range(qubits), range(qubits))

    QPUs = get_QPUs(co_located=True, family=family_name)
    backend = QPUs[0].backend
    
    compiled_x = transpiler(qc_x, backend, opt_level=2, seed = 33)
    compiled_y = transpiler(qc_y, backend, opt_level=2, seed = 33)
    compiled_z = transpiler(qc_z, backend, opt_level=2, seed = 33)

    compiled_circuits = [compiled_x, compiled_y, compiled_z]

    n_profundidad = compiled_y.depth()
    n_gates =  sum(compiled_y.count_ops().values())
    n_params = len(compiled_y.parameters)

    # Medimos los tiempos de ejecución
    rng = np.random.default_rng(33)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi

    bound_circuit_list = [
        qc.assign_parameters({param: val for param, val in zip(qc.parameters, initial_params)})
        for qc in compiled_circuits
    ]

    import time
    # Medimos los tiempos individuales de ejecución en cada QPU
    execution_times = []
    qjobs = []

    for qc, qpu in zip(bound_circuit_list, QPUs):
        start_time = time.perf_counter()
        job = run(qc, qpu, shots=n_shots, method="statevector")
        end_time = time.perf_counter()
        
        exec_time = end_time - start_time
        execution_times.append(exec_time)
        qjobs.append(job)
        print(f"Tiempo de ejecución en {qpu}: {exec_time:.4f} s")

    # Calculamos la media de los tiempos
    average_time = sum(execution_times) / len(execution_times)

    popsize = 3
    max_iter = 1000
    function_evaluations = popsize*max_iter*n_params

    total_time = function_evaluations*average_time

    return qubits, n_profundidad, n_gates, n_params, total_time


# ------------------------------------------------
#  Parámetros
# ------------------------------------------------

num_variables = [10, 20, 40, 50, 60, 100, 150, 200, 250, 300]

ORDERS_FULL = [1, 2, 3, 4, 5]
ORDERS_PARTIAL = [2, 3, 4, 5]

# ------------------------------------------------
#  Paleta fija por order
# ------------------------------------------------

DEFAULT_COLORS = plt.rcParams['axes.prop_cycle'].by_key()['color']

ORDER_COLORS = {
    1: DEFAULT_COLORS[0],
    2: DEFAULT_COLORS[1],
    3: DEFAULT_COLORS[2],
    4: DEFAULT_COLORS[3],
    5: DEFAULT_COLORS[4],
}

## ------------------------------------------------
#  Cálculo de resultados (PARAMS, QUBITS, PROFUNDIDAD, TOTAL TIME)
# ------------------------------------------------

def compute_results(order_list):
    results = {}
    for k in order_list:
        vals = []
        for m in num_variables:
            params = compute_data(m, k, n_shots=1024, family_name="example_family")
            vals.append(params)
        results[k] = vals
    return results

results_full = compute_results(ORDERS_FULL)
results_partial = compute_results(ORDERS_PARTIAL)

# ------------------------------------------------
#  Función de plot generalizada
# ------------------------------------------------

def plot_results(order_list, results, y_index, ylabel, filename, ylim=None):
    """
    y_index: 0=qubits, 1=profundidad, 2=n_gates, 3=n_params, 4=total_time
    """
    plt.figure(figsize=(9, 6))
    x = num_variables

    for k in order_list:
        y = []
        for entry in results[k]:
            if entry is None:
                y.append(float("nan"))
            else:
                y.append(entry[y_index])
        plt.plot(
            x,
            y,
            marker="o",
            label=f"order={k}",
            color=ORDER_COLORS.get(k, "black")
        )

    plt.xlabel("Número de nodos")
    plt.ylabel(ylabel)
    plt.title(f"{ylabel} vs Número de nodos")
    if ylim is not None:
        plt.ylim(0, ylim)
    plt.grid(True)
    plt.legend(loc="upper left")
    plt.tight_layout()
    plt.savefig(filename, dpi=300)
    plt.close()


# ------------------------------------------------
#  Generación de figuras
# ------------------------------------------------

output_dir = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_FAC/Resources"
os.makedirs(output_dir, exist_ok=True)

# Número de nodos vs Qubits
plot_results(
    ORDERS_FULL,
    results_full,
    y_index=0,
    ylabel="Número de qubits",
    filename=os.path.join(output_dir, "qubits_vs_nodes.png")
)

# Número de nodos vs Profundidad
plot_results(
    ORDERS_FULL,
    results_full,
    y_index=1,
    ylabel="Profundidad",
    filename=os.path.join(output_dir, "depth_vs_nodes.png")
)

# Número de nodos vs Número de parámetros
plot_results(
    ORDERS_FULL,
    results_full,
    y_index=3,
    ylabel="Número de parámetros",
    filename=os.path.join(output_dir, "params_vs_nodes.png")
)

# Número de nodos vs Tiempo total
plot_results(
    ORDERS_FULL,
    results_full,
    y_index=4,
    ylabel="Tiempo total (s)",
    filename=os.path.join(output_dir, "total_time_vs_nodes.png")
)

print("✅ Imágenes generadas para qubits, profundidad, parámetros y tiempo total")