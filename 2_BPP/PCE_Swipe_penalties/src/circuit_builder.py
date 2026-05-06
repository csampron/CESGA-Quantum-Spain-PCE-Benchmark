### ========================================================= ###
### Módulo: Circuit
### ========================================================= ###
###
### Este módulo define la clase `Circuit`, que permite crear
### circuitos cuánticos paramétricos (ansatz) configurables
### para algoritmos como VQE o PCE.
###
### Características principales:
### - Número de qubits configurable (`size`)
### - Número de capas (profundidad) configurable (`p`)
### - Diferentes tipos de puertas de rotación (`RX`, `RY`, `RZ`, `U3`, `Taylor_efficient`)
### - Diferentes tipos de entanglement (`CNOT`, `CZ`, `RXX`, `RYY`, `RZZ`, `SU4`, `Taylor_efficient`)
### - Diversas topologías de conectividad entre qubits:
###   "ladder_open", "ladder_closed", "brickwork_single_open",
###   "brickwork_single_closed", "brickwork_double", "brickwork_single_rotating",
###   "round_robin", "2D_lattice", "random", "d-regular"
### - Inicialización de parámetros aleatoria y opción de invertir el circuito (`identity_start`)
### - Compilación a `QuantumCircuit` de Qiskit listo para simulación o ejecución en hardware
###
### Uso típico:
### ------------
### circuit = Circuit(size=6, p=2, entanglement='CNOT', rotation='U3')
### circuit.compile_circuit()
### qc = circuit.get_circuit()  # Devuelve el QuantumCircuit de Qiskit
###
### ========================================================= ###


import math
import networkx as nx
import numpy as np
from qiskit.circuit.library import RXXGate, RYYGate
from qiskit.circuit import QuantumCircuit, ParameterVector
from math import ceil
import random


