import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
import json
import os
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    """Configuration for model training."""
    sequence_length: int = 30
    num_features: int = 63  # 21 landmarks * 3 coordinates
    num_classes: int = 13  # 12 gestures + None
    lstm_units: List[int] = None
    dense_units: List[int] = None
    dropout_rate: float = 0.3
    learning_rate: float = 0.001
    batch_size: int = 32
    epochs: int = 50
    validation_split: float = 0.2
    
    def __post_init__(self):
        if self.lstm_units is None:
            self.lstm_units = [128, 64]
        if self.dense_units is None:
            self.dense_units = [64, 32]

class LSTMGestureModel:
    """
    LSTM-based model for dynamic gesture recognition.
    Processes sequences of hand landmarks over time to recognize gestures.
    """
    
    def __init__(self, training_config: Optional[TrainingConfig] = None):
        """
        Initialize the LSTM model.
        
        Args:
            training_config: Configuration for model architecture and training
        """
        self.config = training_config or TrainingConfig()
        self.model: Optional[tf.keras.Model] = None
        self.label_encoder: Dict[str, int] = {}
        self.reverse_label_encoder: Dict[int, str] = {}
        self.is_trained = False
        self.sequence_buffer = []
        self.buffer_size = self.config.sequence_length
        
        # For smoothing predictions
        self.prediction_history = []
        self.history_size = 5
        
        # Initialize label mapping
        self._init_label_mapping()
        
    def _init_label_mapping(self):
        """Initialize the mapping between gesture names and indices."""
        self.label_encoder = {
            "Hello": 0,
            "Stop": 1,
            "Yes": 2,
            "No": 3,
            "Thank You": 4,
            "Thumbs Up": 5,
            "Point": 6,
            "Peace": 7,
            "OK": 8,
            "Rock On": 9,
            "Call Me": 10,
            "Dislike": 11,
            "None": 12
        }
        self.reverse_label_encoder = {v: k for k, v in self.label_encoder.items()}
        self.config.num_classes = len(self.label_encoder)
        
    def build_model(self) -> tf.keras.Model:
        """
        Build the LSTM model architecture.
        
        Architecture:
        - Bidirectional LSTM layers for temporal features
        - Dropout for regularization
        - Dense layers for classification
        """
        model = models.Sequential()
        
        # Input layer
        model.add(layers.Input(shape=(self.config.sequence_length, self.config.num_features)))
        
        # First Bidirectional LSTM layer
        model.add(layers.Bidirectional(
            layers.LSTM(self.config.lstm_units[0], return_sequences=True, dropout=self.config.dropout_rate)
        ))
        model.add(layers.BatchNormalization())
        
        # Second LSTM layer
        model.add(layers.LSTM(self.config.lstm_units[1], return_sequences=False, dropout=self.config.dropout_rate))
        model.add(layers.BatchNormalization())
        
        # Dense layers
        for units in self.config.dense_units:
            model.add(layers.Dense(units, activation='relu'))
            model.add(layers.Dropout(self.config.dropout_rate))
            model.add(layers.BatchNormalization())
        
        # Output layer
        model.add(layers.Dense(self.config.num_classes, activation='softmax'))
        
        # Compile model
        optimizer = tf.keras.optimizers.Adam(learning_rate=self.config.learning_rate)
        model.compile(
            optimizer=optimizer,
            loss='categorical_crossentropy',
            metrics=['accuracy', tf.keras.metrics.TopKCategoricalAccuracy(k=3, name='top_3_accuracy')]
        )
        
        self.model = model
        logger.info(f"Model built with {self.model.count_params()} parameters")
        return model
    
    def preprocess_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        """
        Preprocess landmark data for model input.
        
        Args:
            landmarks: Raw landmark array (21, 3)
            
        Returns:
            Preprocessed landmarks (normalized and flattened)
        """
        if landmarks.shape != (21, 3):
            raise ValueError(f"Expected landmarks shape (21, 3), got {landmarks.shape}")
        
        # Normalize relative to wrist (landmark 0)
        wrist = landmarks[0]
        normalized = landmarks - wrist
        
        # Flatten to 1D array
        flattened = normalized.flatten()
        
        return flattened
    
    def add_landmarks(self, landmarks: np.ndarray) -> Optional[Tuple[str, float, np.ndarray]]:
        """
        Add a frame of landmarks to the buffer and return prediction if buffer is full.
        
        Args:
            landmarks: Raw landmark array (21, 3)
            
        Returns:
            Tuple of (gesture_name, confidence, probabilities) or None if buffer not ready
        """
        if landmarks is None:
            return None
        
        # Preprocess landmarks
        processed = self.preprocess_landmarks(landmarks)
        
        # Add to buffer
        self.sequence_buffer.append(processed)
        
        # Keep buffer at maximum size
        if len(self.sequence_buffer) > self.buffer_size:
            self.sequence_buffer.pop(0)
        
        # Predict only when buffer is full
        if len(self.sequence_buffer) == self.buffer_size and self.model is not None:
            return self._predict()
        
        return None
    
    def _predict(self) -> Tuple[str, float, np.ndarray]:
        """
        Predict gesture from sequence buffer.
        
        Returns:
            Tuple of (gesture_name, confidence, probabilities)
        """
        # Prepare input array
        input_sequence = np.array(self.sequence_buffer).reshape(1, self.buffer_size, self.config.num_features)
        
        # Get prediction
        predictions = self.model.predict(input_sequence, verbose=0)[0]
        
        # Get top prediction
        top_idx = np.argmax(predictions)
        confidence = float(predictions[top_idx])
        
        # Apply temporal smoothing
        self.prediction_history.append((top_idx, confidence))
        if len(self.prediction_history) > self.history_size:
            self.prediction_history.pop(0)
        
        # Smooth predictions by averaging recent history
        if len(self.prediction_history) >= 3:
            smoothed_idx = self._smooth_predictions()
            if smoothed_idx != top_idx:
                top_idx = smoothed_idx
                confidence = float(predictions[top_idx])
        
        gesture_name = self.reverse_label_encoder.get(top_idx, "None")
        
        return gesture_name, confidence, predictions
    
    def _smooth_predictions(self) -> int:
        """
        Apply temporal smoothing to predictions.
        Uses majority voting from recent predictions.
        
        Returns:
            Smoothed class index
        """
        from collections import Counter
        
        recent_indices = [idx for idx, _ in self.prediction_history]
        counter = Counter(recent_indices)
        
        # Get most common prediction
        most_common = counter.most_common(1)[0][0]
        
        # Only smooth if there's clear majority
        if counter[most_common] >= len(recent_indices) // 2 + 1:
            return most_common
        
        # Otherwise return original (will use the current prediction)
        return self.prediction_history[-1][0]
    
    def train(self, X_train: np.ndarray, y_train: np.ndarray, 
              X_val: Optional[np.ndarray] = None, y_val: Optional[np.ndarray] = None,
              callbacks: Optional[List[tf.keras.callbacks.Callback]] = None) -> Dict[str, List[float]]:
        """
        Train the model on prepared data.
        
        Args:
            X_train: Training sequences (n_samples, sequence_length, num_features)
            y_train: Training labels (one-hot encoded)
            X_val: Validation sequences
            y_val: Validation labels
            callbacks: List of Keras callbacks
            
        Returns:
            Training history
        """
        if self.model is None:
            self.build_model()
        
        # Default callbacks
        if callbacks is None:
            callbacks = [
                tf.keras.callbacks.EarlyStopping(
                    monitor='val_loss' if X_val is not None else 'loss',
                    patience=10,
                    restore_best_weights=True
                ),
                tf.keras.callbacks.ReduceLROnPlateau(
                    monitor='val_loss' if X_val is not None else 'loss',
                    factor=0.5,
                    patience=5,
                    min_lr=1e-6
                ),
                tf.keras.callbacks.ModelCheckpoint(
                    filepath=config.MODEL_PATH.replace('.h5', '_best.h5'),
                    monitor='val_accuracy' if X_val is not None else 'accuracy',
                    save_best_only=True,
                    mode='max'
                )
            ]
        
        # Train model
        history = self.model.fit(
            X_train, y_train,
            validation_data=(X_val, y_val) if X_val is not None else None,
            epochs=self.config.epochs,
            batch_size=self.config.batch_size,
            callbacks=callbacks,
            verbose=1
        )
        
        self.is_trained = True
        logger.info("Model training completed")
        
        return history.history
    
    def save_model(self, filepath: str):
        """
        Save the trained model and label encoder.
        
        Args:
            filepath: Path to save the model
        """
        if self.model is None:
            raise ValueError("No model to save")
        
        # Save model
        self.model.save(filepath)
        
        # Save label encoder
        encoder_path = filepath.replace('.h5', '_labels.json')
        with open(encoder_path, 'w') as f:
            json.dump(self.label_encoder, f)
        
        logger.info(f"Model saved to {filepath}")
        logger.info(f"Label encoder saved to {encoder_path}")
    
    def load_model(self, filepath: str) -> bool:
        """
        Load a trained model.
        
        Args:
            filepath: Path to the saved model
            
        Returns:
            bool: True if model loaded successfully
        """
        try:
            # Load model
            self.model = tf.keras.models.load_model(filepath)
            
            # Load label encoder
            encoder_path = filepath.replace('.h5', '_labels.json')
            if os.path.exists(encoder_path):
                with open(encoder_path, 'r') as f:
                    self.label_encoder = json.load(f)
                self.reverse_label_encoder = {int(v): k for k, v in self.label_encoder.items()}
                self.config.num_classes = len(self.label_encoder)
            
            self.is_trained = True
            logger.info(f"Model loaded from {filepath}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to load model: {e}")
            return False
    
    def reset(self):
        """Reset the sequence buffer and prediction history."""
        self.sequence_buffer = []
        self.prediction_history = []
    
    def get_buffer_status(self) -> dict:
        """Get current buffer status."""
        return {
            "buffer_size": len(self.sequence_buffer),
            "max_size": self.buffer_size,
            "is_ready": len(self.sequence_buffer) == self.buffer_size
        }
    
    def summary(self):
        """Print model summary."""
        if self.model:
            self.model.summary()
        else:
            print("Model not built yet")