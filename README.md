# CESGA-Quantum-Spain-PCE-Benchmark


<p align="center">
  <a>
    <img src="https://img.shields.io/badge/os-linux-blue" alt="Python version" height="18">
  </a>
  <a>
    <img src="https://img.shields.io/badge/python-3.9-blue.svg" alt="Python version" height="18">
  </a>
  <a href="cesga-quantum-spain.github.io/cunqa/">
    <img src="https://img.shields.io/badge/docs-blue.svg" alt="Python version" height="18">
  </a>
</p>

<br>

<p>
    <div align="center">
      <a href="https://www.cesga.es/">
        <picture>
          <source media="(prefers-color-scheme: dark)" srcset="docs/source/_static/logo_cesga_blanco.png" width="200" height="50">
          <source media="(prefers-color-scheme: light)" srcset="docs/source/_static/logo_cesga_negro.png" width="200" height="50">
          <img src="docs/source/_static/logo_cesga_negro.png" width="30%" style="display: inline-block;" alt="CESGA logo">
        </picture>
      </a>
      <img src="data:image/gif;base64,R0lGODlhAQABAAD/ACwAAAAAAQABAAACADs=" width="40">
      <a href="https://quantumspain-project.es/">
        <picture>
          <source media="(prefers-color-scheme: dark)" srcset="docs/source/_static/QuantumSpain_logo_white.png" width="240" height="50">
          <source media="(prefers-color-scheme: light)" srcset="docs/source/_static/QuantumSpain_logo_color.png" width="240" height="50">
          <img src="docs/source/_static/QuantumSpain_logo_white.png" width="30%" style="display: inline-block;" alt="QuantumSpain logo">
        </picture>
      </a>
    </div>
</p>


#
In this repository you can find the code used to get the results shown in the paper <i>Benchmark of Pauli Correlation Encoding for different optimisation problems</i>.

The repository is organized as followed:

- `1_MaxCut`: Code used for the execution of the MaxCut problem.
    - `Results`: Directory with plots, results and the code used to obtain such plots and results
    - `PCE`:
        - `init_cunqa.sh` to download dependencies
        - `main_simul.sh` to execute the program
        - `src/` contains all the main modules to prepare, execute and analyse the experiments, it includes:
            - `auxiliar.py` → Auxiliar functions, including calculation of the number of qubits and coding of Hamiltonians.  
            - `exe_experiments.py` → Generation of experiment combinations and automated execution.
            - `grafica_csv.py` → Functions to generate figures based on the results shown on a CSV file. 
            - `utilities.py` → Classical optimisation (Powell, COBYLA, Differential Evolution, etc.) and callbacks.
            - `tensor_exp_value.py` → Tensor construction of the computational basis and qubits combinations.
            - `circuit_builder.py` → Class used to build and compile parametric circuits. 
            - `graphs/` → Instances of the MaxCut problem used on the benchmark.

- `2_BPP`: Code used for the execution of the BPP problem.
    - Uses the same structure as the `1_MaxCut/` directory with the addition of two new directories:
        - `Parameter_swipe_alpha_beta/` → Code used to perform a parameter swipe of alpha and beta.
        - `Parameter_swipe_penalties/` → Code used to perform a parameter swipe on the lambda penalties of the cost function.

- `3_TSP`: Code used for the execution of the TSP problem.
    - Uses the same structure as the `2_BPP/` directory.

- `4_VRP`: Code used for the execution of the VRP problem.
    - Contains two directories:
        - `VRP_Cluster/` → clustering method for the resolution of the VRP problem.
        - `VRP_org/` → non clustering method for the resolution of the VRP problem.

        Inside each of these directories the same structure as the TSP and BPP problems directories.

- `PCE_SHOTS`: Code used for the execution of the MaxCut problem with shots and noisy simulation
    - Follows the same structure as the `1_MaxCut` directory but allows execution with simulated noise and shots.


### How to execute on HPC environment

In order to execute a problem of your liking you must change the `main_simul.py` file to your desired problem specifications
the following represents a given specification:

```console
Problema = ["MaxCut"]             # Type of problem, in this case, instead of changing this just execute the directory of the desired problem
Tamaño = [10]                     # Number of nodes on the graph, check the `graphs/` directory to see the available problem sizes
Optimiz = ["POWELL"]              # Classical algorithm optimizer, you can choose any optimizer you desire as long as their behavour is described on the `utilities.py` file
k = [2]                           # PCE compression parameter

```

After chosing the desired problem to solve:

1. Go to PCE directory on terminal `cd PCE`
2. Execute the comand `source init_cunqa.sh`
3. Execute the comand `sbatch main_simul.sh`, you can change the SBATCH specs inside this file



