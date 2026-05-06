#!/bin/bash

# ============================================================
# Levantar todas las familias de QPUs necesarias
# ============================================================

# MaxCut 10
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_10_shots6 --co-located


# MaxCut 20
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots6 --co-located


# MaxCut 40
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_40_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_40_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_40_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_40_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_40_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_20_shots6 --co-located


# MaxCut 50
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_50_shots6 --co-located


# MaxCut 60
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots1 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots2 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots3 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots4 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots5 --co-located
qraise -n 3 -t 02:00:00 --simulator Aer --family_name family_circuits_MaxCut_60_shots6 --co-located



echo "Todas las familias levantadas."
