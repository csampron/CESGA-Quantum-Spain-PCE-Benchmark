import os
import sys

sys.path.append(os.getenv("HOME"))

import math
import numpy as np
from pathlib import Path

from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from src.op_graph import load_graph
from src.auxiliar import num_qubits
from src.circuit_builder import Circuit
from src.tensor_exp_value import build_sign_tensor
from src.tensor_exp_value import run_with_probabilities
from src.tensor_exp_value import build_probability_tensor
from src.tensor_exp_value import select_nodes_from_aux

from src.tensor_exp_value import (
    build_probability_tensor,
    run_with_probabilities,
    select_nodes_from_aux,
    combine_counts_shots,
    combine_counts_circuits
)

from cunqa.qutils import get_QPUs
from cunqa.qiskit_deps.transpiler import transpiler
from cunqa.qjob import gather

# ======================================================
# Reconstrucción simple del statevector
# ======================================================

def reconstruir_statevector(probs_x, probs_y, probs_z):
    """
    Reconstrucción aproximada del statevector a partir de
    probabilidades en bases X, Y y Z.
    """

    probs_x = np.array(probs_x)
    probs_y = np.array(probs_y)
    probs_z = np.array(probs_z)

    # Magnitud desde base Z
    amplitudes_abs = np.sqrt(probs_z)

    # Estimación fase (simplificada)
    real_part = 2 * probs_x - 1
    imag_part = 2 * probs_y - 1

    phase = np.arctan2(imag_part, real_part)

    psi = amplitudes_abs * np.exp(1j * phase)

    # Normalizar
    norm = np.linalg.norm(psi)
    if norm != 0:
        psi = psi / norm

    return psi


# ======================================================
# FUNCIÓN PRINCIPAL
# ======================================================

