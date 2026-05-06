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

from src.tensor_exp_value import (
    build_sign_tensor,
    build_probability_tensor,
    run_with_probabilities,
    select_nodes_from_aux,
    combine_counts_shots,
    combine_counts_circuits
)

from cunqa.qutils import get_QPUs
from cunqa.qiskit_deps.transpiler import transpiler
from cunqa.qjob import gather


def comprobacion_valores_esperados(
    problema: str,
    tamaño: int,
    k: int,
    n_shots: int,
    seed: int = 33,
    CUNQA: str = "Circuits",  # "Shots", "Circuits", "Simulation"
    family_name: str | None = None,
):
    """
    Ejecuta un experimento VQA y devuelve probabilidades y valores esperados.
    Imprime resultados por base (X,Y,Z) y por nodo.
    """

    parent = Path(__file__).resolve().parent
    graph, num_ver = load_graph(f"{parent}/src/graphs/{problema}_{tamaño}.mc")
    m = num_ver

    qubits = num_qubits(m, k)
    num_layers = math.ceil(m ** (1 - (1 / k)))
    list_size = m // 3

    # Construcción del circuito
    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement="Taylor_efficient",
        rotation="Taylor_efficient",
        connectivity="brickwork_single_rotating",
    )
    qc_builder.compile_circuit()
    qc = qc_builder.get_circuit()

    # Tensor de signos
    d_t = build_sign_tensor(n_circuits=3, n_qubits=qubits, k_degree=k)

    # Parámetros iniciales
    rng = np.random.default_rng(seed)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi
    bound_circuit = qc.assign_parameters(
        {p: v for p, v in zip(qc.parameters, initial_params)}
    )

    counts_list = []

    # ======================================================
    # --- SIMULACIÓN EXACTA ---
    # ======================================================
    sim = AerSimulator(seed_simulator=seed)

    def prepare_for_statevector(qc):
        qc_clean = qc.remove_final_measurements(inplace=False)
        for creg in qc_clean.cregs:
            qc_clean.remove_register(creg)
        qc_clean.save_statevector()
        return qc_clean

    bound_circuit_clean = prepare_for_statevector(bound_circuit)
    compiled_clean = transpile(bound_circuit_clean, sim, optimization_level=0)
    state_exact = sim.run(compiled_clean).result().get_statevector(compiled_clean)

    # Probabilidades exactas
    probs_z_exact = np.abs(state_exact) ** 2

    qc_x = QuantumCircuit(qubits)
    qc_x.set_statevector(state_exact)
    for q in range(qubits):
        qc_x.h(q)
    qc_x.save_statevector()
    probs_x_exact = np.abs(sim.run(qc_x).result().get_statevector(qc_x)) ** 2

    qc_y = QuantumCircuit(qubits)
    qc_y.set_statevector(state_exact)
    for q in range(qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    qc_y.save_statevector()
    probs_y_exact = np.abs(sim.run(qc_y).result().get_statevector(qc_y)) ** 2

    probs_exact = {"X": probs_x_exact, "Y": probs_y_exact, "Z": probs_z_exact}

    # ======================================================
    # --- EJECUCIÓN CON SHOTS (QPU backend) ---
    # ======================================================
    if CUNQA in ["Shots", "Circuits"]:
        QPUs = get_QPUs(on_node=False, family=family_name)
        if not QPUs:
            raise RuntimeError("No se encontraron QPUs disponibles")
        backend = QPUs[0].backend

        # Preparar circuitos con medidas
        qc_z = bound_circuit.copy()
        cr_z = ClassicalRegister(qubits)
        qc_z.add_register(cr_z)
        qc_z.measure(range(qubits), range(qubits))

        qc_x = bound_circuit.copy()
        for q in range(qubits):
            qc_x.h(q)
        cr_x = ClassicalRegister(qubits)
        qc_x.add_register(cr_x)
        qc_x.measure(range(qubits), range(qubits))

        qc_y = bound_circuit.copy()
        for q in range(qubits):
            qc_y.sdg(q)
            qc_y.h(q)
        cr_y = ClassicalRegister(qubits)
        qc_y.add_register(cr_y)
        qc_y.measure(range(qubits), range(qubits))

        compiled_circuits = [
            transpiler(c, backend, opt_level=2, seed=seed)
            for c in [qc_x, qc_y, qc_z]
        ]

        if CUNQA == "Shots":
            shots_per_qpu = [n_shots // len(QPUs)] * len(QPUs)
            shots_per_qpu[0] += n_shots % len(QPUs)

            qjobs = [
                qpu.run(qc, shots=shots)
                for qpu, shots in zip(QPUs, shots_per_qpu)
                for qc in compiled_circuits
            ]
            results = gather(qjobs)
            counts_list = combine_counts_shots(
                results, n_qubits=qubits, n_circuits=3, num_qpus=len(QPUs)
            )[1]

        else:  # Circuits
            qjobs = [qpu.run(qc, shots=n_shots) for qc, qpu in zip(compiled_circuits, QPUs)]
            results = gather(qjobs)
            counts_list = combine_counts_circuits(results, n_qubits=qubits)[1]

            for job, base in zip(qjobs, ["X","Y","Z"]*len(QPUs)):
                print(f"{base}: {job}")

            for i, df in enumerate(counts_list):
                print(f"\nCounts {i} (base {['X','Y','Z'][i]}):")
                print(df.head())

        # --- Convertir DataFrames a arrays de probabilidades ---
        probs_shots = {}
        for base, df in zip(["X", "Y", "Z"], counts_list):
            total_counts = df["total_counts"].to_numpy()
            probs_array = total_counts / total_counts.sum()
            probs_shots[base] = probs_array

    else:
        probs_shots = probs_exact.copy()
        counts_list = [probs_x_exact, probs_y_exact, probs_z_exact]

    # ======================================================
    # --- Valores esperados ---
    # ======================================================
    p_t_exact = build_probability_tensor([probs_x_exact, probs_y_exact, probs_z_exact], 1, qubits)
    aux_exact = run_with_probabilities(d_t, p_t_exact)["reshaped_result"]
    node_exp_map_exact = select_nodes_from_aux(aux_exact, m, list_size, return_concatenated=True)

    p_t_shots = build_probability_tensor([probs_shots["X"], probs_shots["Y"], probs_shots["Z"]], n_shots, qubits)
    aux_shots = run_with_probabilities(d_t, p_t_shots)["reshaped_result"]
    node_exp_map_shots = select_nodes_from_aux(aux_shots, m, list_size, return_concatenated=True)

    # ======================================================
    # --- Imprimir resultados legibles ---
    # ======================================================
    def print_probs(probs, n_shots=None):
        for base in ["X","Y","Z"]:
            print(f"Base {base}:")
            for i, p in enumerate(probs[base]):
                if p > 1e-6:
                    print(f"  {i:04b} : {p:.6f}")
            print()
        if n_shots: 
            print(f"(n_shots={n_shots})\n")

    def print_exp(node_map, label):
        print(f"=== Valores esperados {label} ===")
        for node, val in node_map.items():
            print(f"  Nodo {node}: {val:.6f}")
        print()

    print("\n=== Probabilidades EXACTAS ===")
    print_probs(probs_exact)
    print("\n=== Probabilidades con SHOTS ===")
    print_probs(probs_shots, n_shots=n_shots)

    print_exp(node_exp_map_exact, "EXACTOS")
    print_exp(node_exp_map_shots, f"SHOTS (n_shots={n_shots})")

    return {
        "probs_exact": probs_exact,
        "probs_shots": probs_shots,
        "exp_exact": node_exp_map_exact,
        "exp_shots": node_exp_map_shots
    }





nombre_de_familia = "family_circuits_MaxCut_10_shots6"

res = comprobacion_valores_esperados(
    problema="MaxCut",
    tamaño=10,
    k=2,
    n_shots=10000000,
    seed=33,
    CUNQA="Circuits",
    family_name=nombre_de_familia
)