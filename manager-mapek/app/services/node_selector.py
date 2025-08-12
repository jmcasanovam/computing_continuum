from app.strategies.least_users import LeastUsersStrategy
from app.strategies.weighted_score import WeightedScoreStrategy
from app.services.node_monitor import nodes_status
from kubernetes import client, config


class NodeSelector:
    def __init__(self, strategy_name):
        self.strategy = self._load_strategy(strategy_name)

    def _load_strategy(self, name):
        if name == "least_users":
            return LeastUsersStrategy()
        elif name == "weighted":
            return WeightedScoreStrategy()
        raise ValueError("Estrategia desconocida")
    
    def get_node_roles(self):
        """Obtiene los roles de los nodos a partir de las etiquetas."""
        roles = {}
        try:
            config.load_incluster_config()  # Carga la configuración del clúster
            v1 = client.CoreV1Api()

            # Obtiene la lista de nodos
            nodes = v1.list_node().items
            for node in nodes:
                if 'node-type' in node.metadata.labels:
                    roles[node.status.addresses[0].address] = node.metadata.labels['node-type']
        except Exception as e:
            print(f"Error al obtener roles de nodos: {e}")
        return roles

    def select_node(self):
        node_roles = self.get_node_roles()
        online_nodes_info = [(ip, info) for ip, info in nodes_status.items() if info["status"] == "online"]
        
        priority_order = ["edge", "fog", "cloud"]
        
        for role in priority_order:
            candidates_in_role = [
                (ip, info) for ip, info in online_nodes_info
                if node_roles.get(ip) == role
            ]
            if candidates_in_role:
                print(f"[DEBUG] Encontrados {len(candidates_in_role)} candidatos en la categoría '{role}'.")
            else:
                print(f"[DEBUG] No hay candidatos en la categoría '{role}'. Pasando al siguiente rol.")

            if candidates_in_role:
                # Aplicamos la estrategia solo a los candidatos de este rol
                selected_node = self.strategy.select_node(candidates_in_role)
                if selected_node:
                    selected_ip, _ = selected_node
                    print(f"[DEBUG] Nodo seleccionado en la categoría '{role}': {selected_ip}")
                    print(f"[DEBUG] Estado del nodo seleccionado: {nodes_status[selected_ip]}")
                    return selected_node # Devuelve (ip, data)
        
        # Si no se encuentra ningún nodo en ninguna de las categorías, devolver None
        return None