### ========================================================= ###
### Módulo: tensor_counts
### ========================================================= ###
###
### Funciones para:
### - Generar tensores de base computacional y combinaciones de qubits
### - Construir tensores de probabilidades a partir de counts
### - Calcular valores esperados mediante productos tensoriales
### - Seleccionar subconjuntos de nodos y combinarlos
### - Combinar resultados de múltiples QPUs y circuitos
###
### ========================================================= ###

import numpy as np
from itertools import combinations
from math import comb
import pandas as pd


### ========================================================= ###
### FUNCIONES DE GENERACIÓN DE TENSORES
### ========================================================= ###

def computational_basis_tensor(n_circuits, n_qubits):
    """ Devuelve un tensor de forma (n_circuits, 2^n_qubits, n_qubits), donde cada fila contiene la cadena de bits correspondiente a cada uno de los estados de la base computacional. """
    n_states = 2 ** n_qubits  # Total de estados de la base computacional (2^n)

    # Creamos una columna con enteros desde 0 hasta 2^n - 1
    states = np.arange(n_states, dtype=np.int8)[:, None]

    # Generamos la matriz de bits para cada entero (representación binaria en orden q_0 ... q_{n-1})
    # '>>' desplaza bits a la derecha y '& 1' se queda solo con el último bit


    # Orden invertido que coincide con qiskit (|q_{n-1} ... q_0>)
    #bits = ((states >> np.arange(n_qubits)) & 1).astype(np.uint8)

    # Orden invertido que NO coincide con qiskit (|q_{n-1} ... q_0>)
    bits = ((states >> np.arange(n_qubits - 1, -1, -1)) & 1).astype(np.uint8) 


    # Replicamos esta matriz 'bits' para cada circuito (sin copiar datos)
    return np.broadcast_to(bits, (n_circuits, n_states, n_qubits))


def combination_tensor(n_circuits, n_qubits, k_degree):
    """ Devuelve un tensor de forma (n_circuits, n_qubits, n_combinations), donde cada columna contiene 1s en las posiciones que corresponden a una combinación de qubits de tamaño k_degree. """
    # Número total de combinaciones posibles de qubits de tamaño k_degree
    n_combinations = comb(n_qubits, k_degree)

    # Matriz base inicializada en ceros
    base = np.zeros((n_qubits, n_combinations), dtype=np.int8)

    # Iteramos sobre todas las combinaciones posibles de índices de qubits
    for j, combo in enumerate(combinations(range(n_qubits), k_degree)):
        base[list(combo), j] = 1  # Ponemos 1 donde la combinación lo indique

    # Garantiza coherencia en el orden de bits: la fila 0 corresponde a Z0, la fila 1 a Z1, etc.
    base = base[::-1, :]

    # Replicamos la matriz base a lo largo del eje de circuitos (sin copiar datos)
    return np.broadcast_to(base, (n_circuits, n_qubits, n_combinations))





def build_probability_tensor(df_list, n_shots, n_qubits):
    """
    Convierte una lista de DataFrames o arrays de probabilidades a un tensor de probabilidades
    siguiendo el orden natural de bits (Z0, ..., Zn-1).

    Parámetros
    ----------
    df_list : list
        Lista de DataFrames con columna 'total_counts' o arrays de probabilidades ya normalizadas.
    n_shots : int
        Número de disparos (para normalizar DataFrames).
    n_qubits : int
        Número de qubits del sistema.

    Returns
    -------
    np.ndarray
        Tensor de probabilidades con shape (n_circuits, 2^n_qubits, 1)
    """
    prob_arrays = []

    for item in df_list:
        # Caso 1: DataFrame con counts de Qiskit
        if hasattr(item, "columns") and "total_counts" in item.columns:
            counts = item["total_counts"].to_numpy()
            n_states = 2**n_qubits

            # Creamos array de probabilidades inicializado en 0
            probs = np.zeros(n_states, dtype=float)

            # Los índices de los counts de Qiskit corresponden a los strings de bits
            # Convertimos cada índice a bitstring y luego a índice en orden natural
            for idx, c in enumerate(counts):
                # Bitstring Qiskit: q_{n-1} ... q_0
                bitstr_qiskit = format(idx, f'0{n_qubits}b')
                # Convertir a orden natural: Z0 ... Zn-1
                bitstr_nat = bitstr_qiskit[::-1]
                # Nuevo índice en decimal
                new_idx = idx
                probs[new_idx] = c / n_shots

        # Caso 2: array numpy de probabilidades
        else:
            probs = np.asarray(item, dtype=float)
            if not np.isclose(probs.sum(), 1.0):
                probs = probs / probs.sum()

        # Convertir a shape (2^n_qubits, 1)
        prob_arrays.append(probs.reshape(-1, 1))

    # Apilar en eje de circuitos
    return np.stack(prob_arrays, axis=0)




