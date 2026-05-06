import sqlite3
import json
import os
import numpy as np
import re

# === CONFIGURACIÓN ===
RESULTS_DIR = "Resultados"
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
# Claves como enteros: número de vértices n
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

# === BUSCAR ARCHIVOS JSON DE RESULTADOS ===
json_files = []
for root, dirs, files in os.walk(RESULTS_DIR):
    for file in files:
        if file.startswith("MaxCut_") and file.endswith(".json"):
            json_files.append(os.path.join(root, file))

print(f"📁 Se encontraron {len(json_files)} archivos JSON de resultados.\n")

# === PROCESAR CADA ARCHIVO ===
conn = sqlite3.connect(DB_NAME)
c = conn.cursor()

for ruta_json in json_files:
    try:
        with open(ruta_json, "r", encoding="utf-8") as f:
            data = json.load(f)

        resultados = data.get("resultados", [])
        if not resultados:
            print(f"⚠️ Sin resultados en: {ruta_json}")
            continue

        # === Calcular estadísticas ===
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

        # === Extraer n del filename (entero exacto) ===
        # Formatos esperados: MaxCut_10_COBYLA_2.json, MaxCut_100_SOMETHING_3.json, etc.
        m = re.match(r"MaxCut_(\d+)_([A-Za-z0-9]+)_(\d+)\.json", filename)
        n_value = None
        if m:
            n_value = int(m.group(1))
        else:
            # Intentar extracción genérica de "MaxCut_<n>"
            m2 = re.search(r"MaxCut_(\d+)", filename)
            if m2:
                n_value = int(m2.group(1))

        if n_value is None:
            print(f"⚠️ No se pudo extraer n del filename: {filename} — saltando")
            continue

        # === Obtener sol_exact usando n como clave entero ===
        sol_exact = EXACT_SOLUTIONS.get(n_value)
        if sol_exact is None:
            print(f"⚠️ No hay sol_exact para n={n_value} (archivo: {filename}) — saltando")
            continue

        # === Calcular razones ===
        r = mejor_valor / sol_exact if sol_exact else None
        r_media = media_sol / sol_exact if sol_exact else None

        # === Insertar o actualizar en la base de datos ===
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

        if len(params) != 10:
            raise ValueError(f"Parámetros inesperados (esperados 10): {len(params)} para {filename}")

        c.execute('''
            INSERT OR REPLACE INTO MaxCut_results 
            (filename, n_ejecuciones, tiempo_medio, media_sol, desviacion_sol, r_media, mejor_sol, r, mejor_bitstring, mejor_params)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', params)

        print(f"✅ Insertado: {filename} | n={n_value} | mejor_sol={mejor_valor} | sol_exact={sol_exact} | r={r:.6f}")

    except Exception as e:
        print(f"❌ Error procesando {ruta_json}: {e}")

conn.commit()
conn.close()

print("\n📊 Base de datos actualizada correctamente.")
