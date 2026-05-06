import numpy as np

# Valores exactos
vals_exact = np.array([
    0.021379, -0.027731, 0.054223,
    0.067142, -0.362352, 0.000000,
    -0.038580, 0.006377, -0.021397, -0.153500
])

# Valores obtenidos con SHOTS
vals_shots = np.array([
    0.021800, -0.027981, 0.054591,
    0.066979, -0.362214, -0.000196,
    -0.038736, 0.006162, -0.021426, -0.153550
])

# Diferencia
diff = vals_shots - vals_exact

# MAE
mae = np.mean(np.abs(diff))

# Error máximo absoluto
max_err = np.max(np.abs(diff))

print(f"MAE: {mae:.6e}")
print(f"Error máximo absoluto: {max_err:.6e}")
