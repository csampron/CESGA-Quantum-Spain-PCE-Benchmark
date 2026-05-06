#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_100_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_100_noisy0_shots2 --co-located

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_150_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_150_noisy0_shots2 --co-located

# MaxCut 200
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_200_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_200_noisy0_shots2 --co-located

# MaxCut 250
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_250_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_250_noisy0_shots2 --co-located

# MaxCut 300
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_300_noisy0_shots1 --co-located
qraise -n 3 -t 06:00:00  --simulator Aer --family_name family_circuits_MaxCut_300_noisy0_shots2 --co-located


echo "Todas las familias levantadas."
