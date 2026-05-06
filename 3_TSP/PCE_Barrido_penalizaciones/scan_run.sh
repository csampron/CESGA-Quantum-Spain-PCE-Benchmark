#!/bin/bash
#SBATCH -J scan_ab
#SBATCH --array=0-79
#SBATCH -o scan_ab_%A_%a.out
#SBATCH -e scan_ab_%A_%a.err
#SBATCH --time=24:00:00
#SBATCH --mem=50G


# IMPORTANTE: si se desea cambiar el número de combinaciones de parámetros o de repeticiones hay que modificar --array=0-(len(grid) x num_repeticiones)-1)

module purge

module load qmio/hpc gcc/12.3.0 hpcx-ompi flexiblas/3.3.0 boost cmake/3.27.6 gcccore/12.3.0 nlohmann_json/3.11.3 ninja/1.9.0 pybind11/2.13.6-python-3.11.9 qiskit/1.2.4-python-3.11.9
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9


srun python -u params_run.py
