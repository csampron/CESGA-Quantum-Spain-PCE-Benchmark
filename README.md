# CESGA-Quantum-Spain-PCE-Benchmark

## Benchmark of Pauli Correlation Encoding for different optimisation problems

In this repository you can find the code used to get the results shown in the paper Benchmark of Pauli Correlation Encoding for different optimisation problems.

The repository is organized as followed:

- 1_MaxCut: Code used for the execution of the MaxCut problem.
    - Results: Directory with plots, results and the code used to obtain such plots and results
    - PCE_CUNQA:
        - init_cunqa.sh to download dependencies
        - main_simul.sh to execute the program
        - `src/` contains all the main modules to prepare, execute and analyse the experiments, it includes:
            - `auxiliar.py` → Auxiliar functions, including calculation of the number of qubits and coding of Hamiltonians.  
            - `exe_experiments.py` → Generation of experiment combinations and automated execution.
            - `grafica_csv.py` → Functions to generate figures based on the results shown on a CSV file. 
            - `utilities.py` → Classical optimisation (Powell, COBYLA, Differential Evolution, etc.) and callbacks.
            - `tensor_exp_value.py` → Tensor construction of the computational basis and qubits combinations.
            - `circuit_builder.py` → Class used to build and compile parametric circuits. 
            - `graphs/` → Instances of the MaxCut problem used on the benchmark.

- 2_BPP: Code used for the execution of the BPP problem.
    - Uses the same structure as the `1_MaxCut/` directory with the addition of two new directories:
        - `Parameter_swipe_alpha_beta/` → Code used to perform a parameter swipe of alpha and beta.
        - `Parameter_swipe_penalties/` → Code used to perform a parameter swipe on the lambda penalties of the cost function.

- 3_TSP: Code used for the execution of the TSP problem.
    - Uses the same structure as the `2_BPP/` directory.

- 4_VRP: Code used for the execution of the VRP problem.
    - Contains two directories:
        - `VRP_Cluster/` → clustering method for the resolution of the VRP problem.
        - `VRP_org/` → non clustering method for the resolution of the VRP problem.

        Inside each of these directories the same structure as the TSP and BPP problems directories. 


