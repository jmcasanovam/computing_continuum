from .base import NodeSelectionStrategy

class LeastUsersStrategy(NodeSelectionStrategy):
    def select_node(self, nodes_info):
        # La lista nodes_info ya ha sido filtrada por el NodeSelector para incluir solo los nodos online.

        if not nodes_info:
            return None # Si no hay candidatos, no hay nada que seleccionar
        
        return min(nodes_info, key=lambda item: item[1]["current_load"]["active_users_count"])