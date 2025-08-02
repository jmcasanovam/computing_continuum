from app.services.node_selector import NodeSelector
from app.services import node_monitor

def test_selector_returns_none_if_all_nodes_offline():
    node_monitor.nodes_status.clear()
    node_monitor.nodes_status.update({
        "192.168.1.10": {
            "edge_id": "node_x",
            "status": "offline",
            "current_load": {"active_users_count": 1},
            "message": "offline"
        },
        "192.168.1.11": {
            "edge_id": "node_y",
            "status": "offline",
            "current_load": {"active_users_count": 2},
            "message": "offline"
        }
    })

    selector = NodeSelector(strategy_name="least_users")
    ip = selector.select_node()
    assert ip is None
