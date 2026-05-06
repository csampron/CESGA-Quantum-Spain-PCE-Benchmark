#!/bin/bash
#SBATCH -J exp_circuits
#SBATCH -o logs/exp_%A_%a.out
#SBATCH -e logs/exp_%A_%a.err
#SBATCH --time=90:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=150G
#SBATCH --array=0-14

# ============================================================
# CONFIGURACIÓN INICIAL
# ============================================================

echo "==========================================="
echo "JOB ID        : $SLURM_JOB_ID"
echo "ARRAY TASK ID : $SLURM_ARRAY_TASK_ID"
echo "NODE          : $(hostname)"
echo "FECHA INICIO  : $(date)"
echo "==========================================="

set -e  # detener ejecución si hay error

# Crear carpeta logs si no existe
mkdir -p logs

# ============================================================
# CARGA DE MÓDULOS
# ============================================================

module purge
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9
module load qiskit/1.2.4-python-3.11.9

echo "Módulos cargados"

# ============================================================
# PARÁMETROS EXPERIMENTO
# ============================================================

SIZES=(100 150 200 250 300)
SHOTS_LIST=(10000 100000 1000000)

NUM_FAM=3
K=2
SEED=1
MAXITER=1000
NQPUS=3
PROBLEMA="MaxCut"

# ============================================================
# MAPEO ARRAY → (SIZE, SHOTS)
# ============================================================

# =============================
# Calcular tamaño y family según SLURM_ARRAY_TASK_ID
# =============================

IDX=$SLURM_ARRAY_TASK_ID

SIZE_IDX=$(( IDX / NUM_FAM ))
SIZE=${SIZES[$SIZE_IDX]}

FAMILY_IDX=$(( IDX % NUM_FAM ))
SHOTS=${SHOTS_LIST[$FAMILY_IDX]}

FAMILY_NUM=$(( FAMILY_IDX + 1 ))

FAMILY="family_circuits_MaxCut_${SIZE}_not_noisy_shots${FAMILY_NUM}"


echo "==========================================="
echo "Problema : $PROBLEMA"
echo "Tamaño   : $SIZE"
echo "Shots    : $SHOTS"
echo "k        : $K"
echo "QPUs     : $NQPUS"
echo "Family   : $FAMILY"
echo "Seed     : $SEED"
echo "==========================================="


# ============================================================
# EJECUCIÓN PYTHON
# ============================================================

echo "Iniciando experimento..."

srun python -u main_simul.py \
    --family "$FAMILY" \
    --problema "$PROBLEMA" \
    --tamaño "$SIZE" \
    --k "$K" \
    --shots "$SHOTS" \
    --nqpus "$NQPUS" \
    --maxiter "$MAXITER" \
    --seed "$SEED"


# ============================================================
# LIBERAR QPUs (siempre)
# ============================================================

echo "Liberando QPUs..."
qdrop --family_name "$FAMILY"
echo "QPUs liberadas"


echo "==========================================="
echo "✔ Experimento completado correctamente"
echo "FECHA FIN: $(date)"
echo "==========================================="