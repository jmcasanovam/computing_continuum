import pandas as pd
from sklearn.model_selection import train_test_split # Not strictly used here, but kept for general ML practice
from app.models.ticwatch_predictor import TicWatchPredictor
from app.data.database import create_tables, insert_ticwatch_data, get_all_training_data
from app.config import FEATURE_COLUMNS
from cloud_node.model_repository import ModelRepository
import os
import uuid # To generate example user_ids and session_ids
from datetime import datetime, timedelta

def generate_dummy_data(num_samples=1000):
    """Generates dummy data for initial model training."""
    data = []
    # Only the three specified activities
    activities = ['sleeping', 'sedentary', 'training']
    
    # Define realistic ranges for each activity
    activity_profiles = {
        'sleeping': {
            'acc': [0.1, 0.1, 0.1], 'accl': [0.01, 0.01, 0.01], 'gir': [0.01, 0.01, 0.01],
            'hr': (50, 70), 'step': 0
        },
        'sedentary': {
            'acc': [0.2, 0.2, 0.2], 'accl': [0.05, 0.05, 0.05], 'gir': [0.05, 0.05, 0.05],
            'hr': (60, 90), 'step': 0
        },
        'training': { # Combining running/cycling for 'training'
            'acc': [1.0, 1.0, 1.0], 'accl': [0.3, 0.3, 0.3], 'gir': [0.3, 0.3, 0.3],
            'hr': (120, 180), 'step': (50, 300) # Steps can vary
        }
    }
    
    for i in range(num_samples):
        # Generate user_ids. Some users will have multiple samples.
        # This simple logic creates a new user_id every 10 samples
        user_id = f"user_{uuid.uuid4().hex[:8]}" if i % 10 == 0 else data[-1]['user_id'] if i > 0 else f"user_{uuid.uuid4().hex[:8]}"
        session_id = f"session_{uuid.uuid4().hex[:8]}"
        timestamp = datetime.now() - timedelta(minutes=num_samples - i) # Data ordered by time
        
        # Select an activity based on loop index
        activity = activities[i % len(activities)]
        profile = activity_profiles[activity]
        
        # Generate feature values based on the activity profile
        acc_vals = [val + (i % 5) * 0.01 for val in profile['acc']]
        accl_vals = [val + (i % 5) * 0.001 for val in profile['accl']]
        gir_vals = [val + (i % 5) * 0.001 for val in profile['gir']]
        
        hr = profile['hr'][0] + (i % (profile['hr'][1] - profile['hr'][0] + 1))
        
        step = 0
        if isinstance(profile['step'], tuple):
            step = profile['step'][0] + (i % (profile['step'][1] - profile['step'][0] + 1))
        else:
            step = profile['step']
            
        data.append({
            'session_id': session_id,
            'user_id': user_id,
            'timeStamp': timestamp,
            'tic_accx': acc_vals[0], 'tic_accy': acc_vals[1], 'tic_accz': acc_vals[2],
            'tic_acclx': accl_vals[0], 'tic_accly': accl_vals[1], 'tic_acclz': accl_vals[2],
            'tic_girx': gir_vals[0], 'tic_giry': gir_vals[1], 'tic_girz': gir_vals[2],
            'tic_hrppg': hr,
            'tic_step': step,
            'ticwatchconnected': True,
            'estado_real': activity, # This is the true label for training
            'predicted_state': None # No prediction yet
        })
    return data

def generate_initial_model():
    print("--- Generating initial generic model ---")

    # 1. Ensure DB tables exist
    create_tables()

    # 2. Generate dummy data and save it to the DB
    print("Generating dummy training data...")
    dummy_data = generate_dummy_data(num_samples=3000) # More data for a robust generic model
    for d in dummy_data:
        insert_ticwatch_data(d)
    print(f"Inserted {len(dummy_data)} dummy records into the database.")

    # 3. Load all data with true labels
    print("Loading training data from DB...")
    training_df = get_all_training_data()

    if training_df.empty:
        print("No true-labeled data available to train the generic model. Aborting.")
        return

    X = training_df[FEATURE_COLUMNS]
    y = training_df['estado_real']

    print(f"Data loaded for training: {len(X)} samples.")
    print(f"Class distribution: \n{y.value_counts()}")

    # 4. Train the generic model
    predictor = TicWatchPredictor()
    predictor.train_model(X, y)

    # 5. Save the generic model using the ModelRepository
    model_repo = ModelRepository()
    model_path = model_repo.save_model(predictor.model, "generic_activity_model", is_generic=True)

    print("--- Initial generic model generated and saved ---")

if __name__ == "__main__":
    generate_initial_model()