def build_sign_tensor(n_circuits, n_qubits, k_degree):
    """ Construye los tensores estáticos del pipeline:
    a = computational_basis_tensor(...)
    b = combination_tensor(...)
    c = a @ b
    d = (-1)**c
    d_t = d.transpose(0, 2, 1)

    Devuelve un diccionario con los resultados intermedios.
    """
    # 1. Tensor base computacional
    a = computational_basis_tensor(n_circuits, n_qubits)

    # 2. Tensor de combinaciones
    b = combination_tensor(n_circuits, n_qubits, k_degree)
    
    # 3. Producto tensorial "pre-signo"
    c = a @ b
    
    # 4. Tensor de signos
    d = (-1) ** c
    
    # 5. Transponer d: (n_circuits, n_combinations, 2^n_qubits)
    d_t = d.transpose(0, 2, 1)
    
    return d_t


def run_with_probabilities(d_t, p_t):
    """ Calcula el resultado del pipeline a partir del tensor de signos (d_t) y el tensor de probabilidades (p_t).

    Parámetros
    ----------
    d_t : np.ndarray
        Tensor de signos transpuesto, con forma (n_circuits, n_combinations, 2^n_qubits)
    p_t : np.ndarray
        Tensor de probabilidades, con forma (n_circuits, 2^n_qubits, 1)

    Devuelve
    --------
    dict
        {'result': ..., 'reshaped_result': ...}
    """
    # 1. Aplicamos el tensor de signos al tensor de probabilidades
    result = d_t @ p_t  # -> (n_circuits, n_combinations, 1)

    # 2. Transponemos: (n_circuits, 1, n_combinations)
    reshaped_result = result.transpose(0, 2, 1)

    # 3. Devolver como diccionario
    return {
        "result": result,
        "reshaped_result": reshaped_result
    }


def select_nodes_from_aux(aux, m, n, return_concatenated=True):
    """ Selecciona subconjuntos automáticos del tensor `aux` según el valor de `n`.

    - Toma los `n` primeros valores de X (aux[0, 0, :n]).
    - Toma los `n` primeros valores de Y (aux[1, 0, :n]).
    - Toma los restantes `m - 2n` valores de Z (aux[2, 0, :rem]).

    Si return_concatenated=True, devuelve un diccionario {nodo: valor} 
    con los valores concatenados para poder usar en get_partition_from_expmap.
    Si return_concatenated=False, devuelve un diccionario separado {'X', 'Y', 'Z'}.

    Parámetros
    ----------
    aux : np.ndarray
        Tensor con forma (3, 1, m), donde las tres primeras dimensiones
        representan las bases X, Y, Z respectivamente.
    m : int
        Número total de nodos del grafo.
    n : int
        Número de elementos a seleccionar en las bases X e Y.
        La base Z tomará automáticamente los restantes m - 2n.
    return_concatenated : bool, opcional
        Si True, devuelve un diccionario {nodo: valor} concatenado.
        Si False, devuelve un diccionario separado {'X', 'Y', 'Z'}.

    Devuelve
    --------
    dict
        Diccionario con los valores seleccionados.
        - Si return_concatenated=True: {0: X0, 1: X1, ..., n+m-1: Z?}
        - Si return_concatenated=False: {'X': x_vals, 'Y': y_vals, 'Z': z_vals}
    """
    if aux.ndim != 3:
        raise ValueError(f"Se esperaba un tensor 3D, recibido: {aux.shape}")

    if aux.shape[0] != 3:
        raise ValueError(f"La primera dimensión de 'aux' debe ser 3 (X, Y, Z); recibido {aux.shape[0]}.")

    rem = m - 2 * n
    if rem < 0:
        raise ValueError(f"n demasiado grande: m={m}, n={n}, m - 2n = {rem}")

    x_vals = aux[0, 0, :n]
    y_vals = aux[1, 0, :n]
    z_vals = aux[2, 0, :rem] if rem > 0 else np.array([])

    if return_concatenated:
        concatenated = np.concatenate([x_vals, y_vals, z_vals])
        # Construir diccionario nodo -> valor
        return {i: val for i, val in enumerate(concatenated)}
    else:
        return {'X': x_vals, 'Y': y_vals, 'Z': z_vals}


