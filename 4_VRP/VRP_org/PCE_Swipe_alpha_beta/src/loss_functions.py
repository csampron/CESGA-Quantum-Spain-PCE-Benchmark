### ========================================================= ###
### Función: loss_func_estimator
### ========================================================= ###
###
### Evalúa la función de pérdida (loss) para un conjunto de parámetros
### de un ansatz cuántico, usando tensores precomputados y counts
### obtenidos vía simulador o QPUs (CUNQA).
###
### ========================================================= ###

def loss_func_estimator(
    x,
    alpha,
    beta,
    ansatz,
    sim,
    graph,
    Capacity,
    list_size,
    num_qubits,
    d_t,
    n_shots,
    experiment_result,
    CUNQA: str,
    family_name = None
):

    from src.tensor_exp_value import (
        build_probability_tensor,
        run_with_probabilities,
        select_nodes_from_aux
    )
    import numpy as np

    # =====================================================
    # 1. Bind parámetros
    # =====================================================
    bound_circuit_list = [
        qc.assign_parameters({param: val for param, val in zip(qc.parameters, x)})
        for qc in ansatz
    ]

    # =====================================================
    # 2. Probabilidades (solo simulation aquí para claridad)
    # =====================================================
    def prepare_for_statevector(qc):
        qc_clean = qc.remove_final_measurements(inplace=False)
        for creg in qc_clean.cregs:
            qc_clean.remove_register(creg)
        qc_clean.save_statevector()
        return qc_clean

    bound_circuit_z = prepare_for_statevector(bound_circuit_list[0])
    state_z = sim.run(bound_circuit_z).result().get_statevector(bound_circuit_z)
    probs_z = np.abs(state_z) ** 2

    from qiskit import QuantumCircuit

    qc_x = QuantumCircuit(num_qubits)
    qc_x.set_statevector(state_z)
    for q in range(num_qubits):
        qc_x.h(q)
    qc_x.save_statevector()
    state_x = sim.run(qc_x).result().get_statevector(qc_x)
    probs_x = np.abs(state_x) ** 2

    qc_y = QuantumCircuit(num_qubits)
    qc_y.set_statevector(state_z)
    for q in range(num_qubits):
        qc_y.sdg(q)
        qc_y.h(q)
    qc_y.save_statevector()
    state_y = sim.run(qc_y).result().get_statevector(qc_y)
    probs_y = np.abs(state_y) ** 2

    counts_list = [probs_x, probs_y, probs_z]
    n_shots = 1

    p_t = build_probability_tensor(counts_list, n_shots, num_qubits)

    # =====================================================
    # 3. Valores esperados
    # =====================================================
    aux = run_with_probabilities(d_t, p_t)["reshaped_result"]

    # =====================================================
    # 4. Variables relajadas
    # =====================================================
    n_nodes = graph.number_of_nodes()
    A = n_nodes
    n_steps = n_nodes + 1  # ahora correctamente
    depot = 0

    node_exp_map = select_nodes_from_aux(aux, A * n_nodes * n_steps, list_size, return_concatenated=True)

    exp_array = np.array([node_exp_map[i] for i in range(len(node_exp_map))])
    z_relaxed = np.tanh(alpha * exp_array)
    x_relaxed = (z_relaxed + 1.0) / 2.0

    def idx_avs(a, v, s):
        return a * (n_nodes * n_steps) + v * n_steps + s

    # =====================================================
    # 5. Q1: coste rutas
    # =====================================================
    H_A = 0.0
    for a in range(A):
        for s in range(n_steps - 1):
            for i in range(n_nodes):
                for j in range(n_nodes):
                    if i != j:
                        H_A += graph[i][j]["weight"] * x_relaxed[idx_avs(a,i,s)] * x_relaxed[idx_avs(a,j,s+1)]

    # =====================================================
    # 6. Q2: cada cliente visitado exactamente una vez
    # =====================================================
    H_B = 0.0
    for v in range(1, n_nodes):
        visit_sum = sum(x_relaxed[idx_avs(a,v,s)] for a in range(A) for s in range(n_steps))
        H_B += (1 - visit_sum)**2

    # =====================================================
    # 7. Q3: inicio = fin
    # =====================================================
    H_3 = 0.0
    for a in range(A):
        H_3 += (x_relaxed[idx_avs(a,depot,0)] - x_relaxed[idx_avs(a,depot,n_steps-1)])**2

    # =====================================================
    # 8. Q4: capacidad
    # =====================================================
    C = Capacity
    H_4 = 0.0
    for a in range(A):
        load_sum = sum(x_relaxed[idx_avs(a,i,s)] for i in range(1,n_nodes) for s in range(n_steps))
        H_4 += (load_sum - C * x_relaxed[idx_avs(a,depot,0)])**2

    # =====================================================
    # 9. Q5: consistencia de pasos
    # =====================================================
    H_5 = 0.0
    for a in range(A):
        for s in range(n_steps):
            step_sum = sum(x_relaxed[idx_avs(a,i,s)] for i in range(n_nodes))
            H_5 += (x_relaxed[idx_avs(a,depot,0)] - step_sum)**2

    # =====================================================
    # 10. Loss total
    # =====================================================
    lamda_B = 1000  # cliente no visitado = gran penalización
    lamda_3 = 10    # inicio/fin mal = penalización moderada
    lamda_4 = 100   # capacidad violada = penalización fuerte
    lamda_5 = 100    # pasos inconsistentes = penalización baja

    loss = H_A + lamda_B*H_B + lamda_3*H_3 + lamda_4*H_4 + lamda_5*H_5

    # Término de regularización sobre z_relaxed:
    reg_term = np.mean(z_relaxed**2)   # valores cercanos a ±1 contribuyen más

    # Escalador del grafo para ajustar magnitud
    v = 100
    # Añadir al loss total
    loss += beta * v * reg_term

    experiment_result.append({"loss": loss, "exp_map": node_exp_map})
    return loss