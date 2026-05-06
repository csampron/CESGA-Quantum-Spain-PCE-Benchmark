#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import argparse
import json
import numpy as np
import time
import math
from typing import Tuple, Optional

# Permitir imports desde HOME
sys.path.append(os.getenv("HOME"))

from cunqa.qpu import get_QPUs, run
from cunqa.qjob import gather
from cunqa.qiskit_deps.transpiler import transpiler
from qiskit import ClassicalRegister


## FUNCIÓN APPEND JSON

def append_result_to_json(file_path, new_result):
    """
    Añade un diccionario 'new_result' a un archivo JSON con formato:
    {"resultados": [ ... ]}, usando bloqueo exclusivo (flock).
    """
    import json
    import os
    import fcntl

    # Asegura que el directorio existe
    os.makedirs(os.path.dirname(file_path), exist_ok=True)

    # Abrimos el archivo en modo lectura/escritura o lo creamos si no existe
    with open(file_path, "a+", encoding="utf-8") as f:
        f.seek(0)  # Ir al inicio
        # Bloqueo exclusivo: otro proceso esperará hasta que se libere
        fcntl.flock(f, fcntl.LOCK_EX)

        try:
            # Si el archivo está vacío, inicializamos la estructura
            try:
                f.seek(0)
                data = json.load(f)
                if not isinstance(data, dict) or "resultados" not in data:
                    data = {"resultados": []}
            except json.JSONDecodeError:
                data = {"resultados": []}

            # Añadir nuevo resultado
            data["resultados"].append(new_result)

            # Reescribir el archivo completo
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)

        finally:
            # Liberar el bloqueo
            fcntl.flock(f, fcntl.LOCK_UN)


# ============================================================
# FUNCIONES MATEMÁTICAS Y CIRCUITOS
# ============================================================

def solve_quadratic(a: float, b: float, c: float) -> Tuple[float, float]:
    disc = b**2 - 4*a*c
    if disc >= 0:
        return (-b + math.sqrt(disc)) / (2*a), (-b - math.sqrt(disc)) / (2*a)
    real = -b / (2*a)
    imag = math.sqrt(-disc) / (2*a)
    return complex(real, imag), complex(real, -imag)

def solve_for_k(m: float, k: int, max_n: int = 200, tol: float = 1e-6, max_iter: int = 100) -> Optional[float]:
    def log_comb(n: float, k: int) -> float:
        return math.lgamma(n + 1) - math.lgamma(k + 1) - math.lgamma(n - k + 1)
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

def compute_data(m, k, n_shots, family_name, seed=33):
    qubits = num_qubits(m, k)

    if qubits is None:
        return None
    num_layers = m ** (1 - (1 / k)) 
    layers = math.ceil(num_layers)

    from circuit_builder import Circuit

    qc_builder = Circuit(
        size=qubits,
        p=layers,
        entanglement='Taylor_efficient',
        rotation='Taylor_efficient',
        connectivity='brickwork_single_rotating',
        mode='custom'
    )
    qc_builder.compile_circuit()
    qc = qc_builder.get_circuit()

    # Medidas en X, Y, Z
    qc_z, qc_x, qc_y = qc.copy(), qc.copy(), qc.copy()
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

    compiled_x = transpiler(qc_x, backend, opt_level=2, seed=seed)
    compiled_y = transpiler(qc_y, backend, opt_level=2, seed=seed)
    compiled_z = transpiler(qc_z, backend, opt_level=2, seed=seed)
    compiled_circuits = [compiled_x, compiled_y, compiled_z]

    n_profundidad = compiled_y.depth()
    n_gates = sum(compiled_y.count_ops().values())
    n_params = len(compiled_y.parameters)

    rng = np.random.default_rng(seed)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi
    bound_circuit_list = [
        qc.assign_parameters({param: val for param, val in zip(qc.parameters, initial_params)})
        for qc in compiled_circuits
    ]

    start_time = time.perf_counter()
    qjobs = [run(qc, qpu, shots=n_shots, method="statevector", fusion_threshold = 1) for qc, qpu in zip(bound_circuit_list, QPUs)] # statevector_parallel_threshold = 10 // mps_parallel_threshold = 10 (con method = "matrix_product_state")
    #qjobs = [run(qc, qpu, shots=n_shots, method="statevector") for qc, qpu in zip(bound_circuit_list, QPUs)] # statevector_parallel_threshold = 10 // mps_parallel_threshold = 10 (con method = "matrix_product_state")
    
    results = gather(qjobs)
    end_time = time.perf_counter()
    
    average_time = (end_time - start_time)

    print(f"avareage_time: {average_time}")

    popsize = 3
    max_iter = 1000
    function_evaluations = popsize * max_iter * n_params
    total_time = function_evaluations * average_time

    teo_layers = layers

    return {
        "qubits": qubits,
        "n_profundidad": n_profundidad,
        "n_gates": n_gates,
        "n_params": n_params,
        "function_evaluations": function_evaluations,
        "average_time": average_time,
        "teo_layers": teo_layers,
        "total_time": total_time
    }

# ============================================================
# ARGPARSE
# ============================================================

parser = argparse.ArgumentParser(description="Experimento con JSON de resultados por combinación")
parser.add_argument("--family", type=str, required=True)
parser.add_argument("--tamaño", type=int, required=True)
parser.add_argument("--k", type=int, required=True)
parser.add_argument("--shots", type=int, required=True)
parser.add_argument("--nqpus", type=int, required=True)
parser.add_argument("--seed", type=int, default=33)
parser.add_argument("--output_dir", type=str, default="./Resultados")
args = parser.parse_args()

# ============================================================
# EJECUCIÓN Y GUARDADO
# ============================================================

os.makedirs(args.output_dir, exist_ok=True)

data = compute_data(args.tamaño, args.k, args.shots, args.family, seed=args.seed)

if data is not None:

    json_file = os.path.join(
        args.output_dir,
        f"results_size{args.tamaño}.json"
    )

    result = {
        "tamano": args.tamaño,
        "k": args.k,
        "shots": args.shots,
        **data
    }

    append_result_to_json(json_file, result)

    print(f"✔ Resultado añadido a {json_file}")

else:
    print(f"⚠ Experimento para tamaño={args.tamaño}, k={args.k} no generó datos")