def combine_counts_shots(results, n_qubits, n_circuits, num_qpus):
    """ Combina los resultados de múltiples QPUs para varios circuitos, asumiendo que los resultados están agrupados por bloques consecutivos (todas las QPUs de un circuito, luego las del siguiente, etc.)

    Parameters
    ----------
    results : list
        Lista de objetos resultado con atributo `.counts` (dict[str, int]).
        Se asume el orden: [circ0_qpu0..n, circ1_qpu0..n, ...].
    n_circuits : int
        Número de circuitos distintos (por ejemplo, 3 si son X/Y/Z).
    num_qpus : int
        Número de QPUs usadas (bloques por circuito).

    Returns
    -------
    total_counts_list : list[dict]
        Lista de diccionarios (uno por circuito) combinando todos los QPUs.
    df_list : list[pd.DataFrame]
        Lista de DataFrames con los counts por QPU (opcional, para inspección).
    """
    total_counts_list = []
    df_list = []

    # --- Plantilla con todos los bitstrings posibles ---
    all_bitstrings = [f"{i:0{n_qubits}b}" for i in range(2**n_qubits)]
    template_series = pd.Series(
        {b: 0 for b in all_bitstrings}, 
        name="template"
    )

    for c in range(n_circuits):
        # Seleccionamos los resultados correspondientes a este circuito
        start = c * num_qpus
        end = start + num_qpus
        circ_results = results[start:end]

        # Convertimos cada resultado en una Series
        series_list = [
            pd.Series(r.counts, name=f"qpu_{i}") 
            for i, r in enumerate(circ_results)
        ]

        # Insertamos la plantilla al comienzo
        series_list.insert(0, template_series)

        # Concatenamos → ahora están todos los bitstrings garantizados
        df = pd.concat(series_list, axis=1).fillna(0)

        # Quitamos la columna plantilla
        df = df.drop(columns=["template"])

        # Añadimos total
        df["total_counts"] = df.sum(axis=1)

        # Ordenamos
        df = df.sort_index()

        # Guardamos outputs
        total_counts = df["total_counts"].to_dict()
        df_list.append(df)
        total_counts_list.append(total_counts)

    return total_counts_list, df_list


def combine_counts_circuits(results, n_qubits):
    """ Recibe la salida directa de `gather(qjobs)` en modo 'Circuits' y devuelve un formato idéntico al de combine_counts:

    - padded_counts_list: lista de dicts por circuito
    - df_list: lista de DataFrames por circuito
    """
    # --- Todos los bitstrings posibles ---
    bitstrings = [f"{i:0{n_qubits}b}" for i in range(2**n_qubits)]

    padded_counts_list = []
    df_list = []

    for i, res in enumerate(results):
        # Serie original del resultado
        s = pd.Series(res.counts)

        # Rellenamos los faltantes directamente
        s = s.reindex(bitstrings, fill_value=0)

        # Construimos DF igual que el de combine_counts (pero solo 1 QPU)
        df = pd.DataFrame({
            f"qpu_{i}": s,
            "total_counts": s    # suma trivial
        })

        # Guardamos
        padded_counts_list.append(s.to_dict())
        df_list.append(df)

    return padded_counts_list, df_list

