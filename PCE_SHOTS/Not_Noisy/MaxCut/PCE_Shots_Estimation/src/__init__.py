"""
Paquete principal para la ejecución del algoritmo de optimización cuántica (PCE + VQE).

Incluye módulos para:
- Construcción y carga de grafos
- Definición del circuito cuántico
- Cálculo del número de qubits
- Evaluación de funciones de pérdida
- Optimización y postprocesado
- Visualización de resultados
- Ejecución de experimentos y casuísticas específicas
"""

# --- Módulo de grafos ---
# Funciones para cargar grafos y calcular tamaños de corte (cut size)
from .op_graph import calc_cut_size, load_graph

# --- Módulo auxiliar ---
# Función para calcular el número de qubits necesarios según el grafo
from .auxiliar import (
    num_qubits,
    build_pauli_correlation_encoding,
    get_partition_from_expmap,
    local_refinement_from_partition,
)


# --- Constructor del circuito cuántico ---
# Clase principal para definir y construir el circuito cuántico
from .circuit_builder import Circuit


# --- Módulo de tensor y valores esperados ---
# Funciones para construir tensores de probabilidad, ejecutar con probabilidades,
# seleccionar nodos auxiliares y combinar resultados de distintos circuitos o mediciones
from .tensor_exp_value import build_probability_tensor, run_with_probabilities, select_nodes_from_aux, combine_counts_shots, combine_counts_circuits
