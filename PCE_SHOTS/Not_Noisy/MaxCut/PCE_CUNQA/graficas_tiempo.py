import sqlite3
import matplotlib.pyplot as plt
import os
from collections import defaultdict

# === CONFIGURACIÓN ===
DB_NAME = "MaxCut_results.db"

OUTPUT_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Not_Noisy/MaxCut/PCE_CUNQA/Images"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# === LEER BASE DE DATOS ===
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
    SELECT filename, tiempo_medio
    FROM MaxCut_results
""")

rows = c.fetchall()
conn.close()


# === ORGANIZAR DATOS ===
# clave = (optimizer, k, shots)
data_dict = defaultdict(list)

for filename, tiempo_medio in rows:

    name = filename.replace("Circuits_MaxCut_", "").replace(".json", "")
    parts = name.split("_")

    if len(parts) != 4:
        continue

    n = int(parts[0])
    optimizer = parts[1]
    k = int(parts[2])
    shots = int(parts[3])

    data_dict[(optimizer, k, shots)].append((n, tiempo_medio))


# === OBTENER OPTIMIZADORES ===
optimizers = sorted(set(key[0] for key in data_dict.keys()))

# === GRAFICAR ===
for optimizer in optimizers:

    plt.figure(figsize=(9,5))
    k_value = 2

    shots_values = sorted(
        set(key[2] for key in data_dict if key[0] == optimizer and key[1] == k_value)
    )

    colors = plt.cm.tab10.colors
    markers = ['o', 's', '^', 'D', 'v', 'P', 'X', '*', '<', '>']

    for shots in shots_values:

        key = (optimizer, k_value, shots)
        data = data_dict.get(key, [])

        if not data:
            continue

        data.sort(key=lambda x: x[0])

        n_vals = [d[0] for d in data]
        t_vals = [d[1] for d in data]

        idx = shots_values.index(shots)
        color = colors[idx % len(colors)]
        marker = markers[idx % len(markers)]

        plt.plot(
            n_vals,
            t_vals,
            marker=marker,
            color=color,
            linestyle='-',
            label=f"shots={shots}"
        )

    plt.ylim(0, 400000)
    plt.xlabel("Número de vértices")
    plt.ylabel("Tiempo medio (s)")
    plt.title(f"Tiempo de ejecución | Optimizer: {optimizer} | k=2")

    plt.grid(True, linestyle=":")
    plt.legend()

    plt.tight_layout()

    output_path = os.path.join(
        OUTPUT_DIR,
        f"Tiempos_{optimizer}_k2_shots.png"
    )

    plt.savefig(output_path, dpi=300)
    plt.close()

    print(f"[OK] Gráfico guardado: {output_path}")


print("\n📊 Gráficas generadas correctamente.")