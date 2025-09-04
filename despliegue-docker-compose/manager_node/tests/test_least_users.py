from app.services.node_selector import NodeSelector
from app.services import node_monitor

def test_least_users_ip_selection():
    node_monitor.nodes_status.clear()
    node_monitor.nodes_status.update({
        "192.168.1.10": {
            "edge_id": "node_10",
            "status": "online",
            "current_load": {"active_users_count": 5},
            "message": "ok"
        },
        "192.168.1.20": {
            "edge_id": "node_20",
            "status": "online",
            "current_load": {"active_users_count": 2},
            "message": "ok"
        },
        "192.168.1.30": {
            "edge_id": "node_30",
            "status": "offline",
            "current_load": {"active_users_count": 0},
            "message": "offline"
        }
    })

    selector = NodeSelector(strategy_name="least_users")
    ip = selector.select_node()
    assert ip == "192.168.1.20"
