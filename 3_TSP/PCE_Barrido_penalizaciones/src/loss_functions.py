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
from cunqa.qutils import get_QPUs
from cunqa.qjob import gather

def loss_func_estimator(
    x,
    alpha,
    beta,
    A,
    B,
    ansatz,
    sim,
    graph,
    list_size,
    num_qubits,
    d_t,
    n_shots,
    experiment_result,
    CUNQA: str,
    family_name = None
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
    if CUNQA == "Shots":
        QPUs = get_QPUs(on_node=False, family=family_name)
        if not QPUs:
            raise ValueError("No se encontraron QPUs disponibles.")

        shots_per_qpu = [n_shots // len(QPUs)] * len(QPUs)
        shots_per_qpu[0] += n_shots % len(QPUs)

        qjobs = [qpu.run(qc, shots=par, method="statevector")
                 for par, qpu in zip(shots_per_qpu, QPUs)
                 for qc in bound_circuit_list]

        results = gather(qjobs)
        counts_list = combine_counts_shots(
            results,
            n_qubits=num_qubits,
            n_circuits=len(bound_circuit_list),
            num_qpus=len(QPUs)
        )[1]

    elif CUNQA == "Circuits":
        QPUs = get_QPUs(on_node=False, family=family_name)
        if not QPUs:
            raise ValueError("No se encontraron QPUs disponibles.")

        qjobs = [qpu.run(qc, shots=n_shots, method="statevector")
                 for qc, qpu in zip(bound_circuit_list, QPUs)]
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
        bound_circuit_x = prepare_for_statevector(bound_circuit_list[0])
        bound_circuit_y = prepare_for_statevector(bound_circuit_list[1])
       
        # Ejecutar Z completo
        bound_circuit_z = prepare_for_statevector(bound_circuit_list[2])
        state_z = sim.run(bound_circuit_z).result().get_statevector(bound_circuit_z)

        # Probabilidades exactas
        probs_z = np.abs(state_z) ** 2

        # Ejecutar X e Y sobre statevector de Z
        state_x = sim.run(bound_circuit_x, initial_statevector=state_z).result().get_statevector(bound_circuit_x)
        state_y = sim.run(bound_circuit_y, initial_statevector=state_z).result().get_statevector(bound_circuit_y)

        # Probabilidades exactas
        probs_x = np.abs(state_x) ** 2
        probs_y = np.abs(state_y) ** 2

        # Lista en formato compatible con build_probability_tensor
        counts_list = [probs_x, probs_y, probs_z]

        # Para probabilities exactas, n_shots debe ser 1
        n_shots = 1

    p_t = build_probability_tensor(counts_list, n_shots)

    ### ----------------------------------------------------- ###
    ### 3. Calcular valores esperados usando d_t
    ### ----------------------------------------------------- ###
    aux = run_with_probabilities(d_t, p_t)["reshaped_result"]

    ### ----------------------------------------------------- ###
    ### 4. Selección de nodos de interés
    ### ----------------------------------------------------- ###
    m = graph.number_of_nodes()
    node_exp_map = select_nodes_from_aux(aux, m**2, list_size, return_concatenated=True)

    # ------------------------------
    # 3. Variables cuánticas "relajadas" por ciudad
    # ------------------------------
    # --- 1. Relajación de las variables binaria x_{i,j} ~ [0,1] ---
    # node_exp_map -> dict {0: val0, 1: val1, ..., m-1: val_{m-1}}
    values = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    z_relaxed = np.tanh(alpha * values)

    def idx_ij(i, j):
        return i * m + j  # índice lineal

    def x_ij(i, j):
        # [0,1] desde [-1,1]
        return (z_relaxed[idx_ij(i,j)] + 1.0) / 2.0

    # --- 2. Coste del tour (relajado) ---
    #B = 1.0
    tsp_cost = 0.0
    
    cities = list(graph.nodes())
    #print("DEBUG: cities =", cities)
    #print("DEBUG: graph nodes =", list(graph.nodes()))
    #print("DEBUG: graph edges =", list(graph.edges(data=True)))

    for i in range(m):
        for j in range(m):
            p_next = (j + 1) % m  # posición siguiente
            for k in range(m):
                node_i = cities[i]
                node_k = cities[k]
                if node_i == node_k:
                    continue  # evitar aristas no existentes
                tsp_cost += B * graph[node_i][node_k]["weight"] * x_ij(i,j) * x_ij(k,p_next)
                

    # --- 3. Restricciones suavizadas ---
    # Cada ciudad aparece exactamente una vez
    constraint_city = 0.0
    for i in range(m):
        s = sum(x_ij(i,j) for j in range(m)) - 1
        constraint_city += s**2

    # Cada posición ocupada por exactamente una ciudad
    constraint_pos = 0.0
    for j in range(m):
        s = sum(x_ij(i,j) for i in range(m)) - 1
        constraint_pos += s**2

    # --- 4. Loss total ---
    #A = 1.0
    loss = tsp_cost + A * (constraint_city + constraint_pos)

    # ------------------------------
    # 8. Guardar resultados
    # ------------------------------
    experiment_result.append({"loss": loss, "exp_map": node_exp_map})
    #print(f"Iter {len(experiment_result)} — Loss = {loss}")

    return loss