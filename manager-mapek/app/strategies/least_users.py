from .base import NodeSelectionStrategy

class LeastUsersStrategy(NodeSelectionStrategy):
    def select_node(self, nodes_info):
        candidates = [
            (ip, data) for ip, data in nodes_info
            if data.get("status") == "online"
        ]
        if not candidates:
            return None
        return min(candidates, key=lambda item: item[1]["current_load"]["active_users_count"])