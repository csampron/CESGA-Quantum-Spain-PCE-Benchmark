### ========================================================= ###
### Función: loss_func_estimator
### ========================================================= ###
###
### Evalúa la función de pérdida (loss) para un conjunto de parámetros
### de un ansatz cuántico, usando tensores precomputados y counts
### obtenidos vía simulador o QPUs (CUNQA).
###
### ========================================================= ###

from src.tensor_exp_value import (
    build_probability_tensor,
    run_with_probabilities,
    select_nodes_from_aux,
    combine_counts_shots,
    combine_counts_circuits
)
import numpy as np
import networkx as nx
from cunqa.qpu import get_QPUs, run
from cunqa.qjob import gather
from cunqa.qiskit_deps.transpiler import transpiler

from qiskit import QuantumCircuit, ClassicalRegister, transpile
from qiskit_aer import AerSimulator


def loss_func_estimator(
    x,
    alpha,
    beta,
    ansatz,
    sim,
    graph,
    list_size,
    num_qubits,
    d_t,
    n_shots,
    experiment_result,
    CUNQA: str,
    QPUs=None
):
    """
    Evalúa la función de pérdida usando un tensor de signos precomputado (d_t)
    y calculando el tensor de probabilidades a partir de counts simulados
    o paralelizados en QPUs.

    Parámetros
    ----------
    x : array-like
        Vector de parámetros del ansatz.
    alpha : float
        Escala para la función tanh en la pérdida.
    beta : float
        Escala del término de regularización.
    ansatz : list[QuantumCircuit]
        Lista de circuitos paramétricos para cada base (X, Y, Z).
    sim : Backend
        Simulador cuántico local.
    graph : nx.Graph
        Grafo sobre el que se calcula la función de coste.
    list_size : int
        Número de cadenas de Pauli de cada tipo.
    num_qubits : int
        Número total de qubits/nodos.
    d_t : np.ndarray
        Tensor de signos transpuesto (precomputado).
    n_shots : int
        Número de disparos para la simulación/ejecución en QPUs.
    experiment_result : list
        Lista para almacenar resultados intermedios de cada evaluación.
    CUNQA : str
        Modo de paralelización o None:
        - "Shots" → paralelización por cantidad de shots.
        - "Circuits" → paralelización por circuitos.
        - "Simulation" → simulación local.
    
    family_name : str, optional
        Nombre de la familia de QPUs levantadas con qraise (por defecto None).

    Retorna
    -------
    float
        Valor escalar de la función de pérdida.
    """

    ### ----------------------------------------------------- ###
    ### 1. Bind de parámetros en cada circuito
    ### ----------------------------------------------------- ###

    bound_circuit_list = [
        qc.assign_parameters({param: val for param, val in zip(qc.parameters, x)})
        for qc in ansatz
    ]
    
    ### ----------------------------------------------------- ###
    ### 2. Obtener counts y construir tensor de probabilidades
    ### ----------------------------------------------------- ###
    if CUNQA in ["Shots", "Circuits"]:

        if CUNQA == "Shots":
            if not QPUs:
                raise RuntimeError("No se encontraron QPUs disponibles")
            shots_per_qpu = [n_shots // len(QPUs)] * len(QPUs)
            shots_per_qpu[0] += n_shots % len(QPUs)
           

            qjobs = [
                run(qc, qpu, shots=shots, method="statevector")
                for qpu, shots in zip(QPUs, shots_per_qpu)
                for qc in bound_circuit_list
            ]
            results = gather(qjobs)
            counts_list = combine_counts_shots(
                results, n_qubits=num_qubits, n_circuits=3, num_qpus=len(QPUs)
            )[1]

        else:  # Circuits
            qjobs = [run(qc, qpu, shots=n_shots, method="statevector") for qc, qpu in zip(bound_circuit_list, QPUs)]
            results = gather(qjobs)

            counts_list = combine_counts_circuits(results, n_qubits=num_qubits)[1]

    elif CUNQA == "Simulation":

        def prepare_for_statevector(qc):
            """Elimina medidas y registros clásicos para poder obtener statevector"""
            qc_clean = qc.remove_final_measurements(inplace=False)
            for creg in qc_clean.cregs:
                qc_clean.remove_register(creg)
            # Guardamos el statevector
            qc_clean.save_statevector()
            return qc_clean

        # Preparamos los circuitos     
        # Ejecutar Z completo
        bound_circuit_z = prepare_for_statevector(bound_circuit_list[0])
        state_z = sim.run(bound_circuit_z).result().get_statevector(bound_circuit_z)

        # Probabilidades exactas
        probs_z = np.abs(state_z) ** 2

        # Ejecutar X e Y sobre statevector de Z

        # Ejecutar sobre initial_statevector=state_z
        # X: aplicar H
        qc_x = QuantumCircuit(num_qubits)
        qc_x.set_statevector(state_z)
        for q in range(num_qubits):
            qc_x.h(q)
        qc_x.save_statevector()
        state_x = sim.run(qc_x).result().get_statevector(qc_x)

        # Y: aplicar S† H
        qc_y = QuantumCircuit(num_qubits)
        qc_y.set_statevector(state_z)
        for q in range(num_qubits):
            qc_y.sdg(q)
            qc_y.h(q)
        qc_y.save_statevector()
        state_y = sim.run(qc_y).result().get_statevector(qc_y)


        # Probabilidades exactas
        probs_x = np.abs(state_x) ** 2
        probs_y = np.abs(state_y) ** 2

        # Lista en formato compatible con build_probability_tensor
        counts_list = [probs_x, probs_y, probs_z]

        # Para probabilities exactas, n_shots debe ser 1
        n_shots = 1

    p_t = build_probability_tensor(counts_list, n_shots,num_qubits)
    ### ----------------------------------------------------- ###
    ### 3. Calcular valores esperados usando d_t
    ### ----------------------------------------------------- ###
    aux = run_with_probabilities(d_t, p_t)["reshaped_result"]
    ### ----------------------------------------------------- ###
    ### 4. Selección de nodos de interés
    ### ----------------------------------------------------- ###
    m = graph.number_of_nodes()
    node_exp_map = select_nodes_from_aux(aux, m, list_size, return_concatenated=True)
    ### ----------------------------------------------------- ###
    ### 5. Cálculo de la función de pérdida
    ### ----------------------------------------------------- ###
    loss = sum(
        np.tanh(alpha * node_exp_map[edge0 - 1]) *
        np.tanh(alpha * node_exp_map[edge1 - 1])
        for edge0, edge1 in graph.edges()
    )
    ### ----------------------------------------------------- ###
    ### 6. Término de regularización
    ### ----------------------------------------------------- ###
    regulation_term = np.mean([np.tanh(alpha * node_exp_map[i]) ** 2
                               for i in range(num_qubits)]) ** 2
    v = compute_nu(graph)
    loss += beta * v * regulation_term

    ### ----------------------------------------------------- ###
    ### 7. Guardar resultados intermedios
    ### ----------------------------------------------------- ###
    experiment_result.append({"loss": loss, "exp_map": node_exp_map})

    return loss


 

def compute_nu(graph: nx.Graph | nx.MultiGraph) -> float:
    ordered_nodes = sorted(graph.nodes())
    adj_matrix = nx.to_numpy_array(graph, nodelist=ordered_nodes)
    # Check if the graph is weighted or not
    if np.any((adj_matrix != 0) & (adj_matrix != 1)):
        min_span_tree = nx.minimum_spanning_tree(graph)
        ordered_tree_nodes = sorted(min_span_tree.nodes())
        min_span_tree_matrix = nx.to_numpy_array(min_span_tree, nodelist=ordered_tree_nodes)
        # minimum spanning tree total weight
        tree_total_weight = np.sum(min_span_tree_matrix) / 2
        # graph total weight
        graph_weight = np.sum(adj_matrix) / 2
        # poljak-turzik lower bound
        nu = graph_weight / 2 + tree_total_weight / 4
    else:
        n_edges = len(graph.edges())
        n_nodes = len(graph.nodes())
        # edwars-erdos bound
        nu = n_edges / 2 + (n_nodes - 1) / 4
    return nu