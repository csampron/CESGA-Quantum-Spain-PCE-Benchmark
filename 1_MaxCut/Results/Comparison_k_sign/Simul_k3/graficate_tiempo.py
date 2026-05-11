import sqlite3
import re
import matplotlib.pyplot as plt
import os


DB_NAME = "MaxCut_results.db"


def extract_times_from_db(vertex_sizes=[], optimizers=[]):

    # Diccionario: optimizador → lista ordenada según vertex_sizes
    times = {opt: [] for opt in optimizers}

    # Conectar con la base de datos
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()

    for V in vertex_sizes:
        for opt in optimizers:

            # Query para obtener tiempo_medio
            c.execute("""
                SELECT filename, tiempo_medio
                FROM MaxCut_results
                WHERE filename LIKE ?
            """, (f"%MaxCut_{V}_{opt}_%",))

            rows = c.fetchall()

            if not rows:
                print(f"[WARNING] No hay registros para V={V}, opt={opt}")
                times[opt].append(None)
                continue

            # Extraer lista de tiempos medios
            tiempos = []
            for filename, tiempo_medio in rows:
                if tiempo_medio is not None:
                    tiempos.append(tiempo_medio)

            if tiempos:
                mean_time = sum(tiempos) / len(tiempos)
            else:
                mean_time = None

            times[opt].append(mean_time)

    conn.close()
    return times



def plot_times_from_db(vertex_sizes=[], optimizers=[]):

    output_dir = "Your_route/z_MaxCut/A_DIFFERENTIAL_COMPARISON/Comparison_k/Simul_k2"
    os.makedirs(output_dir, exist_ok=True)

    times = extract_times_from_db(vertex_sizes, optimizers)

    for opt in optimizers:
        Y = times[opt]

        if all(v is None for v in Y):
            print(f"[WARNING] No hay datos válidos para {opt}")
            continue

        plt.figure(figsize=(8,5))
        plt.plot(vertex_sizes, Y, marker="o")
        plt.xlabel("Número de vértices")
        plt.ylabel("Tiempo medio (s)")
        plt.title(f"Tiempo de ejecución - {opt} - k=2")
        plt.grid(True, linestyle="--", alpha=0.5)
        plt.tight_layout()

        out = os.path.join(output_dir, f"Tiempos_{opt}_k2.png")
        plt.savefig(out)
        plt.close()
        print(f"[OK] Gráfico generado: {out}")


# =============================
# EJECUCIÓN
# =============================

vertex_sizes = [10, 20, 40, 50, 60, 100, 150, 200, 250, 300]
optimizers = ["DIFFERENTIALEVOLUTION"]

plot_times_from_db(
    vertex_sizes=vertex_sizes,
    optimizers=optimizers
)
