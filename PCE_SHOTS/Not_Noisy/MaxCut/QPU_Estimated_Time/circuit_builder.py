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


import math
import networkx as nx
import numpy as np
from qiskit.circuit.library import RXXGate, RYYGate, RZZGate
from qiskit.circuit import QuantumCircuit, ParameterVector
from math import ceil
import random


class Circuit(object):
    """
    Clase que define un circuito cuántico paramétrico (ansatz).

    Modos disponibles:
    - 'custom' / 'Taylor_efficient' / 'U3' : tu implementación actual
    - 'original' : ansatz exactamente como el código original (RX, RY, RZ y RXX)
    """
    def __init__(self, size: int = 6, p: int = 0, entanglement="CNOT", rotation='U3',
                 connectivity="alternating_closed", initial_param=None, mode="custom"):
        self.size = size
        self.p = p
        self.entanglement = entanglement
        self.rotation = rotation
        self.connectivity = connectivity
        self.entang_list = []
        self.initial_param = initial_param
        self.circuit_representation = None
        self.mode = mode  # 'custom' o 'original'

    # ------------------ PUBLIC ------------------ #
    def compile_circuit(self):
        c = QuantumCircuit(self.size)
        self.circuit_representation = self._qiskit_circuit_(c)

    def get_circuit(self):
        return self.circuit_representation

    # ------------------ CONNECTIVITY ------------------ #
    def _define_connectivity_(self, layer):
        entang_list = []
        layer = math.ceil(layer / 2)

        if self.connectivity == "brickwork_single_rotating":
            entang_list_unpaired = [q for q in range(layer - 1, self.size + layer - 1)]
            def refit(lst, size):
                for i in range(len(lst)):
                    if lst[i] > size - 1:
                        lst[i] -= size
                if all(q < size for q in lst):
                    return lst
                else:
                    return refit(lst, size)
            entang_list_unpaired = refit(entang_list_unpaired, self.size)
            for q in range(1, len(entang_list_unpaired), 2):
                entang_list.append((entang_list_unpaired[q - 1], entang_list_unpaired[q]))

        elif self.connectivity == "ladder_open":
            for i in range(self.size - 1):
                entang_list.append((i, i + 1))

        elif self.connectivity == "ladder_closed":
            for i in range(self.size - 1):
                entang_list.append((i, i + 1))
            entang_list.append((self.size - 1, 0))

        # Otros patrones puedes añadirlos aquí según necesites
        return entang_list

    # ------------------ CIRCUITO QISKIT ------------------ #
    def _qiskit_circuit_(self, c: QuantumCircuit):
        param = ParameterVector('p', 0)
        params_number = 0

        # Contadores para modo original
        index_single = 0
        index_double = 0
        counter_taylor = 0

        for l in range(self.p):
            entang_list = self._define_connectivity_(l)

            # ------------------ MODO ORIGINAL ------------------ #
            if self.mode == "original":
                if l % 2 == 0:
                    # Capas de rotación individuales
                    if index_single % 3 == 0:
                        gate_type = 'RX'
                    elif index_single % 3 == 1:
                        gate_type = 'RY'
                    else:
                        gate_type = 'RZ'
                    index_single += 1
                    for q in range(self.size):
                        if len(param) < params_number + 1:
                            param.resize(params_number + 1)
                        if gate_type == 'RX':
                            c.rx(param[params_number], q)
                        elif gate_type == 'RY':
                            c.ry(param[params_number], q)
                        else:
                            c.rz(param[params_number], q)
                        params_number += 1
                else:
                    # Capas de entanglement RXX
                    if index_double % 2 == 0:
                        q_idx = list(range(0, self.size-1, 2))
                    else:
                        q_idx = list(range(1, self.size-1, 2))
                    for q in q_idx:
                        if len(param) < params_number + 1:
                            param.resize(params_number + 1)
                        c.append(RXXGate(param[params_number]), [q, q+1])
                        params_number += 1
                    index_double += 1

            # ------------------ MODO CUSTOM ------------------ #
            else:
                # Rotaciones
                if l % 2 == 0:
                    rotation = self.rotation
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

                # Entanglement
                else:
                    entanglement = self.entanglement
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
                            pass  # puedes añadir SU4 aquí
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
