#!/usr/bin/env python3
"""
Training script for the LSTM gesture recognition model.
Supports training on custom data or synthetic data generation.
"""

import numpy as np
import cv2
import mediapipe as mp
import os
import sys
import json
import argparse
from pathlib import Path
from datetime import datetime
from typing import List, Tuple, Dict
import random

# Add backend to path
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from app.lstm_model import LSTMGestureModel, TrainingConfig
from app.config import config

class DataCollector:
    """Utility class for collecting training data."""
    
    def __init__(self):
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=1,
            min_detection_confidence=0.5,
            min_tracking_confidence=0.5
        )
        
    def collect_gesture(self, gesture_name: str, num_sequences: int = 50, 
                       sequence_length: int = 30) -> List[np.ndarray]:
        """
        Collect training data for a specific gesture.
        
        Args:
            gesture_name: Name of the gesture to collect
            num_sequences: Number of sequences to collect
            sequence_length: Frames per sequence
            
        Returns:
            List of sequences (each sequence is list of landmarks)
        """
        print(f"\n{'='*60}")
        print(f"Collecting data for gesture: {gesture_name}")
        print(f"Need {num_sequences} sequences of {sequence_length} frames each")
        print(f"Press SPACE to start recording, ESC to skip, ENTER to finish")
        print(f"{'='*60}\n")
        
        cap = cv2.VideoCapture(0)
        sequences = []
        current_sequence = []
        
        while len(sequences) < num_sequences:
            ret, frame = cap.read()
            if not ret:
                continue
            
            frame = cv2.flip(frame, 1)
            rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
            results = self.hands.process(rgb_frame)
            
            # Draw landmarks
            if results.multi_hand_landmarks:
                hand_landmarks = results.multi_hand_landmarks[0]
                
                # Extract landmarks
                landmarks = []
                for lm in hand_landmarks.landmark:
                    landmarks.append([lm.x, lm.y, lm.z])
                
                if len(current_sequence) < sequence_length:
                    current_sequence.append(np.array(landmarks))
                
                # Draw landmarks on frame
                mp.solutions.drawing_utils.draw_landmarks(
                    frame, hand_landmarks, self.mp_hands.HAND_CONNECTIONS)
            
            # Display info
            cv2.putText(frame, f"Gesture: {gesture_name}", (10, 30),
                       cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)
            cv2.putText(frame, f"Sequences: {len(sequences)}/{num_sequences}", (10, 60),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, f"Current sequence: {len(current_sequence)}/{sequence_length}", (10, 90),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)
            cv2.putText(frame, "SPACE: Record | ESC: Skip | ENTER: Finish", (10, frame.shape[0] - 20),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, (255, 255, 255), 1)
            
            cv2.imshow('Data Collection', frame)
            
            key = cv2.waitKey(1) & 0xFF
            if key == ord(' '):  # Space - record sequence
                if len(current_sequence) == sequence_length:
                    sequences.append(current_sequence)
                    current_sequence = []
                    print(f"✓ Recorded sequence {len(sequences)}/{num_sequences}")
                else:
                    print(f"✗ Need {sequence_length} frames, got {len(current_sequence)}")
                    
            elif key == 27:  # ESC - skip this gesture
                print(f"Skipped {gesture_name}")
                break
                
            elif key == 13:  # Enter - finish collection
                break
        
        cap.release()
        cv2.destroyAllWindows()
        
        return sequences
    
    def generate_synthetic_data(self, num_sequences: int = 100, 
                                sequence_length: int = 30) -> Dict[str, List]:
        """
        Generate synthetic data for testing the training pipeline.
        Creates random movement patterns for each gesture.
        """
        print("Generating synthetic training data...")
        
        label_encoder = {
            "Hello": 0, "Stop": 1, "Yes": 2, "No": 3, "Thank You": 4,
            "Thumbs Up": 5, "Point": 6, "Peace": 7, "OK": 8,
            "Rock On": 9, "Call Me": 10, "Dislike": 11, "None": 12
        }
        
        X = []
        y = []
        
        for gesture_name, label in label_encoder.items():
            print(f"  Generating {num_sequences} sequences for {gesture_name}...")
            
            for _ in range(num_sequences):
                # Generate random landmark sequences
                sequence = []
                for _ in range(sequence_length):
                    # Random landmarks (21 points x 3 coordinates)
                    landmarks = np.random.randn(21, 3) * 0.1
                    sequence.append(landmarks.flatten())
                
                X.append(sequence)
                y.append(label)
        
        return np.array(X), np.array(y)