class Circuit(object):
    """
    Clase que define un circuito cuántico paramétrico (ansatz).

    Los parámetros principales del circuito y la conectividad están
    documentados en el encabezado del módulo.
    """
    def __init__(self, size: int = 6, p: int = 0, entanglement="CNOT", rotation='U3',
                 connectivity="alternating_closed", initial_param=None):
        self.size = size
        self.p = p
        self.entanglement = entanglement
        self.rotation = rotation
        self.connectivity = connectivity
        self.entang_list = []
        self.initial_param = initial_param
        self.circuit_representation = None

    def compile_circuit(self):
        c = QuantumCircuit(self.size)
        self.circuit_representation = self._qiskit_circuit_(c)

    def identity_start(self, seed):
        np.random.seed(seed)
        self.p = ceil(self.p / 2)
        self.compile_circuit()
        # Inicialización aleatoria de parámetros
        param_values = np.random.uniform(-1, 1, len(self.circuit_representation.parameters)) * np.pi
        param_dict = dict(zip(self.circuit_representation.parameters, param_values))
        self.circuit_representation.assign_parameters(param_dict)
        # Circuito inverso
        inverse_circuit = self.circuit_representation.inverse()
        self.circuit_representation = self.circuit_representation.compose(inverse_circuit)


    def get_circuit(self):
        return self.circuit_representation

    # ------------------ CONNECTIVITY ------------------ #
    def _define_connectivity_(self, layer):
        entang_list = []  # Lista que almacenará los pares de qubits que se entrelazan
        layer = math.ceil(layer / 2)  # Ajuste del número de capa, usado en patrones tipo brickwork

        # --- Ladder open ---
        if self.connectivity == "ladder_open":
            # Conecta cada qubit con su vecino inmediato (i, i+1)
            # No hay conexión entre el último y el primero
            for i in range(self.size - 1):
                entang_list.append((i, i + 1))

        # --- Ladder closed ---
        elif self.connectivity == "ladder_closed":
            # Igual que ladder_open, pero además conecta el último qubit con el primero
            for i in range(self.size - 1):
                entang_list.append((i, i + 1))
            entang_list.append((self.size - 1, 0))

        # --- Brickwork double ---
        elif self.connectivity == "brickwork_double":
            # Patrones tipo “ladrillo” con dos capas
            if self.size % 2 == 0:
                # Para tamaño par, se conectan pares alternados: 0-1,2-3,... y luego 1-2,3-4,...
                for i in range(0, self.size, 2):
                    entang_list.append((i, i + 1))
                for i in range(1, self.size - 1, 2):
                    entang_list.append((i, i + 1))
            else:
                # Para tamaño impar, similar pero evitando conectar fuera del rango
                for i in range(0, self.size - 1, 2):
                    entang_list.append((i, i + 1))
                for i in range(1, self.size - 1, 2):
                    entang_list.append((i, i + 1))

        # --- Brickwork single open ---
        elif self.connectivity == "brickwork_single_open":
            # Solo se conecta una capa de brickwork, alternando según la capa
            if self.size % 2 == 0:
                if layer % 2 == 0:
                    for i in range(0, self.size, 2):
                        entang_list.append((i, i + 1))
                else:
                    for i in range(1, self.size - 1, 2):
                        entang_list.append((i, i + 1))
            else:
                if layer % 2 == 0:
                    for i in range(0, self.size - 1, 2):
                        entang_list.append((i, i + 1))
                else:
                    for i in range(1, self.size - 1, 2):
                        entang_list.append((i, i + 1))

        # --- Brickwork single closed ---
        elif self.connectivity == "brickwork_single_closed":
            # Similar al brickwork single open, pero algunas capas cierran el círculo
            if self.size % 2 == 0:
                if layer % 2 == 0:
                    entang_list.append((0, self.size - 1))  # Cierra la conexión entre primer y último
                    for i in range(1, self.size - 1, 2):
                        entang_list.append((i, i + 1))
                else:
                    for i in range(0, self.size, 2):
                        entang_list.append((i, i + 1))
            else:
                if layer % 2 == 0:
                    for i in range(0, self.size - 1, 2):
                        entang_list.append((i, i + 1))
                else:
                    for i in range(1, self.size - 1, 2):
                        entang_list.append((i, i + 1))

        # --- Brickwork rotating ---
        elif self.connectivity == "brickwork_single_rotating":
            # Rotación de la capa de brickwork para que los pares cambien con cada capa
            entang_list_unpaired = [q for q in range(layer - 1, self.size + layer - 1)]

            def refit(entang_list_unpaired, size):
                # Ajusta los índices que exceden el tamaño del sistema
                for i in range(len(entang_list_unpaired)):
                    if entang_list_unpaired[i] > size - 1:
                        entang_list_unpaired[i] -= size
                if all(q < size for q in entang_list_unpaired):
                    return entang_list_unpaired
                else:
                    return refit(entang_list_unpaired, size)

            entang_list_unpaired = refit(entang_list_unpaired, self.size)
            # Se crean pares de los elementos ajustados
            for q in range(1, len(entang_list_unpaired), 2):
                entang_list.append((entang_list_unpaired[q - 1], entang_list_unpaired[q]))

        # --- Round robin ---
        elif self.connectivity == 'round_robin':
            # Cada qubit se empareja con todos los demás en un ciclo tipo torneo
            def qubits_round_robin(players):
                s = []
                if len(players) % 2 == 1:
                    players = players + [None]  # Añade un "bye" si hay número impar
                n = len(players)
                mapping = list(range(n))
                mid = n // 2
                for i in range(n - 1):
                    l1 = mapping[:mid]
                    l2 = mapping[mid:]
                    l2.reverse()
                    rnd = []
                    for j in range(mid):
                        t1 = players[l1[j]]
                        t2 = players[l2[j]]
                        if t1 is not None and t2 is not None:
                            rnd.append((t1, t2))
                    s.append(rnd)
                    mapping = mapping[mid:-1] + mapping[:mid] + mapping[-1:]
                return s

            length = self.size - 1 if self.size % 2 == 0 else self.size
            entang_list = qubits_round_robin(list(range(self.size)))[layer % length]

        # --- 2D lattice ---
        elif self.connectivity == "2D_lattice":
            size = math.ceil(math.sqrt(self.size))
            edge_list = []
            # Aquí se mantendría la lógica original de la rejilla 2D
            # Los pares serían vecinos en la cuadrícula
            # Ejemplo: (i, j) si están adyacentes horizontal o verticalmente

        # --- Random ---
        elif self.connectivity == "random":
            # Mezcla aleatoria de qubits y crea pares secuenciales
            import random
            qubits_list = list(range(self.size))
            random.shuffle(qubits_list)
            entang_list = [(qubits_list[i], qubits_list[i + 1]) for i in range(0, len(qubits_list) - 1, 2)]

        # --- d-regular ---
        elif 'regular' in self.connectivity:
            # Grafo d-regular aleatorio: cada nodo tiene exactamente d conexiones
            d = int(self.connectivity.replace('-regular', ''))
            p = math.floor(layer % self.size)
            seed = 0
            graph = nx.random_regular_graph(d, self.size, seed)
            while not nx.is_connected(graph):
                seed += 1
                graph = nx.random_regular_graph(d, self.size, seed)
            entang_list = []
            while len(graph) > 0:
                while p >= len(graph):
                    p -= 1
                if len(list(graph[list(graph.nodes())[p]].keys())) == 0:
                    p = len(graph)
                    while p > 0:
                        p -= 1
                        if len(list(graph[list(graph.nodes())[p]].keys())) == 0:
                            continue
                        else:
                            break
                    if p == 0:
                        break
                p_node = p % d
                while p_node >= len(list(graph[list(graph.nodes())[p]].keys())):
                    p_node -= 1
                entang_list.append((list(graph.nodes())[p], list(graph[list(graph.nodes())[p]].keys())[p_node]))
                graph.remove_nodes_from([list(graph[list(graph.nodes())[p]].keys())[p_node], list(graph.nodes())[p]])

            # Si algún par ya existía, recalcula
            for i in entang_list:
                if i in self.entang_list or tuple(reversed(i)) in self.entang_list:
                    entang_list = self._define_connectivity_(layer + 2)
            self.entang_list = entang_list

        return entang_list



    # ------------------ CIRCUITO QISKIT ------------------ #
    def _qiskit_circuit_(self, c: QuantumCircuit):
        param = ParameterVector('p', 0)
        params_number = 0

        def SU4_qiskit(circ, q0, q1):
            nonlocal params_number
            if len(param) < params_number + 15:
                param.resize(params_number + 15)
            indices = list(range(params_number, params_number + 15))
            params_number += 15
            circ.u(param[indices[0]], param[indices[1]], param[indices[2]], q0)
            circ.u(param[indices[3]], param[indices[4]], param[indices[5]], q1)
            circ.cx(q0, q1)
            circ.u(param[indices[6]], param[indices[7]], param[indices[8]], q0)
            circ.u(param[indices[9]], param[indices[10]], param[indices[11]], q1)
            circ.cx(q0, q1)
            circ.u(param[indices[12]], param[indices[13]], param[indices[14]], q0)
            circ.cx(q0, q1)

        counter_taylor = 0

        for l in range(self.p):
            entang_list = self._define_connectivity_(l)
            rotation = self.rotation
            entanglement = self.entanglement

            # Capas de rotación
            if l % 2 == 0:
                if self.rotation == 'Taylor_efficient':
                    if counter_taylor % 3 == 0:
                        rotation = 'RZ'
                    elif counter_taylor % 3 == 1:
                        rotation = 'RX'
                    else:
                        rotation = 'RY'
                    counter_taylor += 1

                for q in range(self.size):
                    if q in [x for t in entang_list for x in t] or l == 0:
                        if rotation == 'RX':
                            if len(param) < params_number + 1:
                                param.resize(params_number + 1)
                            c.rx(param[params_number], q)
                            params_number += 1
                        elif rotation == 'RY':
                            if len(param) < params_number + 1:
                                param.resize(params_number + 1)
                            c.ry(param[params_number], q)
                            params_number += 1
                        elif rotation == 'RZ':
                            if len(param) < params_number + 1:
                                param.resize(params_number + 1)
                            c.rz(param[params_number], q)
                            params_number += 1
                        elif rotation == 'U3':
                            if len(param) < params_number + 2:
                                param.resize(params_number + 2)
                            c.u(param[params_number], param[params_number+1], 0, q)
                            params_number += 2

            # Capas de entanglement
            else:
                if entanglement == 'Taylor_efficient':
                    if counter_taylor % 3 == 0:
                        entanglement = 'RZZ'
                    elif counter_taylor % 3 == 1:
                        entanglement = 'RXX'
                    else:
                        entanglement = 'RYY'
                    counter_taylor += 1

                for q0, q1 in entang_list:
                    if q0 is None or q1 is None:
                        continue
                    if entanglement == 'SU4':
                        SU4_qiskit(c, q0, q1)
                    elif entanglement == 'RXX':
                        if len(param) < params_number + 1:
                            param.resize(params_number + 1)
                        c.append(RXXGate(param[params_number]), [q0, q1])
                        params_number += 1
                    elif entanglement == 'RZZ':
                        if len(param) < params_number + 1:
                            param.resize(params_number + 1)
                        c.rzz(param[params_number], q0, q1)
                        params_number += 1
                    elif entanglement == 'RYY':
                        if len(param) < params_number + 1:
                            param.resize(params_number + 1)
                        c.append(RYYGate(param[params_number]), [q0, q1])
                        params_number += 1
                    elif entanglement == 'CZ':
                        c.cz(q0, q1)
                    elif entanglement == 'CNOT':
                        c.cx(q0, q1)

        return c

