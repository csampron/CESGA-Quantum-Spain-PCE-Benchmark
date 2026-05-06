import os
import sys
import pandas as pd
import matplotlib.pyplot as plt

def graficar_coste(ruta_csv):
    """
    Genera una gráfica de la evolución del valor de la función de coste
    a lo largo de las iteraciones de un proceso de optimización.

    Parámetros:
    -----------
    ruta_csv : str
        Ruta del archivo CSV que contiene los datos. 
        El archivo debe tener dos columnas: 'iteracion' y 'valor_coste'.

    Resultado:
    -----------
    - Muestra una gráfica de la evolución del coste.
    - Guarda la figura como un archivo PNG con el mismo nombre del CSV.
    """

    # === 1. Verificar que el archivo exista ===
    if not os.path.exists(ruta_csv):
        print(f"❌ No se encontró el archivo: {ruta_csv}")
        return

    # === 2. Cargar el archivo CSV con pandas ===
    df = pd.read_csv(ruta_csv)

    # === 3. Verificar que el CSV tenga las columnas esperadas ===
    # Se espera que tenga al menos 'iteracion' y 'valor_coste'
    if not {"iteracion", "valor_coste"}.issubset(df.columns):
        print("❌ El CSV no tiene las columnas esperadas: 'iteracion' y 'valor_coste'")
        print("Columnas encontradas:", list(df.columns))
        return

    # === 4. Crear la figura y graficar ===
    plt.figure(figsize=(8, 5))  # tamaño de la figura
    plt.plot(
        df["iteracion"],           # eje X: número de iteración
        df["valor_coste"],         # eje Y: valor del coste
        marker='o',                # marcador circular por punto
        color='royalblue',         # color azul elegante
        linewidth=2                # grosor de línea
    )

    # === 5. Personalizar la gráfica ===
    plt.title("Evolución del valor de la función de coste")  # título de la gráfica
    plt.xlabel("Iteración")                                 # etiqueta del eje X
    plt.ylabel("Valor de la función de coste")               # etiqueta del eje Y
    plt.grid(True, linestyle="--", alpha=0.6)                # cuadrícula suave
    plt.tight_layout()                                       # ajustar márgenes automáticamente

    # === 6. Guardar y mostrar la gráfica ===
    # El PNG se guarda con el mismo nombre del CSV
    nombre_png = os.path.splitext(ruta_csv)[0] + "_grafica.png"
    plt.savefig(nombre_png, dpi=300)  # guardar imagen con alta resolución
    plt.show()                         # mostrar la figura en pantalla

    print(f"✅ Gráfica guardada en: {nombre_png}")


# === 7. Permitir ejecución directa desde terminal ===
if __name__ == "__main__":
    # Uso esperado desde consola:
    #   python graficar_coste.py historial_coste.csv
    if len(sys.argv) < 2:
        print("Uso: python graficar_coste.py <ruta_csv>")
    else:
        graficar_coste(sys.argv[1])


