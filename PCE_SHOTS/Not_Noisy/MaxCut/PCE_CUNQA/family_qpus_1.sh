#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 10
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_not_noisy_shots1 --co-located
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_not_noisy_shots2 --co-located
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_not_noisy_shots3 --co-located

# MaxCut 20
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_not_noisy_shots1 --co-located
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_not_noisy_shots2 --co-located
qraise -n 3 -t 48:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_not_noisy_shots3 --co-located

# MaxCut 40
qraise -n 3 -t 90:00:00  --simulator Aer --family_name family_circuits_MaxCut_40_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00  --simulator Aer --family_name family_circuits_MaxCut_40_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00  --simulator Aer --family_name family_circuits_MaxCut_40_not_noisy_shots3 --co-located

# MaxCut 50
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_50_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_50_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_50_not_noisy_shots3 --co-located

# MaxCut 60
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_60_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_60_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_60_not_noisy_shots3 --co-located


echo "Todas las familias levantadas."
