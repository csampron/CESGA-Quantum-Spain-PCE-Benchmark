import os, sys
sys.path.append(os.getenv("HOME"))

from cunqa.qutils import qraise, qdrop

# === IMPORTACIÓN DE FUNCIONES PRINCIPALES ===
# Estas funciones permiten generar combinaciones de parámetros experimentales,
# aplicar filtros y ejecutar automáticamente los experimentos definidos.

from src.exe_experiments import (
    casuistica_experimento,     # genera todas las combinaciones posibles de parámetros
    filtrar_combinaciones,      # permite filtrar combinaciones por criterio (opcional)
    ejecutar_experimentos       # ejecuta los experimentos uno por uno
)

from src.auxiliar import num_qubits # Calcula el número de qubits necesarios

# Función encargada de graficar los resultados obtenidos en cada experimento
from src.grafica_csv import (
    graficar_coste         # genera y guarda una gráfica a partir del CSV del experimento
)

# === 1. DEFINICIÓN DE LOS PARÁMETROS DEL EXPERIMENTO ===
# Cada lista representa un conjunto de valores posibles para uno de los ejes del experimento.
# Se generarán todas las combinaciones posibles entre los elementos de estas listas.
#   - Problema: tipo de problema cuántico a resolver (en este caso, siempre "MaxCut").
#   - Tamaño: número de nodos del grafo a utilizar.
#   - Optimiz: algoritmo clásico de optimización (ej. "COBYLA", "POWELL", "SLSQP"...).
#   - k: parámetro que controla la compresión o agrupación de variables del circuito cuántico.

Problema = ["VRP"]
Tamaño = [8]
Instancia = [1]
Optimiz = ["DIFFERENTIALEVOLUTION"]
k = [2]


# Diccionario global que al ser None hace que se ejecuten los parámetros por defecto establecidos en utilities.py
optimizer_params = None

# === 2. GENERAR TODAS LAS COMBINACIONES DE EXPERIMENTOS ===
# 'casuistica_experimento' toma las listas definidas arriba y devuelve
# una lista con todas las combinaciones posibles entre sus elementos.
# Por ejemplo:
# [
#   ["MaxCut", 10, "COBYLA", 2],
#   ["MaxCut", 10, "POWELL", 2]
# ]
# Cada una de estas combinaciones representa un experimento independiente.
combinaciones = casuistica_experimento(Problema, Tamaño, Optimiz, k)


# === 3. EJECUTAR LOS EXPERIMENTOS Y GRAFICAR LOS RESULTADOS ===
# Se recorre cada combinación generada y se ejecuta de forma independiente.
# La función 'ejecutar_experimentos' se encarga internamente de:
#   - Cargar el grafo correspondiente (según el tamaño y problema)
#   - Construir el circuito cuántico con los parámetros adecuados
#   - Ejecutar la optimización (VQE)
#   - Guardar los resultados en un archivo JSON y CSV
#   - Devolver la ruta del CSV con el historial de coste
#
# Posteriormente, 'graficar_resultados' toma esa ruta y genera una gráfica
# mostrando la evolución del valor de la función de coste por iteración.

# Número de iteraciones a llevar a cabo
maxiter = 2500

# Número de shots a llevar a cabo
n_shots = 1 # En este caso no se van a usar porque se va a tener simulaciónn exacta


for combo in combinaciones:
    #for i in range(10):

    print(f"\n🚀 Ejecutando experimento con parámetros: {combo}")
    
    # Definir los hiperparámetros usados internamente
    alpha = 17.0
    beta = 0.8
    
    # Ejecuta el experimento y obtiene la ruta del CSV con los resultados
    ruta_csv, ruta_csv_iter = ejecutar_experimentos(exp_list=combo, optimizer_params=optimizer_params, alpha=alpha, beta=beta, maxiter=maxiter, n_shots=n_shots, nqpus = None, cunqa_str = "Simulation", family_name = None)
    
    # Genera y guarda la gráfica correspondiente al CSV del experimento
    graficar_coste(ruta_csv_iter)

