def check_capacity_benchmark(solutions, capacities):
    """
    Comprueba si las soluciones de un benchmark CVRP respetan la capacidad.

    Parámetros
    ----------
    solutions : list
        Lista de soluciones. Cada solución es una lista de rutas,
        y cada ruta es una lista de arcos [i, j].
    capacities : list[int]
        Capacidad asociada a cada solución (mismo orden).

    Retorna
    -------
    None (imprime el resultado)
    """

    assert len(solutions) == len(capacities), "Número de soluciones y capacidades no coincide"

    print("=== CHEQUEO DE CAPACIDAD CVRP ===\n")

    for idx, (solution, capacity) in enumerate(zip(solutions, capacities), start=1):
        print(f"Solución {idx} | Capacidad = {capacity}")

        feasible = True

        for r_idx, route in enumerate(solution):
            # Extraer nodos visitados (excluyendo depot)
            visited_nodes = set()

            for i, j in route:
                if i != 0:
                    visited_nodes.add(i)
                if j != 0:
                    visited_nodes.add(j)

            load = len(visited_nodes)

            if load > capacity:
                feasible = False
                print(
                    f"  ❌ Ruta {r_idx}: carga {load} > capacidad {capacity} | nodos = {sorted(visited_nodes)}"
                )
            else:
                print(
                    f"  ✅ Ruta {r_idx}: carga {load}/{capacity} | nodos = {sorted(visited_nodes)}"
                )

        if feasible:
            print("  ✅ Solución FACTIBLE\n")
        else:
            print("  ❌ Solución NO factible\n")



solutions_bench = [
    [[[0, 1], [1, 0]], [[0, 2], [2, 3], [3, 0]]],
    [[[0, 1], [1, 0]], [[0, 2], [2, 3], [3, 0]]],
    [[[0, 1], [1, 4], [4, 0]], [[0, 3], [3, 2], [2, 0]]],
    [[[0, 2], [2, 0]], [[0, 4], [4, 1], [1, 3], [3, 0]]],
    [[[0, 1], [1, 5], [5, 2], [2, 0]], [[0, 4], [4, 3], [3, 0]]],
    [[[0, 1], [1, 0]], [[0, 5], [5, 4], [4, 2], [2, 3], [3, 0]]],
    [[[0, 2], [2, 3], [3, 1], [1, 6], [6, 4], [4, 0]], [[0, 5], [5, 0]]],
    [[[0, 1], [1, 2], [2, 3], [3, 4], [4, 5], [5, 0]], [[0, 6], [6, 0]]],
    [[[0, 1], [1, 6], [6, 2], [2, 7], [7, 5], [5, 0]], [[0, 3], [3, 4], [4, 0]]],
    [[[0, 4], [4, 1], [1, 3], [3, 2], [2, 7], [7, 5], [5, 0]], [[0, 6], [6, 0]]]
]

capacities = [3, 3, 3, 3, 3, 4, 4, 4, 4, 5]

check_capacity_benchmark(solutions_bench, capacities)



solutions_pce = [
    [[[0, 1], [1, 3],[3, 2], [2, 0]]],
    [[[0, 1], [1, 2],[2, 3],[3, 0]]],
    [[[0, 3], [3, 2], [2, 0]], [[0, 1], [1, 4], [4, 0]]],
    [[[0, 3], [3, 2], [2, 0]], [[0, 1], [1, 4], [4, 0]]],
    [[[0, 4], [4, 3], [3, 0]], [[0, 2], [2, 5], [5, 1], [1, 0]]],
    [[[0, 3], [3, 1], [1, 0]], [[0, 2], [2, 4], [4, 5], [5, 0]]],
    [[[0, 3], [3, 2], [2, 1], [1, 6], [6, 0]], [[5, 0], [0, 4], [4, 5]]],
    [[[0, 1], [1, 5], [5, 2], [2, 3], [3, 0]], [[0, 4], [4, 6], [6, 0]]],
    [[[0, 7], [7, 2], [2, 3], [3, 0]], [[0, 5], [5, 6], [6, 1], [1, 4], [4, 0]]],
    [[[3, 7], [7, 6], [6, 0], [0, 1], [1, 2], [2, 3]], [[5, 0], [0, 4], [4, 0]]]
]

#check_capacity_benchmark(solutions_pce, capacities)