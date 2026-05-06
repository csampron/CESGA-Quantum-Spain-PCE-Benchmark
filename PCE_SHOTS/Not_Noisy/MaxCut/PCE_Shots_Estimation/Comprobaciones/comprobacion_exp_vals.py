from pathlib import Path
import numpy as np
from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit_aer import AerSimulator

from src.op_graph import load_graph
from src.auxiliar import num_qubits
from src.circuit_builder import Circuit
from src.tensor_exp_value import (
    build_sign_tensor,
    run_with_probabilities,
    build_probability_tensor,
    select_nodes_from_aux
)


def comparar_valores_esperados_aer(problema, tamaño, k, n_shots, seed=33):
    """
    Calcula valores esperados y probabilidades usando solo AerSimulator:
      1️⃣ Simulación exacta (statevector)
      2️⃣ Ejecución con shots
    Luego imprime comparaciones por base (X, Y, Z).
    """

    parent = Path(__file__).resolve().parent

    # --- Cargar grafo y definir qubits ---
    graph, num_ver = load_graph(f"{parent}/src/graphs/{problema}_{tamaño}.mc")
    m = num_ver
    qubits = num_qubits(m, k)
    num_layers = int(np.ceil(m ** (1 - 1/k)))

    # --- Construcción del circuito ---
    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement="Taylor_efficient",
        rotation="Taylor_efficient",
        connectivity="brickwork_single_rotating"
    )
    qc_builder.compile_circuit()
    qc = qc_builder.get_circuit()

    # --- Parámetros iniciales ---
    rng = np.random.default_rng(seed)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi
    bound_circuit = qc.assign_parameters({p: v for p, v in zip(qc.parameters, initial_params)})

    # --- AerSimulator ---
    sim = AerSimulator(seed_simulator=seed)

    # --- Preparamos circuitos medidos para X, Y, Z ---
    circuits = {}
    # Z
    qc_z = bound_circuit.copy()
    cr_z = ClassicalRegister(qubits)
    qc_z.add_register(cr_z)
    qc_z.measure(range(qubits), range(qubits))
    circuits["Z"] = qc_z

    # X
    qc_x = bound_circuit.copy()
    for q in range(qubits):
        qc_x.h(q)
    cr_x = ClassicalRegister(qubits)
    qc_x.add_register(cr_x)
    qc_x.measure(range(qubits), range(qubits))
    circuits["X"] = qc_x

    # Y
    qc_y = bound_circuit.copy()
    for q in range(qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    cr_y = ClassicalRegister(qubits)
    qc_y.add_register(cr_y)
    qc_y.measure(range(qubits), range(qubits))
    circuits["Y"] = qc_y

    # --- Simulación exacta (statevector) ---
    qc_exact = bound_circuit.remove_final_measurements(inplace=False)
    qc_exact.save_statevector()
    compiled_exact = transpile(qc_exact, sim, optimization_level=0)
    result_exact = sim.run(compiled_exact).result()
    psi_exact = result_exact.get_statevector(compiled_exact)

    # Probabilidades exactas
    probs_exact = {}
    probs_exact["Z"] = np.abs(psi_exact)**2

    # Para X y Y, aplicamos las transformaciones de base
    qc_temp = QuantumCircuit(qubits)
    qc_temp.set_statevector(psi_exact)
    for q in range(qubits):
        qc_temp.h(q)
    qc_temp.save_statevector()
    state_x = sim.run(transpile(qc_temp, sim, optimization_level=0)).result().get_statevector()
    probs_exact["X"] = np.abs(state_x)**2

    qc_temp = QuantumCircuit(qubits)
    qc_temp.set_statevector(psi_exact)
    for q in range(qubits):
        qc_temp.sdg(q)
        qc_temp.h(q)
    qc_temp.save_statevector()
    state_y = sim.run(transpile(qc_temp, sim, optimization_level=0)).result().get_statevector()
    probs_exact["Y"] = np.abs(state_y)**2

    # --- Simulación con shots ---
    results_shots = {b: sim.run(transpile(circuits[b], sim, optimization_level=2), shots=n_shots).result()
                     for b in circuits}

    counts_list = [results_shots[b].get_counts() for b in ["X", "Y", "Z"]]

    # counts_list: lista de diccionarios de counts para [X, Y, Z]
    probs_list = []
    for counts in counts_list:
        # convertir dict de counts a array de probabilidades
        bitstrings = [f"{i:0{qubits}b}" for i in range(2**qubits)]
        p = np.array([counts.get(b, 0)/n_shots for b in bitstrings])
        probs_list.append(p.reshape(-1, 1))  # forma (2^n_qubits, 1)

    # Apilar en eje de circuitos → forma (3, 2^n_qubits, 1)
    probs_shots = np.stack(probs_list, axis=0)


    # --- Tensor de signos y valores esperados ---
    d_t = build_sign_tensor(n_circuits=3, n_qubits=qubits, k_degree=k)

    aux_exact = run_with_probabilities(d_t, np.stack([probs_exact["X"], probs_exact["Y"], probs_exact["Z"]], axis=0)[:,:,None])["reshaped_result"]
    aux_shots = run_with_probabilities(d_t, probs_shots)["reshaped_result"]

    exp_exact = select_nodes_from_aux(aux_exact, m, m//3, return_concatenated=True)
    exp_shots = select_nodes_from_aux(aux_shots, m, m//3, return_concatenated=True)

    # --- Organizar por base ---
    def organizar_por_base(node_exp_map):
        n = m//3
        rem = m - 2*n
        base_dict = {"X": {}, "Y": {}, "Z": {}}
        for i, (node, val) in enumerate(node_exp_map.items()):
            if i < n:
                base_dict["X"][node] = val
            elif i < 2*n:
                base_dict["Y"][node] = val
            else:
                base_dict["Z"][node] = val
        return base_dict

    exp_exact_base = organizar_por_base(exp_exact)
    exp_shots_base = organizar_por_base(exp_shots)

    # --- Imprimir ---
    print(f"\n=== Probabilidades EXACTAS ===")
    for base in ["X","Y","Z"]:
        print(f"Base {base}:")
        for i,p in enumerate(probs_exact[base]):
            print(f"  {i:04b} : {p:.6f}")
        print()

    probs_shots_dict = {
    "X": probs_shots[0,:,0],
    "Y": probs_shots[1,:,0],
    "Z": probs_shots[2,:,0]
    }

    print(f"\n=== Probabilidades con SHOTS (n_shots={n_shots}) ===")
    for base in ["X","Y","Z"]:
        print(f"Base {base}:")
        for i, p in enumerate(probs_shots_dict[base]):
            print(f"  {i:04b} : {p:.6f}")
        print()

    print(f"\n=== Valores esperados EXACTOS ===")
    for base in ["X","Y","Z"]:
        print(f"Base {base}:")
        for node,val in exp_exact_base[base].items():
            print(f"  Nodo {node}: {val:.6f}")
        print()

    print(f"\n=== Valores esperados con SHOTS (n_shots={n_shots}) ===")
    for base in ["X","Y","Z"]:
        print(f"Base {base}:")
        for node,val in exp_shots_base[base].items():
            print(f"  Nodo {node}: {val:.6f}")
        print()

    return {
        "probs_exact": probs_exact,
        "probs_shots": probs_shots,
        "exp_exact": exp_exact_base,
        "exp_shots": exp_shots_base,
        "n_shots": n_shots
    }


# Ejemplo de uso
comparar_valores_esperados_aer("MaxCut", 10, 2, 10000000)
