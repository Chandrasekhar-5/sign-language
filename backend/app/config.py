import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Configuration settings for the application."""
    
    # Server settings
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", 8000))
    
    # WebSocket settings
    WS_MAX_SIZE = int(os.getenv("WS_MAX_SIZE", 1024 * 1024))  # 1MB
    WS_PING_INTERVAL = int(os.getenv("WS_PING_INTERVAL", 20))  # seconds
    WS_PING_TIMEOUT = int(os.getenv("WS_PING_TIMEOUT", 20))  # seconds
    
    # Model settings
    MODEL_PATH = os.getenv("MODEL_PATH", "models/gesture_model.h5")
    SEQUENCE_LENGTH = int(os.getenv("SEQUENCE_LENGTH", 30))  # frames per gesture
    GESTURE_CLASSES = [
        "Hello", "Stop", "Yes", "No", "Thank You", 
        "Thumbs Up", "Point", "Peace", "OK", 
        "Rock On", "Call Me", "Dislike", "None"
    ]
    CONFIDENCE_THRESHOLD = float(os.getenv("CONFIDENCE_THRESHOLD", 0.7))
    
    # MediaPipe settings
    MIN_DETECTION_CONFIDENCE = float(os.getenv("MIN_DETECTION_CONFIDENCE", 0.5))
    MIN_TRACKING_CONFIDENCE = float(os.getenv("MIN_TRACKING_CONFIDENCE", 0.5))
    
    # Video settings
    TARGET_WIDTH = int(os.getenv("TARGET_WIDTH", 640))
    TARGET_HEIGHT = int(os.getenv("TARGET_HEIGHT", 480))
    FPS_TARGET = int(os.getenv("FPS_TARGET", 30))
    
    # Green box settings
    ROI_PADDING = float(os.getenv("ROI_PADDING", 0.2))  # 20% padding around detected hand
    ROI_MIN_SIZE = int(os.getenv("ROI_MIN_SIZE", 100))  # minimum ROI size in pixels
    
    # NLP settings (for sentence formation)
    USE_NLP = os.getenv("USE_NLP", "true").lower() == "true"
    
    @classmethod
    def validate(cls):
        """Validate critical configuration."""
        assert cls.SEQUENCE_LENGTH > 0, "SEQUENCE_LENGTH must be positive"
        assert 0 <= cls.CONFIDENCE_THRESHOLD <= 1, "CONFIDENCE_THRESHOLD must be between 0 and 1"
        assert cls.TARGET_WIDTH > 0 and cls.TARGET_HEIGHT > 0, "Invalid target dimensions"
        return True

config = Config()