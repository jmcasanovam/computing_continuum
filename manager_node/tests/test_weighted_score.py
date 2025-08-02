from app.services.node_selector import NodeSelector
from app.services import node_monitor

def test_weighted_score_ip_selection():
    node_monitor.nodes_status.clear()
    node_monitor.nodes_status.update({
        "192.168.1.100": {
            "edge_id": "node_a",
            "status": "online",
            "current_load": {
                "active_users_count": 10,
                "cpu_load": 0.8,
                "memory_usage": 0.7
            },
            "message": "ok"
        },
        "192.168.1.101": {
            "edge_id": "node_b",
            "status": "online",
            "current_load": {
                "active_users_count": 3,
                "cpu_load": 0.3,
                "memory_usage": 0.4
            },
            "message": "ok"
        }
    })

    selector = NodeSelector(strategy_name="weighted")
    ip = selector.select_node()
    assert ip == "192.168.1.101"
