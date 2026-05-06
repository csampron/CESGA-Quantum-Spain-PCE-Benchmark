#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 100
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_100_shots6 --co-located


# MaxCut 150
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_150_shots6 --co-located


# MaxCut 200
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_200_shots6 --co-located


# MaxCut 250
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_250_shots6 --co-located


# MaxCut 300
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_300_shots6 --co-located



echo "Todas las familias levantadas."
