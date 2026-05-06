### ========================================================= ###
### Módulo: experiment_runner
### ========================================================= ###
###
### Funciones para:
### - Generar combinaciones de experimentos de VRP
### - Filtrar combinaciones según criterios
### - Ejecutar un experimento VRP por clusters
### - Guardar resultados acumulados en JSON
###
### ========================================================= ###


# ============================================================
# Generación de combinaciones experimentales
# ============================================================

def casuistica_experimento(Problema, Tamaño, Instancia, Optimiz, k):
    import itertools
    """
    Devuelve todas las combinaciones posibles de parámetros experimentales
    """
    return [
        [p, t, inst, o, kk]
        for p, t, inst, o, kk in itertools.product(
            Problema, Tamaño, Instancia, Optimiz, k
        )
    ]


def filtrar_combinaciones(combos, indice, valor):
    """
    Filtra combinaciones por valor en una posición concreta
    """
    return [c for c in combos if c[indice] == valor]


# ============================================================
# Función auxiliar: append seguro de resultados VRP
# ============================================================

def append_experiment_result_vrp(json_path, solucion_global):
    """
    Añade un experimento VRP al JSON sin sobrescribir resultados previos.
    """
    import json
    from pathlib import Path

    json_path = Path(json_path)

    # Si el archivo no existe, lo inicializamos
    if not json_path.exists():
        data = {
            "experiments": []
        }
    else:
        with open(json_path, "r") as f:
            data = json.load(f)

        if "experiments" not in data:
            data["experiments"] = []

    # Añadir nuevo experimento
    data["experiments"].append(solucion_global)

    # Guardar
    with open(json_path, "w") as f:
        json.dump(data, f, indent=2)


# ============================================================
# Ejecutor principal de experimentos VRP
# ============================================================

def ejecutar_experimentos(
    exp_list,
    optimizer_params,
    alpha,
    beta,
    maxiter,
    n_shots,
    nqpus,
    cunqa_str,
    family_name
):
    """
    Ejecuta un experimento VRP resolviendo cada cluster como un TSP
    y acumula resultados en un JSON.
    """

    import json
    from pathlib import Path
    from src.exe_tsp import ejecutar_tsp
    from src.op_graph import load_graph

    # --------------------------
    # 1️⃣ Extraer parámetros
    # --------------------------
    problema   = exp_list[0]
    tamaño     = exp_list[1]
    instancia  = exp_list[2]
    optimizer  = exp_list[3]
    k          = exp_list[4]

    # --------------------------
    # 2️⃣ Ubicación de clusters
    # --------------------------
    parent = Path(__file__).resolve().parent
    clusters_dir = parent / f"graphs_clusters/{problema.lower()}_{tamaño}_{instancia}"

    if not clusters_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio: {clusters_dir}")

    cluster_files = sorted(
        clusters_dir.glob(f"{problema.lower()}_{tamaño}_{instancia}_cluster_*.tsp")
    )

    if not cluster_files:
        raise FileNotFoundError(f"No hay archivos .tsp en {clusters_dir}")

    # --------------------------
    # 3️⃣ Carpeta base de resultados
    # --------------------------
    result_base = Path(
        f"Resultados/{problema}/{cunqa_str}/k{k}/{tamaño}_vertices/inst_{instancia}"
    )
    result_base.mkdir(parents=True, exist_ok=True)

    cluster_results_summary = []
    cluster_csv_paths = []
    cluster_csv_iter_paths = []

    # --------------------------
    # 4️⃣ Ejecutar cada cluster
    # --------------------------
    for idx, cluster_file in enumerate(cluster_files):
        G_cluster, num_ver = load_graph(str(cluster_file))

        opt_params = (
            optimizer_params.get(optimizer.upper(), None)
            if optimizer_params else None
        )

        dic_resultado, subcarpeta, ruta_csv, ruta_csv_iter = ejecutar_tsp(
            G=G_cluster,
            optimizer=optimizer,
            optimizer_params=opt_params,
            num_ver=num_ver,
            k=k,
            alpha=alpha,
            beta=beta,
            maxiter=maxiter,
            n_shots=n_shots,
            nqpus=nqpus,
            cunqa_str_arg=cunqa_str,
            family_name=family_name,
            tamaño=tamaño,
            instancia=instancia,
            idx=idx
        )

        cluster_results_summary.append({
            "cluster_index": idx,
            "refined_tour": dic_resultado["refined_tour"],
            "refined_distance": dic_resultado["refined_distance"]
        })

        cluster_csv_paths.append(ruta_csv)
        cluster_csv_iter_paths.append(ruta_csv_iter)

    # --------------------------
    # 5️⃣ Guardar resultados globales (APPEND)
    # --------------------------
    total_cost = sum(c["refined_distance"] for c in cluster_results_summary)

    solucion_global = {
        "num_ver": tamaño,
        "instancia": instancia,
        "optimizer": optimizer,
        "k": k,
        "total_cost": total_cost,
        "clusters": cluster_results_summary
    }

    solucion_json_path = (
        result_base / f"Sol_{tamaño}_vertices_inst_{instancia}.json"
    )

    append_experiment_result_vrp(solucion_json_path, solucion_global)

    # --------------------------
    # 6️⃣ Retorno
    # --------------------------
    return cluster_csv_paths, cluster_csv_iter_paths
