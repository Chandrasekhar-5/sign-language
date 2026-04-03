import numpy as np
import logging
from typing import Optional, Tuple
from .config import config
from .lstm_model import LSTMGestureModel, TrainingConfig

logger = logging.getLogger(__name__)

class GestureModel:
    """
    Gesture recognition model wrapper.
    Uses LSTM model for dynamic gesture recognition.
    """
    
    def __init__(self):
        """Initialize the gesture model."""
        # Initialize LSTM model
        training_config = TrainingConfig(
            sequence_length=config.SEQUENCE_LENGTH,
            num_features=63,  # 21 landmarks * 3 coordinates
            num_classes=len(config.GESTURE_CLASSES)
        )
        self.model = LSTMGestureModel(training_config)
        self.is_trained = False
        
        # For tracking consecutive detections
        self.last_prediction = None
        self.consecutive_count = 0
        self.confidence_threshold = config.CONFIDENCE_THRESHOLD
        
        logger.info(f"GestureModel initialized with {len(config.GESTURE_CLASSES)} classes")
    
    def add_landmarks(self, landmarks: np.ndarray) -> Optional[Tuple[str, float]]:
        """
        Add a frame of landmarks to the buffer and return prediction if buffer is full.
        
        Args:
            landmarks: Array of hand landmarks (21 points * 3 coordinates)
            
        Returns:
            Tuple of (gesture_name, confidence) or None if buffer not ready
        """
        if landmarks is None:
            return None
        
        # Pass to LSTM model
        result = self.model.add_landmarks(landmarks)
        
        if result:
            gesture_name, confidence, _ = result
            
            # Apply confidence threshold
            if confidence < self.confidence_threshold:
                return "None", confidence
            
            return gesture_name, confidence
        
        return None
    
    def load_model(self, model_path: str) -> bool:
        """
        Load trained model from file.
        
        Args:
            model_path: Path to the saved model
            
        Returns:
            bool: True if model loaded successfully
        """
        success = self.model.load_model(model_path)
        if success:
            self.is_trained = True
            logger.info(f"Model loaded from {model_path}")
        else:
            logger.warning(f"Could not load model from {model_path}, using fallback")
        return success
    
    def reset(self):
        """Reset the sequence buffer."""
        self.model.reset()
        self.last_prediction = None
        self.consecutive_count = 0
    
    def get_buffer_status(self) -> dict:
        """Get current buffer status."""
        return self.model.get_buffer_status()