def recuperar_probabilidades(
    problema: str,
    tamaño: int,
    k: int,
    n_shots: int,
    seed: int = 33,
):
    """
    Ejecuta el circuito parametrizado y devuelve:
    - Probabilidades exactas por base (X, Y, Z)
    - Probabilidades obtenidas con n_shots
    - Statevector reconstruido aproximado a partir de las probabilidades con shots

    Returns
    -------
    dict:
        {
            "exact": {"X": ..., "Y": ..., "Z": ...},
            "shots": {"X": ..., "Y": ..., "Z": ...},
            "psi_recon": statevector reconstruido desde las probabilidades de shots
        }
    """

    parent = Path(__file__).resolve().parent

    # 1. Cargar grafo
    graph, num_ver = load_graph(f"{parent}/src/graphs/{problema}_{tamaño}.mc")

    # 2. Definir qubits y capas
    m = num_ver
    qubits = num_qubits(m, k)
    num_layers = math.ceil(m ** (1 - (1 / k)))

    # 3. Construcción circuito
    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement="Taylor_efficient",
        rotation="Taylor_efficient",
        connectivity="brickwork_single_rotating",
    )
    qc_builder.compile_circuit()
    qc = qc_builder.get_circuit()

    # 4. Parámetros iniciales
    rng = np.random.default_rng(seed)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi
    bound_circuit = qc.assign_parameters(
        {p: v for p, v in zip(qc.parameters, initial_params)}
    )

    # ======================================================
    # SIMULATION EXACTA
    # ======================================================
    sim = AerSimulator(seed_simulator=seed)

    qc_clean = bound_circuit.remove_final_measurements(inplace=False)
    qc_clean.save_statevector()
    compiled_clean = transpile(qc_clean, sim, optimization_level=0)
    result = sim.run(compiled_clean).result()
    psi_exact = result.get_statevector(compiled_clean)

    # Probabilidades exactas
    probs_exact = {}
    # Z
    probs_exact["Z"] = np.abs(psi_exact) ** 2
    # X
    qc_x = QuantumCircuit(qubits)
    qc_x.set_statevector(psi_exact)
    for q in range(qubits):
        qc_x.h(q)
    qc_x.save_statevector()
    state_x = sim.run(qc_x).result().get_statevector(qc_x)
    probs_exact["X"] = np.abs(state_x) ** 2
    # Y
    qc_y = QuantumCircuit(qubits)
    qc_y.set_statevector(psi_exact)
    for q in range(qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    qc_y.save_statevector()
    state_y = sim.run(qc_y).result().get_statevector(qc_y)
    probs_exact["Y"] = np.abs(state_y) ** 2

    # ======================================================
    # SHOTS
    # ======================================================
    counts_list = []

    # --- Z ---
    qc_z = bound_circuit.copy()
    cr_z = ClassicalRegister(qubits)
    qc_z.add_register(cr_z)
    qc_z.measure(range(qubits), range(qubits))

    # --- X ---
    qc_x = bound_circuit.copy()
    for q in range(qubits):
        qc_x.h(q)
    cr_x = ClassicalRegister(qubits)
    qc_x.add_register(cr_x)
    qc_x.measure(range(qubits), range(qubits))

    # --- Y ---
    qc_y = bound_circuit.copy()
    for q in range(qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    cr_y = ClassicalRegister(qubits)
    qc_y.add_register(cr_y)
    qc_y.measure(range(qubits), range(qubits))

    compiled_x = transpile(qc_x, sim, optimization_level=2)
    compiled_y = transpile(qc_y, sim, optimization_level=2)
    compiled_z = transpile(qc_z, sim, optimization_level=2)

    circuits = [compiled_x, compiled_y, compiled_z]

    results = [
        sim.run(circ, shots=n_shots, seed_simulator=seed).result()
        for circ in circuits
    ]

    counts_list = [res.get_counts() for res in results]

    # Convertir counts → probabilidades ordenadas
    bitstrings = [f"{i:0{qubits}b}" for i in range(2**qubits)]
    probs_shots = {}
    for base, counts in zip(["X", "Y", "Z"], counts_list):
        total = sum(counts.values())
        p = np.array([counts.get(b, 0) / total for b in bitstrings])
        probs_shots[base] = p

    # ======================================================
    # Reconstruir statevector aproximado desde probabilidades con shots
    # ======================================================
    def reconstruir_statevector(probs_x, probs_y, probs_z):
        probs_x = np.array(probs_x)
        probs_y = np.array(probs_y)
        probs_z = np.array(probs_z)

        amplitudes_abs = np.sqrt(probs_z)
        real_part = 2 * probs_x - 1
        imag_part = 2 * probs_y - 1
        phase = np.arctan2(imag_part, real_part)
        psi = amplitudes_abs * np.exp(1j * phase)
        norm = np.linalg.norm(psi)
        if norm != 0:
            psi = psi / norm
        return psi

    psi_recon = reconstruir_statevector(
        probs_shots["X"], probs_shots["Y"], probs_shots["Z"]
    )

    return {
        "exact": probs_exact,
        "shots": probs_shots,
        "psi_recon": psi_recon,
        "n_shots": n_shots
    }


res = recuperar_probabilidades("MaxCut", 10, 2, 10000000)

# ======================================================
# Probabilidades exactas
# ======================================================
print("=== Probabilidades EXACTAS ===")
for base in ["X", "Y", "Z"]:
    probs = res["exact"][base]
    print(f"Base {base}:")
    for i, p in enumerate(probs):
        if p > 1e-6:  # Mostrar solo probabilidades significativas
            print(f"  {i:0{int(np.log2(len(probs)))}b} : {p:.6f}")
    print()

# ======================================================
# Probabilidades con shots
# ======================================================
print(f"=== Probabilidades con SHOTS (n_shots={res['n_shots']}) ===")
for base in ["X", "Y", "Z"]:
    probs = res["shots"][base]
    print(f"Base {base}:")
    for i, p in enumerate(probs):
        if p > 1e-6:  # Mostrar solo probabilidades significativas
            print(f"  {i:0{int(np.log2(len(probs)))}b} : {p:.6f}")
    print()

# Statevector reconstruido desde shots
#res["psi_recon"]
