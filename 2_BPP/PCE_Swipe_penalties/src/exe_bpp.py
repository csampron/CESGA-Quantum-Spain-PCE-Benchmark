### ========================================================= ###
### Módulo: exe_macut
### ========================================================= ###
###
### Funciones para:
### - Ejecutar experimentos de BinPackigProblem con ansatz cuántico variacional (VQE)
### - Compilar circuitos y medir en bases X, Y, Z
### - Optimización clásica y refinamiento local
### - Guardar resultados parciales y finales en CSV/JSON
###
### ========================================================= ###

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

def ejecutar_bpp(
    Capacity,
    Weights,
    num_items,
    optimizer,
    optimizer_params,
    k,
    alpha,
    beta,
    lambda_1,
    lambda_2,
    lambda_3,
    maxiter,
    n_shots,
    nqpus,
    cunqa_str_arg,
    family_name,
    output_dir
):
    """
    Ejecuta un experimento de BPP utilizando un circuito cuántico variacional (VQE).
    Construye el circuito, ejecuta la optimización, guarda resultados parciales en JSON/CSV
    y devuelve los resultados de la ejecución.
    """

    # === IMPORTS INTERNOS ===
    import math
    import time
    
    from qiskit import transpile, QuantumCircuit
    from qiskit_aer import AerSimulator
    from qiskit.transpiler.preset_passmanagers import generate_preset_pass_manager
    from qiskit import ClassicalRegister
   
    import os

    # Módulos del proyecto
    from src.loss_functions import loss_func_estimator
    from .auxiliar import (
    num_qubits,
    build_bpp_solution_from_expmap,
    postprocess_bins,
    )
    from src.utilities import (run_vqe_optimization)
    from src.circuit_builder import Circuit
    from src.tensor_exp_value import build_sign_tensor
    
    # === 1. Cargar el archivo del problema ===
    print(f"Capacidad bins: {Capacity}, Número de items: {num_items}")

    # === 2. Definir número de qubits y capas del circuito ===
    
    m = num_items**2 # Máximo de variables necesarias en el peor de los caso

    qubits = num_qubits(m, k)
    if qubits == num_items:
        qubits = qubits + 1
    
    layers = (m) ** (1 - (1 / k))                 # fórmula para el número de capas

    #layers = 2 

    num_layers = math.ceil(layers)                    # redondeo al entero superior

    # === 3. Construir codificaciones de Pauli ===
    # Se dividen los nodos en tres subconjuntos (X, Y, Z)
    list_size = (m) // 3
    
    # === 4. Crear y compilar el circuito cuántico ===
    sim = AerSimulator()   # simulador de Qiskit Aer
    

    # Constructor del circuito con los parámetros del experimento
    qc_builder = Circuit(
        size=qubits,
        p=num_layers,
        entanglement='Taylor_efficient',
        rotation='Taylor_efficient',
        connectivity='brickwork_single_rotating'
    )
    qc_builder.compile_circuit()          # construir el circuito
    qc = qc_builder.get_circuit()         # obtener el circuito final

    if cunqa_str_arg != "Simulation":

        # --- Crear copias del circuito original para medir en cada base ---
        qc_z = qc.copy()  # Para términos Z
        qc_x = qc.copy()  # Para términos X
        qc_y = qc.copy()  # Para términos Y

        sim = AerSimulator(seed_simulator=33)   # simulador de Qiskit Aer
        # --- Añadir rotaciones de base y medidas solo si no es Simulation ---
        
        # Z: medir directamente
        cr_z = ClassicalRegister(qubits)
        qc_z.add_register(cr_z)
        qc_z.measure(range(qubits), range(qubits))

        # X: aplicar H antes de medir
        for q in range(qubits):
            qc_x.h(q)
        cr_x = ClassicalRegister(qubits)
        qc_x.add_register(cr_x)
        qc_x.measure(range(qubits), range(qubits))

        # Y: aplicar S† H antes de medir
        for q in range(qubits):
            qc_y.sdg(q)
            qc_y.h(q)
        cr_y = ClassicalRegister(qubits)
        qc_y.add_register(cr_y)
        qc_y.measure(range(qubits), range(qubits))

        # --- Compilación (optimización) de cada circuito para el backend ---
        pm = generate_preset_pass_manager(optimization_level=2, backend=sim)

        compiled_z = pm.run(qc_z)
        compiled_x = pm.run(qc_x)
        compiled_y = pm.run(qc_y)

        #compiled_z = transpile(qc_z, sim, optimization_level=2)
        #compiled_x = transpile(qc_x, sim, optimization_level=2)
        #compiled_y = transpile(qc_y, sim, optimization_level=2)

        # --- Unir los compilados en una lista (o dict) ---
        compiled_circuit = [compiled_x, compiled_y, compiled_z]

    else:
        sim = AerSimulator(method="statevector", seed_simulator=33)
        
        # --- Crear copias del circuito original para medir en cada base ---
        qc_z = qc.copy()  # Para términos Z

        # --- Si es Simulation, solo aplicar rotaciones de base ---
    

        # --- Transpilar para el backend statevector ---
        compiled_z = transpile(qc_z, sim, optimization_level=0)

        # --- Unir los compilados en una lista (o dict) ---
        compiled_circuit = [compiled_z]

    # --- Construimos el tensor de signo ---
    d_t = build_sign_tensor(n_circuits = 3, n_qubits = qubits, k_degree = k)

    
    # === 5. Ejecutar la optimización VQE ===
    start_time = time.time()

    # Si se proporcionó output_dir (viene de run_params), úsalo como raíz.
    # Sino, mantener la lógica antigua (para compatibilidad).
    if output_dir is not None:
        # Crear rutas relativas dentro de output_dir
        # p.ej. ./Experimentos/.../alpha_..../Resultados/...
        # Puedes organizarlo como prefieras; aquí lo dejamos sencillo:
        subcarpeta = os.path.join(output_dir, "Resultados")
        if not os.path.isdir(subcarpeta):
            os.makedirs(subcarpeta, exist_ok=True)
        
        nombre_archivo_csv = f"BPP{num_items}_{optimizer}_{k}.csv"
        nombre_archivo_csv_iter =f"BPP{num_items}_{optimizer}_{k}_iter.csv"
        ruta_csv = os.path.join(subcarpeta, nombre_archivo_csv)
        ruta_csv_iter = os.path.join(subcarpeta, nombre_archivo_csv_iter)
    # lógica original existente (compatibilidad)
    else:
        # lógica original existente (compatibilidad)
        if cunqa_str_arg == "Simulation":
            subcarpeta = f"Resultados/BPP/{cunqa_str_arg}/{num_items}_items/{optimizer}"
        else:
            subcarpeta = f"Resultados/BPP/{cunqa_str_arg}/{nqpus}qpus/{num_items}_items/{optimizer}"

        nombre_archivo_csv = f"BPP{num_items}_{optimizer}_{k}.csv"    
        nombre_archivo_csv_iter =f"BPP{num_items}_{optimizer}_{k}_iter.csv"
        ruta_csv = os.path.join(subcarpeta, nombre_archivo_csv)
        ruta_csv_iter = os.path.join(subcarpeta, nombre_archivo_csv_iter)

        # Ejecutar el proceso de optimización variacional
    result, experiment_result = run_vqe_optimization(
        sim=sim,
        n_shots=n_shots,
        alpha=alpha,
        beta=beta,
        lambda_1=lambda_1,
        lambda_2=lambda_2,
        lambda_3=lambda_3,
        compiled_circuit=compiled_circuit,
        Capacity=Capacity,
        Weights=Weights,
        num_items=num_items,
        list_size=list_size,
        d_t = d_t,
        optimizer=optimizer,
        optimizer_params= optimizer_params,
        loss_func_estimator=loss_func_estimator,
        maxiter=maxiter,
        log_csv_path=ruta_csv,
        cunqa_str=cunqa_str_arg,
        family_name = family_name
    )


        
    # === 6. Obtener y construir la solución de Bin Packing ===

    # A partir del mapa de expectativas del último experimento
    min_loss = min(e["loss"] for e in experiment_result)
    best = next(
        e for e in reversed(experiment_result)
        if e["loss"] == min_loss
    )   
    exp_map_final = best["exp_map"]

    # Convertir expectativas → asignación de ítems a bins
    bins_solution, reconstruction_info, status_initial, candidate_info, x_values = (
        build_bpp_solution_from_expmap(
            exp_map_final,
            alpha,
            Weights,
            Capacity
        )
    )

    # ------------------------------------------------------------
    # Mostrar solución inicial
    # ------------------------------------------------------------

    print(f"\nEstado reconstrucción inicial: {status_initial}")

    if bins_solution is not None:

        num_bins_used = len(bins_solution)

        print("\nSolución Bin Packing (BPP) sin postprocesado:")

        for idx, b in enumerate(bins_solution):
            total_weight = sum(int(Weights[i]) for i in b)
            print(f"  Bin {idx}: items {b}  |  peso = {total_weight}")

        print(f"\nNúmero total de bins usados: {num_bins_used}\n")

    else:

        num_bins_used = None

        print("\nNo se encontró solución factible inicial.")
        print(f"Items sin candidato: {reconstruction_info.get('unassigned_items', [])}")
        print(f"Items ambiguos: {reconstruction_info.get('ambiguous_items', [])}")
        print(f"Número de combinaciones evaluadas: {reconstruction_info.get('num_combinations', 0)}")
        print(f"Soluciones factibles encontradas: {reconstruction_info.get('feasible_solutions', 0)}")

    # ------------------------------------------------------------
    # Ejecutar postprocesado
    # ------------------------------------------------------------

    bins_post = postprocess_bins(
        bins_solution,
        Weights,
        Capacity
    )

    if bins_post is not None:

        num_bins_used_post = len(bins_post)

        print("\nSolución Bin Packing (BPP) tras postprocesado:")

        for idx, b in enumerate(bins_post):
            total_weight = sum(int(Weights[i]) for i in b)
            print(f"  Bin {idx}: items {b}  |  peso = {total_weight}")

        print(f"\nNúmero total de bins tras postprocesado: {num_bins_used_post}")

    else:

        num_bins_used_post = None

        print("\nNo se ejecutó postprocesado porque no había solución inicial factible.")

    # ------------------------------------------------------------
    # Tiempo total
    # ------------------------------------------------------------

    end_time = time.time()
    elapsed = end_time - start_time

    print(f"⏱️ Tiempo total de ejecución: {elapsed:.2f} segundos")

    print("bins_solution:", bins_solution)
    print("bins_post:", bins_post)
    print([type(b) for b in bins_post] if bins_post is not None else None)


    # === 7. Recolectar resultados finales de la optimización ===

    params = result.x
    num_params = len(params)

    fevs = getattr(result, "nfev", None)
    fvalue = result.fun

    if optimizer.lower() != "cobyla":
        nit = getattr(result, "nit", None)
    else:
        nit = None

    # ------------------------------------------------------------
    # Diccionario final
    # ------------------------------------------------------------

    dic_resultado = {
        "qubits": qubits,
        "elapsed_time": elapsed,

        "alpha": alpha,
        "beta": beta,

        "f_loss_value": fvalue,
        "function_evaluations": fevs,
        "Number of iterations": nit,
        "num_params": num_params,
        "params": params.tolist(),

        # Estado de reconstrucción
        "status_initial": status_initial,

        # Información de reconstrucción desde exp_map
        "reconstruction_info": reconstruction_info,
        "candidate_info": candidate_info,
        "x_values": x_values,

        # Solución inicial
        "bins_solution": bins_solution,
        "num_bins_used": num_bins_used,

        # Solución postprocesada
        "bins_solution_post": bins_post,
        "num_bins_used_post": num_bins_used_post,

        "optimizer_message": getattr(result, "message", ""),
        "optimizer_status": getattr(result, "status", "")
    }

    print("El programa ha finalizado ✅\n")

    # === 8. Guardar en JSON ===
    if output_dir is not None:
        # Guardamos JSON dentro de la carpeta del experimento (p.ej. output_dir/Resultados/)
        nombre_archivo = f"BPP{num_items}_{optimizer}_{k}.json"
        ruta_archivo = os.path.join(subcarpeta, nombre_archivo)
    else:
        if cunqa_str_arg == "Simulation":
            subcarpeta = f"Resultados/BPP/{cunqa_str_arg}/{num_items}_items/{optimizer}"
        else:
            subcarpeta = f"Resultados/BPP/{cunqa_str_arg}/{nqpus}qpus/{num_items}_items/{optimizer}/"
        
        nombre_archivo = f"BPP{num_items}_{optimizer}_{k}.json"

        if not os.path.isdir(subcarpeta):
            os.makedirs(subcarpeta, exist_ok=True)
        ruta_archivo = os.path.join(subcarpeta, nombre_archivo)

    # Usa append_result_to_json sobre la ruta final    
    append_result_to_json(ruta_archivo, dic_resultado)
        

    # === 10. Devolver resultado individual y ruta del experimento ===
    return dic_resultado, subcarpeta, ruta_csv, ruta_csv_iter



