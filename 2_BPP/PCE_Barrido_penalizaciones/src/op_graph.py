### ========================================================= ###
### Módulo: op_graph
### ========================================================= ###
###
### Funciones para trabajar con grafos en el contexto de
### optimización cuántica (PCE + VQE).
###
### Funcionalidades:
### - load_bpp: carga un archivo con los datos de un bin packing problem
###
### ========================================================= ###

def load_bpp(nombre_archivo):

    pesos = []

    with open(nombre_archivo, 'r') as archivo:
        num_items = int(archivo.readline().strip())
        Capacity = int(archivo.readline().strip())

        for linea in archivo:
            p = linea.strip()
            pesos.append(p)

    print("Num_items: " + str(num_items) +'\n')
    print("Capacity: " + str(Capacity) +'\n')
    print("Pesos: " + str(pesos) +'\n')

    return Capacity, pesos, num_items
