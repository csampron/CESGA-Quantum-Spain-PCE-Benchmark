#!/usr/bin/env python3
# plot_vrp_dual.py
# Genera dos gráficas VRP: mejora penalizada (bench factible) y delta coste (bench infactible)

import sqlite3
import os
import numpy as np
import matplotlib.pyplot as plt
from collections import defaultdict

DB_NAME = "VRP_results.db"
FIG_DIR = "Images"
os.makedirs(FIG_DIR, exist_ok=True)

# ----------------------------
# LEER DATOS
# ----------------------------
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

c.execute("""
SELECT instance, optimizer, mejora_penalizada, delta_coste, benchmark_over_capacity
FROM VRP_results
ORDER BY optimizer, instance
""")

rows = c.fetchall()
conn.close()

if not rows:
    print("❌ No hay datos")
    exit(1)

# ----------------------------
# AGRUPAR POR OPTIMIZER
# ----------------------------
data_por_algoritmo = defaultdict(lambda: {
    "factibles": {"instances": [], "mejora": []},
    "infactibles": {"instances": [], "delta": []}
})

for inst, opt, mej, delta, bench_over in rows:
    d = data_por_algoritmo[opt]
    if bench_over == 0:
        d["factibles"]["instances"].append(inst)
        d["factibles"]["mejora"].append(mej)
    else:
        d["infactibles"]["instances"].append(inst)
        d["infactibles"]["delta"].append(delta)

# ----------------------------
# GRAFICAS
# ----------------------------
def graficar_barras(instances, valores, titulo, nombre_figura, color):
    plt.figure(figsize=(10,5))
    x = np.arange(len(instances))
    plt.bar(x, valores, color=color)
    plt.axhline(0, linestyle="--", color="black", linewidth=1)
    plt.xticks(x, instances, rotation=45)
    plt.ylabel("%")
    plt.title(titulo)
    plt.grid(True, linestyle="--", alpha=0.6)
    plt.tight_layout()
    plt.savefig(os.path.join(FIG_DIR, nombre_figura), dpi=300)
    plt.close()

# ----------------------------
# GENERAR GRAFICAS
# ----------------------------
for opt, d in data_por_algoritmo.items():
    print(f"📊 Generando gráficas VRP para {opt}")

    # 1️⃣ Mejora penalizada para benchmarks factibles
    if d["factibles"]["instances"]:
        graficar_barras(
            d["factibles"]["instances"],
            d["factibles"]["mejora"],
            f"{opt} – Mejora penalizada (bench factible)",
            f"{opt}_mejora_penalizada.png",
            color="steelblue"
        )

    # 2️⃣ Delta coste para benchmarks infactibles
    if d["infactibles"]["instances"]:
        graficar_barras(
            d["infactibles"]["instances"],
            d["infactibles"]["delta"],
            f"{opt} – Delta coste (bench infactible)",
            f"{opt}_delta_coste.png",
            color="crimson"
        )

print("✅ Gráficas VRP generadas")
