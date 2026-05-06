#!/bin/bash
#SBATCH -J finplot
#SBATCH -o finplot_%A_%a.out
#SBATCH -e finplot_%A_%a.err
#SBATCH --time=05:00:00
#SBATCH --nodes=1
#SBATCH --ntasks=1
#SBATCH --cpus-per-task=1
#SBATCH --array=0-29   # 5 tamaños × 6 familias = 30 tareas
#SBATCH --mem=3G
#SBATCH --partition=ilk

# =============================
# Módulos
# =============================
module load qmio/hpc gcc/12.3.0 networkx/3.3-python-3.11.9
module load qmio/hpc gcccore/12.3.0 matplotlib/3.6.3-python-3.11.9
module load qiskit/1.2.4-python-3.11.9

# =============================
# Listas de tamaños y shots
# =============================
SIZES=(10 20 40 50 60)
SHOTS_LIST=(100 1000 10000 100000 1000000 10000000)   # 6 familias por tamaño


NUM_FAM=6   # familias por tamaño
SEED=10    # seed fija

# =============================
# Calcular tamaño y family según SLURM_ARRAY_TASK_ID
# =============================
IDX=$SLURM_ARRAY_TASK_ID

# Índice de tamaño
SIZE_IDX=$(( IDX / NUM_FAM ))
SIZE=${SIZES[$SIZE_IDX]}

# Índice de family dentro del tamaño
FAMILY_IDX=$(( IDX % NUM_FAM ))
FAMILY_NUM=$(( FAMILY_IDX + 1 ))  # 1..5

# Construir nombre de family
FAMILY="family_circuits_MaxCut_${SIZE}_shots${FAMILY_NUM}"

# Obtener shots real
SHOTS=${SHOTS_LIST[$FAMILY_IDX]}

echo "=============================="
echo "Array ID: $IDX"
echo "Tamaño: $SIZE"
echo "Family: $FAMILY"
echo "Shots estimados: $SHOTS"
echo "Seed: $SEED"
echo "=============================="

# =============================
# Ejecutar script Python
# =============================
srun python -u multi_exp.py \
    --family "$FAMILY" \
    --problema MaxCut \
    --tamaño "$SIZE" \
    --k 4 \
    --shots "$SHOTS" \
    --seed "$SEED"

echo "Liberando QPUs de la familia: $FAMILY"
qdrop --family_name "$FAMILY"
echo "QPUs liberadas"

# =============================
# Mensaje final
# =============================
echo "Fecha fin: $(date)"
