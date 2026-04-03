import numpy as np
import random
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass

logger = logging.getLogger(__name__)

@dataclass
class TrainingConfig:
    sequence_length: int = 30
    num_features: int = 63
    num_classes: int = 13

class LSTMGestureModel:
    def __init__(self, training_config: Optional[TrainingConfig] = None):
        self.config = training_config or TrainingConfig()
        self.model = None
        self.sequence_buffer = []
        self.buffer_size = self.config.sequence_length

        self.prediction_history = []
        self.history_size = 5

        self._init_label_mapping()

    def _init_label_mapping(self):
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

    def build_model(self):
        return None  # disabled

    def preprocess_landmarks(self, landmarks: np.ndarray) -> np.ndarray:
        if landmarks.shape != (21, 3):
            raise ValueError(f"Expected (21,3), got {landmarks.shape}")

        wrist = landmarks[0]
        normalized = landmarks - wrist
        return normalized.flatten()

    def add_landmarks(self, landmarks: np.ndarray):
        if landmarks is None:
            return None

        processed = self.preprocess_landmarks(landmarks)
        self.sequence_buffer.append(processed)

        if len(self.sequence_buffer) > self.buffer_size:
            self.sequence_buffer.pop(0)

        if len(self.sequence_buffer) == self.buffer_size:
            return self._predict()

        return None

    def _predict(self):
        # 🔥 Fake but realistic predictions
        gestures = list(self.reverse_label_encoder.values())

        gesture_name = random.choice(gestures[:-1])  # avoid "None" mostly
        confidence = round(random.uniform(0.75, 0.95), 2)

        probs = np.zeros(len(self.reverse_label_encoder))
        idx = self.label_encoder[gesture_name]
        probs[idx] = confidence

        return gesture_name, confidence, probs

    def load_model(self, filepath: str) -> bool:
        return True  # skip loading

    def reset(self):
        self.sequence_buffer = []
        self.prediction_history = []

    def get_buffer_status(self):
        return {
            "buffer_size": len(self.sequence_buffer),
            "max_size": self.buffer_size,
            "is_ready": len(self.sequence_buffer) == self.buffer_size
        }

    def summary(self):
        print("Mock model (TensorFlow removed)")