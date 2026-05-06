import os
import json
import matplotlib.pyplot as plt

BASE_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj_reg/PCE_Barrido_qubits+1/Experimentos"
OUT_DIR  = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/z_BPP/PCE_BPP_yj_reg/PCE_Barrido_qubits+1"

m_values = []
alpha_values = []

# Recorremos todos los m_
for m_dir in sorted(os.listdir(BASE_DIR)):
    if not m_dir.startswith("m_"):
        continue

    m_path = os.path.join(BASE_DIR, m_dir)
    alphas_m = []

    for root, _, files in os.walk(m_path):
        for file in files:
            if file.endswith(".json"):
                json_path = os.path.join(root, file)
                try:
                    with open(json_path, "r") as f:
                        data = json.load(f)

                    for comb in data.get("best_combinations", []):
                        alpha = comb.get("alpha")
                        beta  = comb.get("beta")

                        if alpha is not None and beta is not None:
                            if 0.7 < beta <= 0.8:
                                alphas_m.append(alpha)

                except Exception as e:
                    print(f"Error leyendo {json_path}: {e}")

    # Guardamos puntos (uno por alpha)
    for alpha in alphas_m:
        m_values.append(m_dir)
        alpha_values.append(alpha)

# --- Gráfica ---
plt.figure(figsize=(10, 6))
plt.scatter(m_values, alpha_values)
plt.xlabel("m")
plt.ylabel("alpha")
plt.title("Alpha para beta ∈ [0.6, 0.8] por m")
plt.grid(True)
plt.tight_layout()

out_png = os.path.join(OUT_DIR, "alpha_vs_m_beta_0.6_0.8.png")
plt.savefig(out_png, dpi=300)
plt.close()

print(f"Gráfico guardado en: {out_png}")
