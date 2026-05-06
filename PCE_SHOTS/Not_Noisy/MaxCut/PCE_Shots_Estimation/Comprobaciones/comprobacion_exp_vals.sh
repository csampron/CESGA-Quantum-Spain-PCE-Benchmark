#!/bin/bash
#SBATCH -J finplot
#SBATCH -o finplot_%j.out
#SBATCH -e finplot_%j.err
#SBATCH --time=05:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --mem=3G


# =============================
# Módulos
# =============================
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9
module load qiskit/1.2.4-python-3.11.9

# Ejecutar

srun python -u comprobacion_exp_vals.py 