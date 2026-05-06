import sqlite3
import json
import os
import numpy as np
import re

# === CONFIGURACIÓN ===
BASE_DIR = "/mnt/netapp1/Store_CESGA/home/cesga/falonso/PCE_SHOTS/Not_Noisy/MaxCut/PCE_CUNQA"
DB_NAME = "MaxCut_results.db"

# === CREAR / CONECTAR A LA BASE DE DATOS ===
with sqlite3.connect(DB_NAME) as conn:
    c = conn.cursor()
    c.execute('''
    CREATE TABLE IF NOT EXISTS MaxCut_results (
        filename TEXT PRIMARY KEY,
        n_ejecuciones INTEGER,
        tiempo_medio REAL,
        media_sol REAL,
        desviacion_sol REAL,
        r_media REAL,
        mejor_sol REAL,
        r REAL,
        mejor_bitstring TEXT,
        mejor_params TEXT
    )
    ''')
    conn.commit()

# === VALORES EXACTOS DE MAXCUT (óptimos conocidos) ===
EXACT_SOLUTIONS = {
    10: 25,
    20: 97,
    40: 355,
    50: 602,
    60: 852,
    100: 2224,
    150: 4899,
    200: 8717,
    250: 13460,
    300: 19267
}

# === CARPETAS A EXPLORAR (con etiqueta) ===
folders_to_search = [
    ("Circuits", os.path.join(BASE_DIR, "Resultados", "MaxCut"))
]

# === RECOLECTAR TODOS LOS JSON DE MAXCUT ===
json_files = []
for tag, folder in folders_to_search:
    for root, dirs, files in os.walk(folder):
        for file in files:
            if file.startswith("MaxCut_") and file.endswith(".json"):
                json_files.append((tag, os.path.join(root, file)))

print(f"📁 Se encontraron {len(json_files)} archivos JSON de resultados.\n")

# === PROCESAR CADA ARCHIVO ===
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

for tag, ruta_json in json_files:
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        resultados = data.get("resultados", [])
        if not resultados:
            print(f"⚠️ Sin resultados en: {ruta_json}")
            continue

        n_ejecuciones = len(resultados)
        tiempos = [r.get("elapsed_time", 0) for r in resultados]
        cortes = [r.get("refined_cut", 0) for r in resultados]

        tiempo_medio = float(np.mean(tiempos)) if tiempos else 0.0
        media_sol = float(np.mean(cortes)) if cortes else 0.0
        desviacion_sol = float(np.std(cortes)) if cortes else 0.0

        mejor_sol = max(resultados, key=lambda r: r.get("refined_cut", float("-inf")))
        mejor_valor = float(mejor_sol.get("refined_cut", 0))
        mejor_bitstring = mejor_sol.get("refined_bitstring", [])
        mejor_params = mejor_sol.get("params", [])

        filename = os.path.basename(ruta_json)
        filename = f"{tag}_{filename}"  # <-- añadimos prefijo

        # === Extraer n del filename ===
        m = re.match(r"MaxCut_(\d+)_([A-Za-z0-9]+)_(\d+)\.json", os.path.basename(ruta_json))
        n_value = None
        if m:
            n_value = int(m.group(1))
        else:
            m2 = re.search(r"MaxCut_(\d+)", os.path.basename(ruta_json))
            if m2:
                n_value = int(m2.group(1))

        if n_value is None or n_value not in EXACT_SOLUTIONS:
            print(f"⚠️ n={n_value} no está en EXACT_SOLUTIONS — saltando")
            continue


        sol_exact = EXACT_SOLUTIONS.get(n_value)
        if sol_exact is None:
            print(f"⚠️ No hay sol_exact para n={n_value} (archivo: {filename}) — saltando")
            continue

        r = mejor_valor / sol_exact if sol_exact else None
        r_media = media_sol / sol_exact if sol_exact else None

        params = (
            filename,
            n_ejecuciones,
            tiempo_medio,
            media_sol,
            desviacion_sol,
            r_media,
            mejor_valor,
            r,
            json.dumps(mejor_bitstring),
            json.dumps(mejor_params)
        )

        c.execute('''
            INSERT OR REPLACE INTO MaxCut_results 
            (filename, n_ejecuciones, tiempo_medio, media_sol, desviacion_sol, r_media, mejor_sol, r, mejor_bitstring, mejor_params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', params)

        # === 🔥 LÍNEAS AÑADIDAS: MOSTRAR media_sol y tiempo_medio ===
        print(f"➕ Media solución: {media_sol:.4f}")
        print(f"⏱ Tiempo medio: {tiempo_medio:.4f} s")

        print(f"✅ Insertado: {filename} | n={n_value} | mejor_sol={mejor_valor} | sol_exact={sol_exact} | r={r:.6f}\n")

    except Exception as e:
        print(f"❌ Error procesando {ruta_json}: {e}")

conn.commit()
conn.close()
print("\n📊 Base de datos actualizada correctamente.")
