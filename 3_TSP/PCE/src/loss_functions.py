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
    A_1,
    A_2,
    gamma,
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
        # Ejecutar Z completo
        bound_circuit_z = prepare_for_statevector(bound_circuit_list[0])
        state_z = sim.run(bound_circuit_z).result().get_statevector(bound_circuit_z)

        # Probabilidades exactas
        probs_z = np.abs(state_z) ** 2

        # Ejecutar X e Y sobre statevector de Z
        from qiskit import QuantumCircuit

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
    # ---------------------------------------------------------
    # TSP QUBO/PCE con nodo fijo
    # ---------------------------------------------------------

    # Número total de nodos del grafo
    N = graph.number_of_nodes()

    # Lista original de ciudades
    cities = list(graph.nodes())

    # ---------------------------------------------------------
    # 1. Fijar nodo de referencia
    # ---------------------------------------------------------
    fixed_node = cities[0]

    # Ciudades que sí se optimizan
    free_cities = [c for c in cities if c != fixed_node]

    # Ahora m = N-1
    m = len(free_cities)

    # ---------------------------------------------------------
    # 2. Selección de variables auxiliares
    # ---------------------------------------------------------
    # Ahora hay (N-1)^2 variables binarias
    node_exp_map = select_nodes_from_aux(aux, m**2, list_size, return_concatenated=True)

    # ---------------------------------------------------------
    # 3. Variables relajadas
    # ---------------------------------------------------------
    values = np.array([node_exp_map[i] for i in range(len(node_exp_map))])

    # z in [-1,1]
    z_relaxed = np.tanh(alpha * values)

    # ---------------------------------------------------------
    # 4. Indexado
    # ---------------------------------------------------------
    def idx_ij(i, j):
        return i * m + j

    def x_ij(i, j):
        # map [-1,1] -> [0,1]
        return (z_relaxed[idx_ij(i, j)] + 1.0) / 2.0

    # ---------------------------------------------------------
    # 5. Coste del TSP
    # ---------------------------------------------------------
    B_0 = 1.0
    tsp_cost = 0.0

    # ---------------------------------------------------------
    # 5A. Costes entre ciudades consecutivas
    # ---------------------------------------------------------
    for i in range(m):

        node_i = free_cities[i]

        for k in range(m):

            if i == k:
                continue

            node_k = free_cities[k]

            # posiciones consecutivas
            for p in range(m - 1):

                tsp_cost += ( B_0 * graph[node_i][node_k]["weight"] * x_ij(i, p) * x_ij(k, p + 1) )

    # ---------------------------------------------------------
    # 5B. Conexión con nodo fijo
    # ---------------------------------------------------------
    # fixed_node -> primera ciudad
    # última ciudad -> fixed_node

    for i in range(m):

        node_i = free_cities[i]

        w = graph[fixed_node][node_i]["weight"]

        # inicio del tour
        tsp_cost += B_0 * w * x_ij(i, 0)

        # final del tour
        tsp_cost += B_0 * w * x_ij(i, m - 1)

    # ---------------------------------------------------------
    # 6. Restricciones
    # ---------------------------------------------------------

    # 6.a) Cada ciudad aparece exactamente una vez
    constraint_city = 0.0

    for i in range(m):

        s = sum(x_ij(i, j) for j in range(m)) - 1

        constraint_city += s**2

    # 6.b) Cada posición contiene exactamente una ciudad
    constraint_pos = 0.0

    for j in range(m):

        s = sum(x_ij(i, j) for i in range(m)) - 1

        constraint_pos += s**2

    # ---------------------------------------------------------
    # 6.1 NUEVO: término de competencia intra-columna (QUBO clave)
    # ---------------------------------------------------------

    collision_col = 0.0

    for j in range(m):
        for i in range(m):
            for k in range(i + 1, m):
                collision_col += x_ij(i, j) * x_ij(k, j)

    
    
    # ---------------------------------------------------------
    # 7. Loss total
    # ---------------------------------------------------------
    

    loss = tsp_cost + A_1 * constraint_city + A_2 * constraint_pos + gamma * collision_col

    # ---------------------------------------------------------
    # 8. Regularización
    # ---------------------------------------------------------
    reg_term = np.mean(z_relaxed**2)

    v = 1.0

    loss += beta * v * reg_term

    # ------------------------------
    # 8. Guardar resultados
    # ------------------------------
    experiment_result.append({"loss": loss, "exp_map": node_exp_map})
    #print(f"Iter {len(experiment_result)} — Loss = {loss}")

    return loss