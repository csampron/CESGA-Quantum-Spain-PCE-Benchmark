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
    ansatz,
    sim,
    graph,
    C,
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

    p_t = build_probability_tensor(counts_list, n_shots, num_qubits)

    ### ----------------------------------------------------- ###
    ### 3. Calcular valores esperados usando d_t
    ### ----------------------------------------------------- ###
    aux = run_with_probabilities(d_t, p_t)["reshaped_result"]

    ### ----------------------------------------------------- ###
    ### 5. Parámetros del problema VRP
    ### ----------------------------------------------------- ###

    n_nodes = graph.number_of_nodes()
    depot = 0
    # número de vehículos FIJO
    A = 2
    # número total de variables:
    #
    # m = 2 * N * (N-1)
    #
    n_vars = A * n_nodes * (n_nodes - 1)

    # capacidad objetivo por defecto
    if C is None:
        C = n_nodes // A

    ### ----------------------------------------------------- ###
    ### 6. Seleccionar variables relevantes
    ### ----------------------------------------------------- ###

    node_exp_map = select_nodes_from_aux(
        aux,
        n_vars,
        list_size,
        return_concatenated=True
    )

    ### ----------------------------------------------------- ###
    ### 7. Variables relajadas en [0,1]
    ### ----------------------------------------------------- ###

    exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    ### ----------------------------------------------------- ###
    ### 8. Indexado compacto de x_{aij}
    ### ----------------------------------------------------- ###
    ###
    ### Eliminamos self-loops:
    ###
    ###     i != j
    ###
    ### Variables por vehículo:
    ###
    ###     N * (N-1)
    ###
    ### ----------------------------------------------------- ###

    def idx_aij(a, i, j):

        if i == j:
            raise ValueError("Self-loops no permitidos")

        offset = j if j < i else j - 1

        return (
            a * (n_nodes * (n_nodes - 1))
            + i * (n_nodes - 1)
            + offset
        )

    ### ===================================================== ###
    ### Q1 : Coste total
    ### ===================================================== ###

    Q1 = 0.0

    for a in range(A):

        for i in range(n_nodes):

            for j in range(n_nodes):

                if i == j:
                    continue

                Q1 += (
                    graph[i][j]["weight"]
                    * x_relaxed[idx_aij(a, i, j)]
                )

    ### ===================================================== ###
    ### Q2 : Cada cliente tiene
    ###      una entrada y una salida
    ### ===================================================== ###

    Q2 = 0.0

    for i in range(1, n_nodes):

        # ----------------------------------------------------
        # Salidas del nodo i
        # ----------------------------------------------------

        outgoing_sum = 0.0

        for a in range(A):

            for j in range(n_nodes):

                if j == i:
                    continue

                outgoing_sum += x_relaxed[
                    idx_aij(a, i, j)
                ]

        Q2 += (1.0 - outgoing_sum) ** 2

        # ----------------------------------------------------
        # Entradas al nodo i
        # ----------------------------------------------------

        incoming_sum = 0.0

        for a in range(A):

            for j in range(n_nodes):

                if j == i:
                    continue

                incoming_sum += x_relaxed[
                    idx_aij(a, j, i)
                ]

        Q2 += (1.0 - incoming_sum) ** 2

    ### ===================================================== ###
    ### Q3 : Salida y retorno al depósito
    ### ===================================================== ###

    Q3 = 0.0

    # --------------------------------------------------------
    # Salidas del depósito
    # --------------------------------------------------------

    depot_out = 0.0

    for a in range(A):

        for j in range(1, n_nodes):

            depot_out += x_relaxed[
                idx_aij(a, depot, j)
            ]

    Q3 += (2.0 - depot_out) ** 2

    # --------------------------------------------------------
    # Entradas al depósito
    # --------------------------------------------------------

    depot_in = 0.0

    for a in range(A):

        for i in range(1, n_nodes):

            depot_in += x_relaxed[
                idx_aij(a, i, depot)
            ]

    Q3 += (2.0 - depot_in) ** 2

    ### ===================================================== ###
    ### Q4 : Conservación de flujo
    ### ===================================================== ###

    Q4 = 0.0

    for a in range(A):

        for j in range(1, n_nodes):

            flow_balance = 0.0

            for i in range(n_nodes):

                if i == j:
                    continue

                flow_balance += (
                    x_relaxed[idx_aij(a, i, j)]
                    - x_relaxed[idx_aij(a, j, i)]
                )

            Q4 += flow_balance ** 2

    ### ===================================================== ###
    ### Q5 : Restricción de capacidad
    ### ===================================================== ###

    Q5 = 0.0

    for a in range(A):

        vehicle_load = 0.0

        for i in range(1, n_nodes):

            for j in range(n_nodes):

                if i == j:
                    continue

                vehicle_load += x_relaxed[
                    idx_aij(a, i, j)
                ]

        Q5 += (vehicle_load - C) ** 2


    ### ===================================================== ###
    ### Término de regularización
    ### ===================================================== ###
        
    # Término de regularización sobre z_relaxed:
    reg_term = np.mean(z_relaxed**2)   # valores cercanos a ±1 contribuyen más

    # Escalador del grafo para ajustar magnitud
    v = 100
    # Añadir al loss total

    ### ----------------------------------------------------- ###
    ### 9. Loss total
    ### ----------------------------------------------------- ###
    lambda_1 = 1.0
    lambda_2 = 100.0
    lambda_3 = 100.0
    lambda_4 = 100.0
    lambda_5 = 100.0

    
    loss = (
        lambda_1 * Q1
        + lambda_2 * Q2
        + lambda_3 * Q3
        + lambda_4 * Q4
        + lambda_5 * Q5
        + reg_term
    )

    ### ----------------------------------------------------- ###
    ### 10. Guardar resultados
    ### ----------------------------------------------------- ###

    experiment_result.append({"loss": loss, "exp_map": node_exp_map})
    return loss