class DataPreprocessor:
    """Preprocess collected data for training."""
    
    @staticmethod
    def normalize_landmarks(landmarks: np.ndarray) -> np.ndarray:
        """Normalize landmarks relative to wrist."""
        if len(landmarks.shape) == 2:  # Single frame
            wrist = landmarks[0]
            return landmarks - wrist
        else:  # Sequence
            wrist = landmarks[:, 0:1, :]  # Wrist for each frame
            return landmarks - wrist
    
    @staticmethod
    def prepare_sequences(sequences: List[List[np.ndarray]], 
                          labels: List[int]) -> Tuple[np.ndarray, np.ndarray]:
        """
        Prepare sequences for training.
        
        Args:
            sequences: List of sequences (each sequence is list of frames)
            labels: List of labels for each sequence
            
        Returns:
            X: Array of sequences (n_samples, sequence_length, 63)
            y: One-hot encoded labels
        """
        X = []
        y = []
        
        for seq, label in zip(sequences, labels):
            normalized_seq = []
            for frame in seq:
                normalized = DataPreprocessor.normalize_landmarks(frame)
                normalized_seq.append(normalized.flatten())
            X.append(normalized_seq)
            y.append(label)
        
        X = np.array(X)
        
        # One-hot encode labels
        num_classes = len(np.unique(y))
        y_onehot = np.zeros((len(y), num_classes))
        y_onehot[np.arange(len(y)), y] = 1
        
        return X, y_onehot

