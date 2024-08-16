import socket
import threading
import json

# Nodo de la red
class Node:
    def __init__(self, node_id, neighbors):
        self.node_id = node_id
        self.neighbors = neighbors  # Diccionario con el formato {neighbor_id: (ip, port)}
        self.received_messages = set()

    def listen(self):
        # Crear un socket para escuchar mensajes
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.bind(self.neighbors[self.node_id])

        while True:
            message, address = s.recvfrom(1024)
            message = json.loads(message.decode())
            
            # Si el mensaje ya fue recibido antes, ignorarlo
            if message['id'] in self.received_messages:
                continue
            
            self.received_messages.add(message['id'])
            print(f"Mensaje recibido en {self.node_id}: {message['payload']}")

            # Reenviar el mensaje a todos los vecinos, excepto al remitente
            for neighbor, addr in self.neighbors.items():
                if addr != address:
                    s.sendto(json.dumps(message).encode(), addr)

    def send_message(self, message):
        # Agregar un ID único al mensaje
        message['id'] = f"{self.node_id}-{message['id']}"
        self.received_messages.add(message['id'])

        # Enviar el mensaje a todos los vecinos
        for addr in self.neighbors.values():
            s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
            s.sendto(json.dumps(message).encode(), addr)

# Ejemplo de configuración de nodos
if __name__ == "__main__":
    neighbors_A = {
        'B': ('localhost', 5001),
        'C': ('localhost', 5002)
    }
    neighbors_B = {
        'A': ('localhost', 5000),
        'C': ('localhost', 5002)
    }
    neighbors_C = {
        'A': ('localhost', 5000),
        'B': ('localhost', 5001)
    }

    # Crear nodos
    node_A = Node('A', neighbors_A)
    node_B = Node('B', neighbors_B)
    node_C = Node('C', neighbors_C)

    # Hilos para que cada nodo escuche mensajes
    threading.Thread(target=node_A.listen).start()
    threading.Thread(target=node_B.listen).start()
    threading.Thread(target=node_C.listen).start()

    # Enviar un mensaje desde el nodo A
    node_A.send_message({'id': '1', 'payload': 'Hola desde A'})
