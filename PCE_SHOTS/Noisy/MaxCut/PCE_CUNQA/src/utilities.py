### ========================================================= ###
### Módulo: utilities
### ========================================================= ###
###
### Este módulo proporciona funciones para la optimización variacional
### (VQE) de ansatz cuánticos y manejo de resultados de evaluaciones.
###
### Funcionalidades principales:
### -----------------------------
### - run_vqe_optimization(...)
###     Ejecuta la optimización variacional sobre un ansatz cuántico
###     usando diferentes optimizadores clásicos (Powell, BFGS, SPSA,
###     Differential Evolution, etc.).
###     Permite callbacks para registrar la evolución del coste y 
###     guardar los resultados en CSV.
###
### Dependencias:
### -------------
### - Función de cálculo de tamaño de corte: calc_cut_size (op_graph)
### - Optimización: scipy.optimize (minimize, differential_evolution, brute)
### - SPSA de Qiskit (opcional, descomentando import)
### - numpy, csv, os
###
### ========================================================= ###

from scipy.optimize import minimize, differential_evolution, brute #, import SPSA  # Descomentar si se utiliza Qiskit SPSA
import numpy as np
import csv
import os
from functools import partial

def run_vqe_optimization(
    sim,
    n_shots,
    num_qubits,
    alpha,
    beta,
    compiled_circuit,
    G,
    list_size,
    d_t,
    optimizer,
    optimizer_params=None,
    loss_func_estimator=None,
    maxiter=1000,
    log_csv_path=None,
    cunqa_str="None",
    QPUs=None
):
    """
    Ejecuta una optimización variacional (VQE) sobre un ansatz cuántico dado.

    Retorna:
    --------
    result : OptimizeResult
        Resultado del optimizador.
    experiment_result : list
        Lista con los resultados de la función de pérdida en cada evaluación.
    """
    experiment_result = []
    cost_history = []
    iteration_costs = []

    ### CALLBACKS
    def callback(xk):
        """Callback simple para optimización clásica."""
        value = loss_func(xk)
        iteration_costs.append(value)

    def callback_de(intermediate_result):
        """Callback para differential_evolution."""
        iteration_costs.append(intermediate_result.fun)
        return None

    def callback_spsa(nfev, x, fx, stepsize, accepted):
        """Callback para SPSA."""
        cost_history.append(fx)

    def loss_func(x):
        value = loss_func_estimator(
            x=x,
            alpha=alpha,
            beta=beta,
            ansatz=compiled_circuit,
            sim=sim,
            graph=G,
            list_size=list_size,
            num_qubits=num_qubits,
            d_t=d_t,
            n_shots=n_shots,
            experiment_result=experiment_result,
            CUNQA=cunqa_str,
            QPUs=QPUs
        )
        cost_history.append(value)
        return value

    # Generar parámetros iniciales
    rng_default = np.random.default_rng(33)
    initial_params = rng_default.random(len(compiled_circuit[0].parameters)) * 2 * np.pi

    if isinstance(optimizer, str):
        optimizer_lower = optimizer.lower()

        # --- Definir parámetros por defecto de cada optimizador ---
        default_optimizers = {
            "spsa": {
                "class": None,  # Descomentar SPSA si lo usas
                "params": {
                    "maxiter": maxiter,
                    "learning_rate": 0.25,
                    "perturbation": 0.01,
                    "blocking": True,
                    "allowed_increase": 0.05,
                    "last_avg": 10,
                    "callback": callback_spsa
                }
            },
            "powell": {
                "method": "Powell",
                "options": {
                    "maxiter": maxiter,
                    "maxfev": 50000,
                    "xtol": 1e-9,
                    "ftol": 1e-9,
                    "disp": True,
                    "return_all": True
                },
                "callback": callback
            },
            "cobyla": {
                "method": "COBYLA",
                "options": {
                    "maxiter": maxiter,
                    "rhobeg": 1.0,
                    "tol": 1e-9,
                    "disp": False
                },
                "callback": callback
            },
            "bfgs": {
                "method": "BFGS",
                "options": {
                    "disp": True,
                    "maxiter": maxiter,
                    "gtol": 1e-3
                },
                "callback": callback
            },
            "lbfgsb": {
                "method": "L-BFGS-B",
                "options": {
                    "disp": True,
                    "maxiter": maxiter,
                    "ftol": 1e-6,
                    "gtol": 1e-3,
                    "eps": 1e-3
                },
                "callback": callback
            },
            "tnc": {
                "method": "TNC",
                "options": {
                    "disp": True,
                    "maxiter": maxiter,
                    "ftol": 1e-8,
                    "xtol": 1e-8,
                    "gtol": 1e-4
                },
                "callback": callback
            },
            "slsqp": {
                "method": "SLSQP",
                "options": {
                    "disp": True,
                    "maxiter": maxiter,
                    "ftol": 1e-8,
                    "eps": 1e-6
                },
                "callback": callback
            },
            "differentialevolution": {
                "kwargs": {
                    "strategy": "best1exp",
                    "maxiter": maxiter,
                    "popsize": 3,
                    "tol": 1e-7,
                    "mutation": (0.5, 1),
                    "recombination": 0.7,
                    "disp": True,
                    "polish": True,
                    "init": "halton"
                }
            },
            "brute": {}  # Sin opciones por defecto
        }

        if optimizer_lower not in default_optimizers:
            raise ValueError(f"Optimizador desconocido: {optimizer}")

        # --- Sobrescribir parámetros con optimizer_params ---
        opt_config = default_optimizers[optimizer_lower]

        if optimizer_params:
            print(f"⚡ Usando parámetros personalizados para el optimizador {optimizer.upper()}")

            if optimizer_lower == "differentialevolution":
                opt_config["kwargs"].update(optimizer_params)
            elif optimizer_lower == "spsa":
                opt_config["params"].update(optimizer_params)
            else:
                opt_config["options"].update(optimizer_params)
        else:
            print(f"⚡ No se pasaron parámetros, usando valores por defecto del optimizador {optimizer.upper()}")

        # --- Ejecutar optimizador ---
        if optimizer_lower == "spsa":
            # Descomentar cuando SPSA esté disponible
            # opt = SPSA(**opt_config["params"])
            # result = opt.minimize(fun=loss_func, x0=initial_params)
            raise NotImplementedError("SPSA no está importado. Descomenta import SPSA si lo usas.")
        elif optimizer_lower == "differentialevolution":
            result = differential_evolution(
                loss_func,
                bounds=[(0, 2*np.pi)]*len(initial_params),
                seed=33, 
                callback=callback_de,
                **opt_config["kwargs"]  # Solo parámetros válidos para DE: strategy, maxiter, popsize, etc.
            )

        elif optimizer_lower == "brute":
            result = brute(loss_func, ranges=[(0, 2*np.pi)]*len(initial_params))
        else:
            result = minimize(
                loss_func,
                initial_params,
                method=opt_config["method"],
                options=opt_config["options"],
                callback=opt_config["callback"]
            )

    else:
        # Objeto optimizador personalizado
        result = optimizer.minimize(fun=loss_func, x0=initial_params)

    # --- Guardar CSV si se solicita ---
    if log_csv_path:
        os.makedirs(os.path.dirname(log_csv_path), exist_ok=True)
        with open(log_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["iteracion", "valor_coste"])
            for i, val in enumerate(cost_history):
                writer.writerow([i, val])

        iter_csv_path = log_csv_path.replace(".csv", "_iter.csv")
        with open(iter_csv_path, "w", newline="", encoding="utf-8") as f:
            writer = csv.writer(f)
            writer.writerow(["iteracion", "valor_coste"])
            for i, val in enumerate(iteration_costs):
                writer.writerow([i, val])

    return result, experiment_result
