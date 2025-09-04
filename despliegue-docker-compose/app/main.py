import httpx # Para hacer peticiones HTTP asíncronas
import asyncio
from datetime import datetime, timedelta
import uuid
import random

from app.schemas.ticwatch_schema import TicWatchData
from app.config import EDGE_NODE_HOST, EDGE_NODE_PORT

# URL del endpoint del Nodo Edge
EDGE_NODE_URL = f"http://{EDGE_NODE_HOST}:{EDGE_NODE_PORT}"

async def send_dummy_data_to_edge(user_id: str, num_samples: int = 50, delay: float = 0.5):
    """
    Genera y envía datos dummy a un Nodo Edge para un usuario específico.
    Simula el flujo de datos en tiempo real.
    """
    print(f"\n--- Starting data stream for user: {user_id} to {EDGE_NODE_URL} ---")
    session_id = f"session_{uuid.uuid4().hex[:8]}"

    activities_for_dummy = ['sleeping', 'sedentary', 'training'] # Las actividades que nuestro modelo predice

    for i in range(num_samples):
        # Simular datos variados, pero con una tendencia a un estado
        current_activity = random.choice(activities_for_dummy)
        
        # Generar datos de sensor realistas para la actividad
        if current_activity == 'sleeping':
            acc_vals = [random.uniform(0.05, 0.15) for _ in range(3)]
            accl_vals = [random.uniform(0.005, 0.015) for _ in range(3)]
            gir_vals = [random.uniform(0.005, 0.015) for _ in range(3)]
            hr = random.randint(50, 70)
            step = 0
        elif current_activity == 'sedentary':
            acc_vals = [random.uniform(0.15, 0.25) for _ in range(3)]
            accl_vals = [random.uniform(0.03, 0.07) for _ in range(3)]
            gir_vals = [random.uniform(0.03, 0.07) for _ in range(3)]
            hr = random.randint(60, 90)
            step = 0
        elif current_activity == 'training':
            acc_vals = [random.uniform(0.8, 1.8) for _ in range(3)]
            accl_vals = [random.uniform(0.2, 0.6) for _ in range(3)]
            gir_vals = [random.uniform(0.2, 0.6) for _ in range(3)]
            hr = random.randint(120, 180)
            step = random.randint(50, 300)
        
        ticwatch_data = TicWatchData(
            session_id=session_id,
            timeStamp=datetime.now(),
            tic_accx=acc_vals[0], tic_accy=acc_vals[1], tic_accz=acc_vals[2],
            tic_acclx=accl_vals[0], tic_accly=accl_vals[1], tic_acclz=accl_vals[2],
            tic_girx=gir_vals[0], tic_giry=gir_vals[1], tic_girz=gir_vals[2],
            tic_hrppg=float(hr), # Asegurar que sea float
            tic_step=step,
            ticwatchconnected=True,
            estado_real=current_activity # Esto se envía al Edge para que se guarde en la DB y sirva como etiqueta de verdad
        )

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{EDGE_NODE_URL}/predict_activity/{user_id}",
                    json=ticwatch_data.model_dump(mode='json') # Convertir a dict para JSON, con mode='json' para datetime
                )
                response.raise_for_status() # Lanza excepción para errores HTTP (4xx o 5xx)
                prediction_result = response.json()
                print(f"User {user_id} - Predicted: {prediction_result['predicted_activity']} at {prediction_result['timestamp']}")
        except httpx.RequestError as e:
            print(f"Request failed for user {user_id}: {e}")
        except httpx.HTTPStatusError as e:
            print(f"HTTP error for user {user_id}: {e.response.status_code} - {e.response.text}")
        except Exception as e:
            print(f"An unexpected error occurred for user {user_id}: {e}")
        
        await asyncio.sleep(delay) # Simular el envío de datos en tiempo real

    print(f"--- Finished data stream for user: {user_id} ---")

async def main():
    # Creamos dos usuarios de ejemplo
    user1_id = "user_alpha"
    user2_id = "user_beta"
    user3_id = "user_gamma"

    # Ejecutamos las simulaciones de envío de datos concurrentemente
    await asyncio.gather(
        send_dummy_data_to_edge(user1_id, num_samples=30, delay=0.7),
        send_dummy_data_to_edge(user2_id, num_samples=20, delay=1.0),
        send_dummy_data_to_edge(user3_id, num_samples=25, delay=0.8)
    )

if __name__ == "__main__":
    print(f"Starting client simulation. Connecting to Edge Node at {EDGE_NODE_URL}...")
    asyncio.run(main())