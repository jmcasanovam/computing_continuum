import threading
import time
import requests
from app.config import NODE_IPS

nodes_status = {ip: {} for ip in NODE_IPS} # Diccionario para almacenar el estado de cada nodo

def fetch_node_status(ip):
    try:
        print("I'm gonna try to get the status of node:", ip)
        print("Fetching status from:", f"http://{ip}:8003/status")
        response = requests.get(f"http://{ip}:8003/status", timeout=5)
        if response.status_code == 200:
            data = response.json()
            if data.get("status") == "online":
                return data
    except:
        pass
    return {"status": "offline"}

def monitor_nodes():
    while True:
        for ip in NODE_IPS:
            nodes_status[ip] = fetch_node_status(ip)
        time.sleep(5)

def start_monitoring():
    thread = threading.Thread(target=monitor_nodes, daemon=True)
    thread.start()