def main():
    parser = argparse.ArgumentParser(description='Train LSTM gesture recognition model')
    parser.add_argument('--mode', type=str, choices=['collect', 'synthetic', 'train', 'full'],
                       default='full', help='Mode to run')
    parser.add_argument('--gesture', type=str, help='Gesture to collect (for collect mode)')
    parser.add_argument('--sequences', type=int, default=50, help='Number of sequences per gesture')
    parser.add_argument('--epochs', type=int, default=50, help='Number of training epochs')
    parser.add_argument('--batch_size', type=int, default=32, help='Batch size for training')
    parser.add_argument('--data_dir', type=str, default='./data', help='Directory for collected data')
    parser.add_argument('--model_path', type=str, default='../backend/models/gesture_model.h5',
                       help='Path to save the model')
    
    args = parser.parse_args()
    
    # Create directories
    Path(args.data_dir).mkdir(parents=True, exist_ok=True)
    Path(os.path.dirname(args.model_path)).mkdir(parents=True, exist_ok=True)
    
    if args.mode == 'collect':
        # Single gesture collection mode
        if not args.gesture:
            print("Error: --gesture required for collect mode")
            return
        
        collector = DataCollector()
        sequences = collector.collect_gesture(
            args.gesture, 
            num_sequences=args.sequences,
            sequence_length=config.SEQUENCE_LENGTH
        )
        
        # Save collected data
        data_file = os.path.join(args.data_dir, f"{args.gesture.lower().replace(' ', '_')}.npy")
        np.save(data_file, sequences)
        print(f"Saved {len(sequences)} sequences to {data_file}")
        
    elif args.mode == 'synthetic':
        # Generate synthetic data
        collector = DataCollector()
        X, y = collector.generate_synthetic_data(
            num_sequences=args.sequences,
            sequence_length=config.SEQUENCE_LENGTH
        )
        
        # Save synthetic data
        np.save(os.path.join(args.data_dir, 'X_synthetic.npy'), X)
        np.save(os.path.join(args.data_dir, 'y_synthetic.npy'), y)
        print(f"Saved synthetic data: X shape {X.shape}, y shape {y.shape}")
        
        # Train on synthetic data
        config_gesture = TrainingConfig(
            sequence_length=config.SEQUENCE_LENGTH,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
        model = LSTMGestureModel(config_gesture)
        model.build_model()
        
        # Train
        history = model.train(X, y)
        
        # Save model
        model.save_model(args.model_path)
        print(f"Model saved to {args.model_path}")
        
        # Print training results
        print(f"\nTraining Results:")
        print(f"Final accuracy: {history['accuracy'][-1]:.4f}")
        if 'val_accuracy' in history:
            print(f"Final validation accuracy: {history['val_accuracy'][-1]:.4f}")
    
    elif args.mode == 'train':
        # Load collected data and train
        print("Loading collected data...")
        
        # Load all gesture data
        X_all = []
        y_all = []
        
        label_encoder = {
            "Hello": 0, "Stop": 1, "Yes": 2, "No": 3, "Thank You": 4,
            "Thumbs Up": 5, "Point": 6, "Peace": 7, "OK": 8,
            "Rock On": 9, "Call Me": 10, "Dislike": 11, "None": 12
        }
        
        for gesture_name, label in label_encoder.items():
            data_file = os.path.join(args.data_dir, f"{gesture_name.lower().replace(' ', '_')}.npy")
            if os.path.exists(data_file):
                sequences = np.load(data_file, allow_pickle=True)
                print(f"Loaded {len(sequences)} sequences for {gesture_name}")
                
                for seq in sequences:
                    X_all.append(seq)
                    y_all.append(label)
            else:
                print(f"Warning: No data found for {gesture_name}")
        
        if len(X_all) == 0:
            print("No training data found. Please collect data first or use synthetic mode.")
            return
        
        # Prepare data
        preprocessor = DataPreprocessor()
        X, y = preprocessor.prepare_sequences(X_all, y_all)
        
        # Shuffle data
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        # Split train/val
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        print(f"\nTraining data shape: {X_train.shape}")
        print(f"Validation data shape: {X_val.shape}")
        
        # Train model
        config_gesture = TrainingConfig(
            sequence_length=config.SEQUENCE_LENGTH,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
        model = LSTMGestureModel(config_gesture)
        model.build_model()
        
        history = model.train(X_train, y_train, X_val, y_val)
        
        # Save model
        model.save_model(args.model_path)
        print(f"\nModel saved to {args.model_path}")
        
        # Print training results
        print(f"\nTraining Results:")
        print(f"Final training accuracy: {history['accuracy'][-1]:.4f}")
        print(f"Final validation accuracy: {history['val_accuracy'][-1]:.4f}")
    
    elif args.mode == 'full':
        # Full pipeline: generate synthetic data and train
        print("Running full training pipeline...")
        
        # Generate synthetic data
        collector = DataCollector()
        X, y = collector.generate_synthetic_data(
            num_sequences=args.sequences,
            sequence_length=config.SEQUENCE_LENGTH
        )
        
        # Shuffle and split
        indices = np.random.permutation(len(X))
        X = X[indices]
        y = y[indices]
        
        split = int(0.8 * len(X))
        X_train, X_val = X[:split], X[split:]
        y_train, y_val = y[:split], y[split:]
        
        # Train model
        config_gesture = TrainingConfig(
            sequence_length=config.SEQUENCE_LENGTH,
            epochs=args.epochs,
            batch_size=args.batch_size
        )
        model = LSTMGestureModel(config_gesture)
        model.build_model()
        
        print("\nModel Architecture:")
        model.summary()
        
        history = model.train(X_train, y_train, X_val, y_val)
        
        # Save model
        model.save_model(args.model_path)
        print(f"\n✓ Model saved to {args.model_path}")
        
        # Print final results
        print(f"\n{'='*60}")
        print("TRAINING COMPLETE")
        print(f"{'='*60}")
        print(f"Final training accuracy: {history['accuracy'][-1]:.4f}")
        print(f"Final validation accuracy: {history['val_accuracy'][-1]:.4f}")
        print(f"Final validation top-3 accuracy: {history['top_3_accuracy'][-1]:.4f}")

if __name__ == "__main__":
    main()