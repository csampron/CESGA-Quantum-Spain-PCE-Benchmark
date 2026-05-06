#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 10
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_10_noisy_shots1 --co-located
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_10_noisy_shots2 --co-located

# MaxCut 20
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_20_noisy_shots1 --co-located
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_20_noisy_shots2 --co-located

# MaxCut 40
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_40_noisy_shots1 --co-located
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_40_noisy_shots2 --co-located  

# MaxCut 50
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_50_noisy_shots1 --co-located
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_50_noisy_shots2 --co-located

# MaxCut 60
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_60_noisy_shots1 --co-located
qraise -n 3 -t 02:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_60_noisy_shots2 --co-located

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_100_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_100_noisy0_shots2 --co-located

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_150_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_150_noisy0_shots2 --co-located

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_200_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_200_noisy0_shots2 --co-located

# MaxCut 250
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_250_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_250_noisy0_shots2 --co-located

# MaxCut 300
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_300_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --noise-prop /mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Noisy/Sherbrooke.json --family_name family_circuits_MaxCut_300_noisy0_shots2 --co-located


echo "Todas las familias levantadas."
