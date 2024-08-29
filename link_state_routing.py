import threading
import socket
import json
import time

class Node:
    def __init__(self, node_id, neighbors):
        self.node_id = node_id
        self.neighbors = {n: addr for n, (_, addr) in neighbors.items()}  # Diccionario con formato {neighbor_id: (ip, port)}
        self.topology = {node_id: {n: peso for n, (peso, _) in neighbors.items()}}  # Solo los pesos
        self.distances = {node_id: 0}  # Distancias desde sí mismo
        self.received_messages = set()  # Para evitar procesar mensajes duplicados
        self.lock = threading.Lock()

        # Asegurarse de que el nodo tiene su propia dirección en el diccionario de vecinos
        if node_id not in self.neighbors:
            raise ValueError(f"El nodo {node_id} no tiene su propia dirección configurada en 'neighbors'.")

    def listen(self):
        """Escucha mensajes entrantes y procesa según su tipo."""
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self.neighbors[self.node_id])

        while True:
            message, address = s.recvfrom(1024)
            message = json.loads(message.decode())

            if message['id'] in self.received_messages:
                continue

            self.received_messages.add(message['id'])

            if message['type'] == 'TOPOLOGY':
                self.update_topology(message['from'], message['payload'])

            elif message['type'] == 'ECHO':
                print(f"ECHO recibido en {self.node_id} desde {message['from']}")
                if message['hops'] > 0:
                    self.forward_message(message)

            elif message['type'] == 'MESSAGE':
                print(f"Mensaje para {self.node_id}: {message['payload']}")

    def send_topology(self):
        """Envía la topología conocida a todos los vecinos."""
        message = {
            'type': 'TOPOLOGY',
            'from': self.node_id,
            'to': None,
            'hops': 3,  # Número de saltos máximo
            'id': f"{self.node_id}-topo-{time.time()}",
            'headers': [],
            'payload': self.topology[self.node_id]
        }
        self.broadcast_message(message)

    def update_topology(self, node_id, new_neighbors):
        """Actualiza la topología y recalcula las distancias usando Dijkstra."""
        with self.lock:
            self.topology[node_id] = new_neighbors
            self.recalculate_distances()

    def recalculate_distances(self):
        """Recalcula las rutas más cortas usando el algoritmo de Dijkstra."""
        self.distances = self.dijkstra(self.topology, self.node_id)
        print(f"Tabla de ruteo en {self.node_id}: {self.distances}")

    def dijkstra(self, graph, start):
        """Algoritmo de Dijkstra para encontrar rutas más cortas."""
        distancias = {nodo: float('inf') for nodo in graph}
        distancias[start] = 0

        no_visitados = set(graph)

        while no_visitados:
            nodo_actual = min(no_visitados, key=lambda nodo: distancias[nodo])
            no_visitados.remove(nodo_actual)

            for vecino in graph.get(nodo_actual, {}):
                peso = graph[nodo_actual][vecino]

                if isinstance(peso, str):
                    try:
                        peso = float(peso)  # Intenta convertir a float si es necesario
                    except ValueError:
                        raise ValueError(f"El peso para la arista de {nodo_actual} a {vecino} no es un número: {peso}")
                elif isinstance(peso, (tuple, list)):
                    peso = float(peso[0])  # Si es una tupla o lista, tomar el primer elemento

                distancia_alternativa = distancias[nodo_actual] + peso
                if distancia_alternativa < distancias.get(vecino, float('inf')):
                    distancias[vecino] = distancia_alternativa

        return distancias

    def broadcast_message(self, message):
        """Envía un mensaje a todos los vecinos."""
        for addr in self.neighbors.values():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(json.dumps(message).encode(), addr)

    def forward_message(self, message):
        """Reenvía un mensaje a los vecinos restantes."""
        message['hops'] -= 1
        self.broadcast_message(message)

if __name__ == "__main__":
    # Configuración inicial de los nodos y vecinos
    neighbors_A = {
        'A': (1, ('localhost', 5000)),  # Peso, dirección IP y puerto
        'B': (1, ('localhost', 5001)),
        'C': (4, ('localhost', 5002))
    }
    neighbors_B = {
        'A': (1, ('localhost', 5000)),
        'B': (1, ('localhost', 5001)),  # Asegúrate de incluir la dirección del nodo 'B' en su propio diccionario
        'C': (2, ('localhost', 5002))
    }
    neighbors_C = {
        'A': (4, ('localhost', 5000)),
        'B': (2, ('localhost', 5001)),
        'C': (1, ('localhost', 5002))  # Asegúrate de incluir la dirección del nodo 'C' en su propio diccionario
    }

    # Creación de nodos
    node_A = Node('A', neighbors_A)
    node_B = Node('B', neighbors_B)
    node_C = Node('C', neighbors_C)

    # Iniciar hilos para escuchar mensajes en cada nodo
    threading.Thread(target=node_A.listen).start()
    threading.Thread(target=node_B.listen).start()
    threading.Thread(target=node_C.listen).start()

    time.sleep(2)  # Espera para asegurarse de que todos los nodos estén listos para recibir

    # Enviar la topología desde cada nodo
    node_A.send_topology()
    node_B.send_topology()
    node_C.send_topology()