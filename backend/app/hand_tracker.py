import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class HandLandmarks:
    """Container for hand landmark data."""
    landmarks: List[Dict[str, float]]
    handedness: str
    confidence: float

class HandTracker:
    """
    Hand tracking using MediaPipe with ROI extraction for better performance.
    Provides hand landmark extraction and bounding box calculation.
    """
    
    def __init__(self):
        """Initialize MediaPipe hand tracking model."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
            model_complexity=1  # 0, 1, or 2 for trade-off between accuracy and speed
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # For tracking hand position
        self.last_hand_bbox = None
        self.hand_detected = False
        
    def extract_roi(self, frame: np.ndarray, hand_landmarks) -> Optional[Tuple[int, int, int, int]]:
        """
        Extract Region of Interest around detected hand.
        
        Args:
            frame: Input video frame
            hand_landmarks: MediaPipe hand landmarks
            
        Returns:
            Tuple of (x, y, width, height) for the ROI, or None if no hand detected
        """
        if not hand_landmarks:
            return None
        
        h, w = frame.shape[:2]
        
        # Get all landmark points
        points = []
        for landmark in hand_landmarks.landmark:
            x = int(landmark.x * w)
            y = int(landmark.y * h)
            points.append((x, y))
        
        if not points:
            return None
        
        # Calculate bounding box
        points = np.array(points)
        x_min = max(0, np.min(points[:, 0]))
        x_max = min(w, np.max(points[:, 0]))
        y_min = max(0, np.min(points[:, 1]))
        y_max = min(h, np.max(points[:, 1]))
        
        # Add padding
        padding_x = int((x_max - x_min) * config.ROI_PADDING)
        padding_y = int((y_max - y_min) * config.ROI_PADDING)
        
        x_min = max(0, x_min - padding_x)
        x_max = min(w, x_max + padding_x)
        y_min = max(0, y_min - padding_y)
        y_max = min(h, y_max + padding_y)
        
        # Ensure minimum size
        width = max(config.ROI_MIN_SIZE, x_max - x_min)
        height = max(config.ROI_MIN_SIZE, y_max - y_min)
        
        # Adjust to maintain minimum size
        if x_max - x_min < config.ROI_MIN_SIZE:
            center_x = (x_min + x_max) // 2
            x_min = max(0, center_x - config.ROI_MIN_SIZE // 2)
            x_max = min(w, x_min + config.ROI_MIN_SIZE)
        
        if y_max - y_min < config.ROI_MIN_SIZE:
            center_y = (y_min + y_max) // 2
            y_min = max(0, center_y - config.ROI_MIN_SIZE // 2)
            y_max = min(h, y_min + config.ROI_MIN_SIZE)
        
        self.last_hand_bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
        return self.last_hand_bbox
    
    def draw_green_box(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Draw a green bounding box around the detected hand region.
        
        Args:
            frame: Input video frame
            bbox: Optional bounding box (x, y, w, h). If None, uses last detected.
            
        Returns:
            Frame with green box drawn
        """
        if bbox is None:
            bbox = self.last_hand_bbox
        
        if bbox:
            x, y, w, h = bbox
            # Draw green rectangle with thicker border
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 3)
            # Add a subtle green overlay inside the box (semi-transparent)
            overlay = frame.copy()
            cv2.rectangle(overlay, (x, y), (x + w, y + h), (0, 255, 0), -1)
            cv2.addWeighted(overlay, 0.1, frame, 0.9, 0, frame)
        
        return frame
    
    def process_frame(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]], bool]:
        """
        Process a single frame to extract hand landmarks.
        
        Args:
            frame: Input video frame (BGR format)
            
        Returns:
            Tuple of (landmarks array, bounding box, hand_detected)
        """
        # Convert BGR to RGB
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        
        # Process the frame
        results = self.hands.process(rgb_frame)
        
        # Prepare output
        landmarks_array = None
        bbox = None
        hand_detected = False
        
        if results.multi_hand_landmarks:
            hand_detected = True
            # Use the first hand (most confident)
            hand_landmarks = results.multi_hand_landmarks[0]
            handedness = results.multi_handedness[0].classification[0].label if results.multi_handedness else "Unknown"
            
            # Extract landmarks as array
            landmarks = []
            for landmark in hand_landmarks.landmark:
                landmarks.append([landmark.x, landmark.y, landmark.z])
            landmarks_array = np.array(landmarks)
            
            # Get ROI
            bbox = self.extract_roi(frame, hand_landmarks)
            
            # Draw landmarks on frame for debugging (optional)
            self.mp_drawing.draw_landmarks(
                frame,
                hand_landmarks,
                self.mp_hands.HAND_CONNECTIONS,
                self.mp_drawing_styles.get_default_hand_landmarks_style(),
                self.mp_drawing_styles.get_default_hand_connections_style()
            )
        else:
            self.hand_detected = False
        
        return landmarks_array, bbox, hand_detected
    
    def close(self):
        """Clean up resources."""
        self.hands.close()