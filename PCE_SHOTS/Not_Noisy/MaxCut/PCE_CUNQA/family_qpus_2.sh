#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 100
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_100_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_100_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_100_not_noisy_shots3 --co-located

# MaxCut 150
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_150_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_150_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_150_not_noisy_shots3 --co-located

# MaxCut 200
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_200_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_200_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_200_not_noisy_shots3 --co-located

# MaxCut 250
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_250_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_250_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_250_not_noisy_shots3 --co-located

# MaxCut 300
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_300_not_noisy_shots1 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_300_not_noisy_shots2 --co-located
qraise -n 3 -t 90:00:00 -c 4 --simulator Aer --family_name family_circuits_MaxCut_300_not_noisy_shots3 --co-located


echo "Todas las familias levantadas."
