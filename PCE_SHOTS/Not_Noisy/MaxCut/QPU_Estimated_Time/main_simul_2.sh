#!/bin/bash
#SBATCH -J exp_circuits
#SBATCH -o logs/exp_%A_%a.out
#SBATCH -e logs/exp_%A_%a.err
#SBATCH --time=06:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --mem=20G
#SBATCH --array=0-9   # 5 tamaños × 6 familias = 30 tareas

# =============================
# Cargar módulos
# =============================
module purge
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9
module load qiskit/1.2.4-python-3.11.9

# =============================
# Listas de tamaños y shots
# =============================
SIZES=(100 150 200 250 300)
SHOTS_LIST=(1000 10000)   # 6 familias por tamaño

NUM_FAM=2   # familias por tamaño
SEED=1     # semilla fija
K=3     # k fijo
FAMILY_BASE="family_circuits_MaxCut"

# =============================
# Calcular tamaño y family según SLURM_ARRAY_TASK_ID
# =============================
IDX=$SLURM_ARRAY_TASK_ID

SIZE_IDX=$(( IDX / NUM_FAM ))
SIZE=${SIZES[$SIZE_IDX]}

FAMILY_IDX=$(( IDX % NUM_FAM ))
FAMILY_NUM=$(( FAMILY_IDX + 1 ))  # index 1-based para el nombre
FAMILY="${FAMILY_BASE}_${SIZE}_noisy0_shots${FAMILY_NUM}"

# Obtener shots correspondiente
SHOTS=${SHOTS_LIST[$FAMILY_IDX]}

echo "=============================="
echo "Array ID: $IDX"
echo "Tamaño: $SIZE"
echo "Family: $FAMILY"
echo "Shots: $SHOTS"
echo "k: $K"
echo "Seed: $SEED"
echo "=============================="

# =============================
# Ejecutar script Python que guarda JSON
# =============================
srun python -u main_data_circuits.py \
    --family "$FAMILY" \
    --tamaño "$SIZE" \
    --k "$K" \
    --shots "$SHOTS" \
    --nqpus 3 \
    --seed "$SEED"

# =============================
# Liberar QPUs
# =============================
echo "Liberando QPUs de la familia: $FAMILY"
qdrop --family_name "$FAMILY"
echo "QPUs liberadas"

echo "Fecha fin: $(date)"