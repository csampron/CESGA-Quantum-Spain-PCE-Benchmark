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

def ejecutar_valores_esperados_shots(
    problema: str,
    tamaño: int,
    k: int,
    n_shots: int,
    seed: int = 33,
    CUNQA: str = "Circuits",  # "Shots", "Circuits", "Simulation"
    family_name: str | None = None,
):
    """
    Ejecuta un experimento VQA y devuelve los valores esperados.
    Soporta ejecución con shots, por circuitos, o simulación exacta (statevector).
    """

    # ======================================================
    # 1. Cargar grafo
    # ======================================================
    parent = Path(__file__).resolve().parent
    graph, num_ver = load_graph(f"{parent}/src/graphs/{problema}_{tamaño}.mc")

    # ======================================================
    # 2. Definir qubits y capas
    # ======================================================
    m = num_ver

    qubits = num_qubits(m, k)
    num_layers = math.ceil(m ** (1 - (1 / k)))
    list_size = m // 3

    # ======================================================
    # 3. Construcción del circuito
    # ======================================================
    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement="Taylor_efficient",
        rotation="Taylor_efficient",
        connectivity="brickwork_single_rotating",
    )
    qc_builder.compile_circuit()
    qc = qc_builder.get_circuit()

    # ======================================================
    # 4. Tensor de signo
    # ======================================================
    d_t = build_sign_tensor(n_circuits=3, n_qubits=qubits, k_degree=k)

    # ======================================================
    # 5. Parámetros iniciales
    # ======================================================
    rng = np.random.default_rng(seed)
    initial_params = rng.random(len(qc.parameters)) * 2 * np.pi

    bound_circuit = qc.assign_parameters(
        {p: v for p, v in zip(qc.parameters, initial_params)}
    )

    # ======================================================
    # 6. Ejecutar según CUNQA
    # ======================================================
    counts_list = []

    

    if CUNQA in ["Shots", "Circuits"]:
        # --- Preparar circuitos con medidas ---
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


        if CUNQA == "Shots":
            QPUs = get_QPUs(on_node=False, family=family_name)
            if not QPUs:
                raise RuntimeError("No se encontraron QPUs disponibles")
            shots_per_qpu = [n_shots // len(QPUs)] * len(QPUs)
            shots_per_qpu[0] += n_shots % len(QPUs)

            sim = QPUs[0].backend
           

            # --- Transpile ---
            compiled_x = transpiler(qc_x, sim, opt_level=2, seed = 33)
            compiled_y = transpiler(qc_y, sim, opt_level=2, seed = 33)
            compiled_z = transpiler(qc_z, sim, opt_level=2, seed = 33)
            compiled_circuits = [compiled_x, compiled_y, compiled_z]


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
            QPUs = get_QPUs(on_node=False, family=family_name)

            backend = QPUs[0].backend

            """ print("Tipo de sim:", type(sim)) """
            """ print("Atributos sim:", dir(sim)) """

            """ print("Basis gates backend:") """
            """ print(sim.basis_gates) """


            """ print("Lista de puertas del circuito:") """
            """ for instr, qargs, cargs in qc_x.data: """
            """     print(f"Gate: {instr.name}, qubits: {len(qargs)}, parámetros: {instr.params}") """


            # --- Transpile ---
            compiled_x = transpiler(qc_x, backend, opt_level=2, seed = 33)
            compiled_y = transpiler(qc_y, backend, opt_level=2, seed = 33)
            compiled_z = transpiler(qc_z, backend, opt_level=2, seed = 33)
            compiled_circuits = [compiled_x, compiled_y, compiled_z]


            qjobs = [qpu.run(qc, shots=n_shots) for qc, qpu in zip(compiled_circuits, QPUs)]
            results = gather(qjobs)
            counts_list = combine_counts_circuits(results, n_qubits=qubits)[1]

    elif CUNQA == "Simulation":
        sim = AerSimulator(seed_simulator=seed)

        # --- Preparar circuito sin medidas ---
        def prepare_for_statevector(qc):
            qc_clean = qc.remove_final_measurements(inplace=False)
            for creg in qc_clean.cregs:
                qc_clean.remove_register(creg)
            qc_clean.save_statevector()
            return qc_clean

        bound_circuit_z = prepare_for_statevector(bound_circuit)
        compiled_z = transpile(bound_circuit_z, sim, optimization_level=0)
        state_z = sim.run(compiled_z).result().get_statevector(compiled_z)

        # Probabilidades exactas Z
        probs_z = np.abs(state_z) ** 2

        # X
        qc_x = QuantumCircuit(qubits)
        qc_x.set_statevector(state_z)
        for q in range(qubits):
            qc_x.h(q)
        qc_x.save_statevector()
        state_x = sim.run(qc_x).result().get_statevector(qc_x)
        probs_x = np.abs(state_x) ** 2

        # Y
        qc_y = QuantumCircuit(qubits)
        qc_y.set_statevector(state_z)
        for q in range(qubits):
            qc_y.sdg(q)
            qc_y.h(q)
        qc_y.save_statevector()
        state_y = sim.run(qc_y).result().get_statevector(qc_y)
        probs_y = np.abs(state_y) ** 2

        counts_list = [probs_x, probs_y, probs_z]
        n_shots = 1

    else:
        raise ValueError(f"CUNQA desconocido: {CUNQA}")

    # ======================================================
    # 7. Construir tensor de probabilidades
    # ======================================================
    p_t = build_probability_tensor(counts_list, n_shots, qubits)

    # ======================================================
    # 8. Calcular valores esperados
    # ======================================================
    aux = run_with_probabilities(d_t, p_t)["reshaped_result"]
    node_exp_map = select_nodes_from_aux(
        aux, m, list_size, return_concatenated=True
    )

    return node_exp_map


import numpy as np

def calcular_metricas(values_circ: np.ndarray, values_sim: np.ndarray) -> dict:
    """
    Calcula métricas de error entre los valores esperados obtenidos por Circuits
    y la referencia Simulation.

    Args:
        values_circ: array de valores esperados calculados con n_shots
        values_sim: array de valores esperados exactos (Simulation)

    Returns:
        dict con las métricas:
            - mae: mean absolute error
            - mse: mean squared error
            - std: desviación típica de la diferencia
            - max_error: error máximo absoluto
    """
    diff = values_circ - values_sim
    metrics = {
        "mae": float(np.mean(np.abs(diff))),
        "mse": float(np.mean(diff**2)),
        "std": float(np.std(diff)),
        "max_error": float(np.max(np.abs(diff)))
    }
    return metrics



import json
import fcntl

def guardar_resultados_json(tamaño: int, k: int, shots: int, seed: int, result_dict: dict):
    """
    Guarda resultados de un experimento en JSON por tamaño y shots,
    añadiendo los bloques de semillas sin sobrescribir resultados previos.
    
    Estructura resultante:
    Resultados/
        resultados_tamaño_10.json
        resultados_tamaño_20.json
    Dentro de cada archivo:
    {
        "shots100": [
            {"seed": 1, "mae": 0.0023, ...},
            {"seed": 2, "mae": 0.0031, ...}
        ],
        "shots200": [ ... ]
    }
    
    Args:
        tamaño: número de nodos del grafo
        shots: número de shots
        seed: semilla utilizada
        result_dict: diccionario con métricas (mae, mse, etc.)
        base_dir: carpeta donde guardar los resultados (por defecto 'Resultados')
    """
    # Asegurar directorio
    base_dir: str = f"Resultados/k_{k}/m_{tamaño}"
    Path(base_dir).mkdir(parents=True, exist_ok=True)

    # Archivo JSON por tamaño
    json_file = Path(base_dir) / f"resultados_tamaño_{tamaño}.json"
    shots_key = f"shots{shots}"

    # Abrimos en modo lectura/escritura o creamos si no existe
    with open(json_file, "a+", encoding="utf-8") as f:
        f.seek(0)
        fcntl.flock(f, fcntl.LOCK_EX)
        try:
            try:
                data = json.load(f)
                if not isinstance(data, dict):
                    data = {}
            except json.JSONDecodeError:
                data = {}

            # Inicializar clave de shots
            if shots_key not in data:
                data[shots_key] = []

            # Añadir el resultado con seed
            entry = {"seed": seed}
            entry.update(result_dict)
            data[shots_key].append(entry)

            # Reescribir JSON
            f.seek(0)
            f.truncate()
            json.dump(data, f, ensure_ascii=False, indent=2)
        finally:
            fcntl.flock(f, fcntl.LOCK_UN)


