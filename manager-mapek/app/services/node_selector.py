from ..strategies.least_users import LeastUsersStrategy
from ..strategies.weighted_score import WeightedScoreStrategy
from .node_monitor import nodes_status

class NodeSelector:
    def __init__(self, strategy_name):
        self.strategy = self._load_strategy(strategy_name)

    def _load_strategy(self, name):
        if name == "least_users":
            return LeastUsersStrategy()
        elif name == "weighted":
            return WeightedScoreStrategy()
        raise ValueError("Estrategia desconocida")

    def select_node(self):
        nodes_info = list(nodes_status.items())
        result = self.strategy.select_node(nodes_info)
        print(f"[DEBUG] Resultado de la estrategia: {result}")
        return result