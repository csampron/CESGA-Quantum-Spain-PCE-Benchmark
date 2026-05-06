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

def casuistica_experimento(Problema, Tamaño, Optimiz, k):
    import itertools

    """
    Devuelve una lista de listas con todas las combinaciones posibles
    de los valores de Problema, Tamaño, Optimiz y k.
    """
    return [
        [p, t, o, kk]
        for p, t, o, kk in itertools.product(Problema, Tamaño, Optimiz, k)
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



def ejecutar_experimentos(exp_list, optimizer_params, alpha, beta, maxiter, n_shots, nqpus, cunqa_str, family_name):   
    """
    Ejecuta un experimento de MaxCut para una combinación de parámetros dada.

    Parámetros
    ----------
    exp_list : list
        Lista con la estructura:
        [problema, tamaño, optimizador, k]
        donde:
            - problema: nombre del problema (ej., "MaxCut")
            - tamaño: número de vértices del grafo
            - optimizador: optimizador clásico a usar
            - k: parámetro del modelo (ej., compresión)
    

    optimizer_params: dict, opcional
        Diccionario de parámetros por optimizador, e.g.:
        {"POWELL": {...}, "DIFFERENTIALEVOLUTION": {...}}
        Si no se pasa, se usan los valores por defecto.
         

    alpha : float
        Peso del término principal de la función de coste (este valor será ignorado internamente,
        ya que la función vuelve a calcular alpha en base al número de qubits).  
        *Mantener por compatibilidad con la interfaz externa.*

    beta : float
        Igual que alpha: parámetro externo no utilizado directamente (se recalcula dentro
        según qubits). Se mantiene por compatibilidad.

    maxiter : int
        Número máximo de iteraciones del optimizador clásico.

    n_shots : int
        Número de shots usados en las evaluaciones cuánticas.

    n_qpus: int
        Número de qpus con las que paralelizar.

    cunqa_str : str
        Modo de paralelización/ejecución ("Shots", "Circuits", etc.).
    
    family_name : str
        Nombre de la familia de QPUs levantadas con qraise.

    Funcionamiento
    --------------
    - Carga el grafo correspondiente según el problema y tamaño.
    - Calcula el número de qubits necesarios en función de los vértices y k.
    - Recalcula internamente alpha y beta en función del número de qubits.
    - Ejecuta MaxCut mediante `ejecutar_maxcut()`, que:
        • prepara el circuito,
        • ejecuta el optimizador,
        • guarda outputs (csv, json, etc.),
        • devuelve metadatos sobre las rutas creadas.
    - Devuelve las rutas de salida generadas por ejecutar_maxcut.

    Retorna
    -------
    (ruta_csv, ruta_csv_iter)
        ruta_csv      → CSV con resultados finales del experimento.
        ruta_csv_iter → CSV con el histórico iterativo del optimizador.
    """

    # === IMPORTS LOCALES (evita dependencias circulares) ===
    from src.exe_maxcut import ejecutar_maxcut       # Función principal de ejecución de MaxCut
    from src.op_graph import load_graph  # Carga de grafos y utilidades
    from pathlib import Path

    # === 1. Extraer parámetros del experimento ===
    problema = exp_list[0]     # Ejemplo: "MaxCut"
    tamaño = exp_list[1]       # Ejemplo: 10, 20, 40, 100
    optimizer = exp_list[2]    # Ejemplo: "POWELL", "DIFFERENTIALEVOLUTION"
    k = exp_list[3]            # Parámetro adicional del modelo (ej., compresión)

    #print(f"\n🚀 Ejecutando experimento: {problema} (n={tamaño}), opt={optimizer}, k={k}")

    # === 2. Cargar el grafo correspondiente al problema ===
    # Se espera un archivo con nombre "{problema}_{tamaño}.mc"
    parent = Path(__file__).resolve().parent
    G, num_ver = load_graph(f"{parent}/graphs/{problema}_{tamaño}.mc")

    # === 3. Determinar parámetros del optimizador ===
    # Si se pasaron parámetros específicos para este optimizador, se usan
    opt_params = optimizer_params.get(optimizer.upper(), None) if optimizer_params else None

    # === 4. Ejecutar MaxCut ===
    dic_resultado, subcarpeta, ruta_csv, ruta_csv_iter = ejecutar_maxcut(
        G=G,
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
        family_name=family_name
    )

    # === 5. Devolver las rutas creadas ===
    return ruta_csv, ruta_csv_iter


