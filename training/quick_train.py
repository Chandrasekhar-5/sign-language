#!/usr/bin/env python3
"""
Quick training script for fast model training with synthetic data.
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.lstm_model import LSTMGestureModel, TrainingConfig
from app.config import config
import numpy as np

def quick_train():
    """Quick training with synthetic data."""
    print("🚀 Starting quick training...")
    
    # Generate synthetic data
    print("📊 Generating synthetic training data...")
    num_sequences = 100
    sequence_length = config.SEQUENCE_LENGTH
    
    label_encoder = {
        "Hello": 0, "Stop": 1, "Yes": 2, "No": 3, "Thank You": 4,
        "Thumbs Up": 5, "Point": 6, "Peace": 7, "OK": 8,
        "Rock On": 9, "Call Me": 10, "Dislike": 11, "None": 12
    }
    
    X = []
    y = []
    
    for gesture_name, label in label_encoder.items():
        print(f"  Generating for {gesture_name}...")
        for _ in range(num_sequences):
            sequence = []
            for _ in range(sequence_length):
                # Add some pattern variation for different gestures
                base_pattern = np.random.randn(21, 3) * 0.1
                # Add gesture-specific pattern
                pattern_shift = label * 0.05
                landmarks = base_pattern + pattern_shift
                sequence.append(landmarks.flatten())
            X.append(sequence)
            y.append(label)
    
    X = np.array(X)
    y_onehot = np.zeros((len(y), len(label_encoder)))
    y_onehot[np.arange(len(y)), y] = 1
    
    # Shuffle
    indices = np.random.permutation(len(X))
    X = X[indices]
    y_onehot = y_onehot[indices]
    
    # Split
    split = int(0.8 * len(X))
    X_train, X_val = X[:split], X[split:]
    y_train, y_val = y_onehot[:split], y_onehot[split:]
    
    print(f"\n📈 Training data shape: {X_train.shape}")
    print(f"📉 Validation data shape: {X_val.shape}")
    
    # Create and train model
    print("\n🏗️ Building LSTM model...")
    training_config = TrainingConfig(
        sequence_length=sequence_length,
        epochs=30,
        batch_size=32
    )
    model = LSTMGestureModel(training_config)
    model.build_model()
    
    print("\n🔧 Training model...")
    history = model.train(X_train, y_train, X_val, y_val)
    
    # Save model
    model_path = os.path.join(os.path.dirname(__file__), '..', 'backend', 'models', 'gesture_model.h5')
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    model.save_model(model_path)
    
    print(f"\n✅ Model saved to {model_path}")
    print(f"\n📊 Final Results:")
    print(f"  Training accuracy: {history['accuracy'][-1]:.4f}")
    print(f"  Validation accuracy: {history['val_accuracy'][-1]:.4f}")
    print(f"  Validation top-3 accuracy: {history['top_3_accuracy'][-1]:.4f}")
    
    return model

if __name__ == "__main__":
    quick_train()