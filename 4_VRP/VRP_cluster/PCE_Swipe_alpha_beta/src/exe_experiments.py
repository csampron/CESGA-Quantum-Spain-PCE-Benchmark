### ========================================================= ###
### Módulo: experiment_runner
### ========================================================= ###
###
### Funciones para:
### - Generar combinaciones de experimentos de MaxCut
### - Filtrar combinaciones según criterios
### - Ejecutar un experimento individual de MaxCut
### - Devolver rutas de salida generadas (CSV, iterativo)
###
### ========================================================= ###

def casuistica_experimento(Problema, Tamaño, Instancia, Optimiz, k):
    import itertools

    """
    Devuelve todas las combinaciones posibles de parámetros experimentales:
    - Problema (VRP)
    - Tamaño (nodos totales del VRP)
    - Instancia (1,2,...)
    - Optimización clásica
    - Parámetro k
    """
    return [
        [p, t, inst, o, kk]
        for p, t, inst, o, kk in itertools.product(Problema, Tamaño, Instancia, Optimiz, k)
    ]



def filtrar_combinaciones(combos, indice, valor):
    import itertools
    
    """
    Filtra una lista de combinaciones (listas de 4 elementos)
    devolviendo solo las que tienen 'valor' en la posición 'indice'.
    
    Parámetros:
      combos : list[list] -> lista de combinaciones
      indice : int        -> 0=Problema, 1=Tamaño, 2=Optimiz, 3=k
      valor  : any        -> valor a filtrar (ej. "COBYLA", 10, 2, ...)
    """
    return [c for c in combos if c[indice] == valor]

# ==== Ejemplo de uso ====
#Problema = ["MaxCut"]
#Tamaño = [10, 40, 100]
#Optimiz = ["COBYLA", "POWELL"]
#k = [2, 3]

#combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)

#for combo in combinaciones:
    #print(combo)


# ==== Ejemplo de uso ====
#solo_tamano_10 = filtrar_combinaciones(combinaciones, 1, 10)
#solo_cobyla = filtrar_combinaciones(combinaciones, 2, "COBYLA")

#print("Tamaño 10:", solo_tamano_10)
#print("COBYLA:", solo_cobyla)



import os
from pathlib import Path
import glob

def ejecutar_experimentos(exp_list, optimizer_params, alpha, beta, maxiter, n_shots, nqpus, cunqa_str, family_name, output_dir):
    """
    Ejecuta un experimento VRP resolviendo cada cluster como un TSP.

    Parámetros
    ----------
    exp_list : list
        [problema, tamaño, instancia, optimizador, k]
    optimizer_params : dict, opcional
        Diccionario de parámetros del optimizador
    alpha, beta, maxiter, n_shots, nqpus, cunqa_str, family_name : diversos
        Parámetros de ejecución de los TSP

    Retorna
    -------
    cluster_csv_paths      : list[str] → rutas a CSV finales de cada cluster
    cluster_csv_iter_paths : list[str] → rutas a CSV iterativos de cada cluster
    """

    import os, json
    from pathlib import Path
    from src.exe_tsp import ejecutar_tsp
    from src.op_graph import load_graph

    # --------------------------
    # 1️⃣ Extraer parámetros
    # --------------------------
    problema   = exp_list[0]  # "VRP"
    tamaño     = exp_list[1]  # ej: 4
    instancia  = exp_list[2]  # ej: 1
    optimizer  = exp_list[3]  # ej: "DIFFERENTIALEVOLUTION"
    k          = exp_list[4]  # parámetro k

    # --------------------------
    # 2️⃣ Ubicación de clusters
    # --------------------------
    parent = Path(__file__).resolve().parent
    clusters_dir = parent / f"graphs_clusters/{problema.lower()}_{tamaño}_{instancia}"

    if not clusters_dir.exists():
        raise FileNotFoundError(f"No se encontró el directorio de clusters: {clusters_dir}")

    # Buscar archivos .tsp de la instancia
    cluster_files = sorted(clusters_dir.glob(f"{problema.lower()}_{tamaño}_{instancia}_cluster_*.tsp"))
    if not cluster_files:
        raise FileNotFoundError(f"No se encontraron archivos .tsp en {clusters_dir}")

    # --------------------------
    # 3️⃣ Carpeta de resultados base
    # --------------------------
    result_base = Path(f"Resultados/{problema}/{cunqa_str}/{tamaño}_vertices/inst_{instancia}")
    result_base.mkdir(parents=True, exist_ok=True)

    cluster_results_summary = []
    cluster_csv_paths = []
    cluster_csv_iter_paths = []

    # --------------------------
    # 4️⃣ Ejecutar cada cluster secuencialmente
    # --------------------------
    for idx, cluster_file in enumerate(cluster_files):
        # Cargar grafo del cluster
        G_cluster, num_ver = load_graph(str(cluster_file))

        # Preparar parámetros del optimizador
        opt_params = optimizer_params.get(optimizer.upper(), None) if optimizer_params else None

        # Ejecutar TSP
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
            idx=idx,
            output_dir=output_dir # <-- propagar
        )

        # Guardar resumen del cluster
        cluster_results_summary.append({
            "cluster_index": idx,
            "refined_tour": dic_resultado["refined_tour"],
            "refined_distance": dic_resultado["refined_distance"]
        })

        # Guardar rutas CSV para uso posterior
        cluster_csv_paths.append(ruta_csv)
        cluster_csv_iter_paths.append(ruta_csv_iter)

    # --------------------------
    # 5️⃣ Guardar JSON global resumido
    # --------------------------
    total_cost = sum([c["refined_distance"] for c in cluster_results_summary])

    solucion_global = {
        "num_ver": tamaño,
        "instancia": instancia,
        "optimizer": optimizer,
        "total_cost": total_cost,
        "clusters": cluster_results_summary
    }

    if output_dir is not None:
        output_dir_json = Path(output_dir) / "Resultados"
    else:
        output_dir_json = result_base

    output_dir_json.mkdir(parents=True, exist_ok=True)
    solucion_json_path = output_dir_json / f"Sol_{tamaño}_vertices_inst_{instancia}.json"

    with open(solucion_json_path, "w") as f:
        json.dump(solucion_global, f, indent=2)

    # --------------------------
    # 6️⃣ Devolver listas de CSV y JSON
    # --------------------------
    return cluster_csv_paths, cluster_csv_iter_paths
