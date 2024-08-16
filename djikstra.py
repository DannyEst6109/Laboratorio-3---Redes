def dijkstra(graph, start):
    distancias = {nodo: float('inf') for nodo in graph}
    distancias[start] = 0

    no_visitados = set(graph)

    while no_visitados:
        nodo_actual = min(no_visitados, key=lambda nodo: distancias[nodo])
        
        no_visitados.remove(nodo_actual)

        for vecino, peso in graph[nodo_actual].items():
            distancia_alternativa = distancias[nodo_actual] + peso
            if distancia_alternativa < distancias[vecino]:
                distancias[vecino] = distancia_alternativa

    return distancias

if __name__ == "__main__":
    
    graph = {
        'A': {'B': 1, 'C': 4},
        'B': {'A': 1, 'C': 2, 'D': 5},
        'C': {'A': 4, 'B': 2, 'D': 1},
        'D': {'B': 5, 'C': 1}
    }

    start_node = 'A'
    distances = dijkstra(graph, start_node)

    print(f"Distancias desde el nodo {start_node}: {distances}")