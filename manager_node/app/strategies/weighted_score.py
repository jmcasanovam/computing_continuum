from .base import NodeSelectionStrategy

class WeightedScoreStrategy(NodeSelectionStrategy):
    def select_node(self, nodes_info):
        def score(data):
            load = data["current_load"]
            return (load["active_users_count"] * 0.5 +
                    load["cpu_load"] * 0.3 +
                    load["memory_usage"] * 0.2)

        candidates = [
            (ip, data) for ip, data in nodes_info 
            if data.get("status") == "online"
        ]
        if not candidates:
            return None, None
        return min(candidates, key=lambda item: score(item[1]))
