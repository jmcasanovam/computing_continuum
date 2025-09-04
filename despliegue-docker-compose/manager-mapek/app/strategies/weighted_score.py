from .base import NodeSelectionStrategy

class WeightedScoreStrategy(NodeSelectionStrategy):
    def select_node(self, nodes_info):
        def score(data):
            load = data["current_load"]
            return (load["active_users_count"] * 0.5 +
                    load["cpu_load"] * 0.3 +
                    load["memory_usage"] * 0.2)

        # La lista nodes_info ya ha sido filtrada.
        if not nodes_info:
            return None # Si no hay candidatos, no hay nada que seleccionar
        
        # El min() seleccionará el nodo con la puntuación más baja
        return min(nodes_info, key=lambda item: score(item[1]))