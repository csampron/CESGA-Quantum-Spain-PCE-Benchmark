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
### - Optimización: scipy.optimize (minimize, differential_evolution, brute)
### - SPSA de Qiskit (opcional, descomentando import)
### - numpy, csv, os
###
### ========================================================= ###

from scipy.optimize import minimize, differential_evolution, brute
import numpy as np
import csv
import os
from functools import partial


def compute_loss_bpp(
    x,
    loss_func_estimator,
    alpha,
    beta,
    lambda_1,
    lambda_2,
    lambda_3,
    compiled_circuit,
    sim,
    Capacity,
    Weights,
    num_items,
    list_size,
    d_t,
    n_shots,
    experiment_result,
    CUNQA,
    family_name=None,
    cost_history=None,
    worker_id=None,
    worker_histories=None
):
    value = loss_func_estimator(
        x=x,
        alpha=alpha,
        beta=beta,
        lambda_1=lambda_1,
        lambda_2=lambda_2,
        lambda_3=lambda_3,
        ansatz=compiled_circuit,
        sim=sim,
        Capacity=Capacity,
        Weights=Weights,
        num_items=num_items,
        list_size=list_size,
        num_qubits=compiled_circuit[0].num_qubits,
        d_t=d_t,
        n_shots=n_shots,
        experiment_result=experiment_result,
        CUNQA=CUNQA,
        family_name=family_name
    )

    if cost_history is not None:
        cost_history.append(value)

    if worker_histories is not None and worker_id is not None:
        worker_histories[worker_id].append(value)

    return value


def run_vqe_optimization(
    sim,
    n_shots,
    alpha,
    beta,
    lambda_1,
    lambda_2,
    lambda_3,
    compiled_circuit,
    Capacity,
    Weights,
    num_items,
    list_size,
    d_t,
    optimizer,
    optimizer_params=None,
    loss_func_estimator=None,
    maxiter=1000,
    log_csv_path=None,
    cunqa_str="None",
    family_name=None
):
    experiment_result = []
    cost_history = []
    iteration_costs = []

    def callback(xk):
        value = loss_func(xk)
        iteration_costs.append(value)

    def callback_de(intermediate_result):
        iteration_costs.append(intermediate_result.fun)
        return None

    loss_func = partial(
        compute_loss_bpp,
        loss_func_estimator=loss_func_estimator,
        alpha=alpha,
        beta=beta,
        lambda_1=lambda_1,
        lambda_2=lambda_2,
        lambda_3=lambda_3,
        compiled_circuit=compiled_circuit,
        sim=sim,
        Capacity=Capacity,
        Weights=Weights,
        num_items=num_items,
        list_size=list_size,
        d_t=d_t,
        n_shots=n_shots,
        experiment_result=experiment_result,
        CUNQA=cunqa_str,
        family_name=family_name,
        cost_history=cost_history
    )

    rng_default = np.random.default_rng(33)
    initial_params = rng_default.random(len(compiled_circuit[0].parameters)) * 2 * np.pi

    if isinstance(optimizer, str):
        optimizer_lower = optimizer.lower()

        default_optimizers = {
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
                    "popsize": 1,
                    "tol": 1e-24,
                    "mutation": (0.5, 1),
                    "recombination": 0.7,
                    "disp": True,
                    "polish": True,
                    "init": "halton",
                    "workers": -1
                }
            },
            "brute": {}
        }

        if optimizer_lower not in default_optimizers:
            raise ValueError(f"Optimizador desconocido: {optimizer}")

        opt_config = default_optimizers[optimizer_lower]

        if optimizer_params:
            if optimizer_lower == "differentialevolution":
                opt_config["kwargs"].update(optimizer_params)
            else:
                opt_config["options"].update(optimizer_params)

        if optimizer_lower == "differentialevolution":
            result = differential_evolution(
                loss_func,
                bounds=[(0, 2 * np.pi)] * len(initial_params),
                callback=callback_de,
                **opt_config["kwargs"]
            )

            compute_loss_bpp(
                result.x,
                loss_func_estimator=loss_func_estimator,
                alpha=alpha,
                beta=beta,
                lambda_1=lambda_1,
                lambda_2=lambda_2,
                lambda_3=lambda_3,
                compiled_circuit=compiled_circuit,
                sim=sim,
                Capacity=Capacity,
                Weights=Weights,
                num_items=num_items,
                list_size=list_size,
                d_t=d_t,
                n_shots=n_shots,
                experiment_result=experiment_result,
                CUNQA=cunqa_str,
                family_name=family_name,
                cost_history=cost_history
            )

        elif optimizer_lower == "brute":
            result = brute(
                loss_func,
                ranges=[(0, 2 * np.pi)] * len(initial_params)
            )

        else:
            result = minimize(
                loss_func,
                initial_params,
                method=opt_config["method"],
                options=opt_config["options"],
                callback=opt_config["callback"]
            )

    else:
        result = optimizer.minimize(fun=loss_func, x0=initial_params)

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