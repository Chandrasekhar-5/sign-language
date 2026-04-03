import cv2
import numpy as np
import mediapipe as mp
import logging
from typing import Optional, Tuple, List, Dict
from dataclasses import dataclass, field
from collections import deque
import threading
from concurrent.futures import ThreadPoolExecutor
import time
from .config import config

logger = logging.getLogger(__name__)

@dataclass
class HandLandmarks:
    """Container for hand landmark data."""
    landmarks: List[Dict[str, float]]
    handedness: str
    confidence: float
    timestamp: float = field(default_factory=time.time)

class OptimizedHandTracker:
    """
    Optimized hand tracking with:
    - Frame skipping for performance
    - Parallel processing
    - ROI tracking for faster detection
    - Landmark caching
    """
    
    def __init__(self):
        """Initialize optimized hand tracking."""
        self.mp_hands = mp.solutions.hands
        self.hands = self.mp_hands.Hands(
            static_image_mode=False,
            max_num_hands=2,
            min_detection_confidence=config.MIN_DETECTION_CONFIDENCE,
            min_tracking_confidence=config.MIN_TRACKING_CONFIDENCE,
            model_complexity=0  # Reduced for speed (0=light, 1=full, 2=heavy)
        )
        self.mp_drawing = mp.solutions.drawing_utils
        self.mp_drawing_styles = mp.solutions.drawing_styles
        
        # Performance optimization
        self.frame_skip = 2  # Process every Nth frame
        self.frame_counter = 0
        self.last_landmarks = None
        self.last_bbox = None
        self.last_processed_time = 0
        self.processing_interval = 1.0 / 30  # Max 30 FPS processing
        
        # ROI tracking for faster detection
        self.roi_tracking = True
        self.roi_expand = 1.2  # Expand ROI by 20%
        self.tracking_threshold = 0.3  # Tracking confidence threshold
        
        # Parallel processing
        self.executor = ThreadPoolExecutor(max_workers=2)
        self.processing_future = None
        
        # Caching
        self.landmark_cache = {}
        self.cache_size = 10
        
        # Performance metrics
        self.metrics = {
            'detection_time': [],
            'processing_time': [],
            'fps': [],
            'last_fps': 0
        }
        
    def process_frame_optimized(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]], bool]:
        """
        Optimized frame processing with frame skipping and ROI tracking.
        
        Args:
            frame: Input video frame
            
        Returns:
            Tuple of (landmarks array, bounding box, hand_detected)
        """
        start_time = time.time()
        
        # Frame skipping for performance
        self.frame_counter += 1
        if self.frame_counter % self.frame_skip != 0:
            # Return cached landmarks if available
            if self.last_landmarks is not None:
                return self.last_landmarks, self.last_bbox, True
            return None, None, False
        
        # Rate limiting
        current_time = time.time()
        if current_time - self.last_processed_time < self.processing_interval:
            if self.last_landmarks is not None:
                return self.last_landmarks, self.last_bbox, True
            return None, None, False
        
        self.last_processed_time = current_time
        
        # Process frame
        landmarks_array, bbox, hand_detected = self._process_frame_internal(frame)
        
        # Update cache
        if landmarks_array is not None:
            self.last_landmarks = landmarks_array
            self.last_bbox = bbox
            self._update_cache(landmarks_array)
        
        # Update metrics
        processing_time = (time.time() - start_time) * 1000
        self.metrics['processing_time'].append(processing_time)
        if len(self.metrics['processing_time']) > 100:
            self.metrics['processing_time'].pop(0)
        
        return landmarks_array, bbox, hand_detected
    
    def _process_frame_internal(self, frame: np.ndarray) -> Tuple[Optional[np.ndarray], Optional[Tuple[int, int, int, int]], bool]:
        """
        Internal frame processing with ROI optimization.
        """
        h, w = frame.shape[:2]
        
        # Apply ROI if we're tracking a hand
        if self.roi_tracking and self.last_bbox is not None:
            x, y, bw, bh = self.last_bbox
            # Expand ROI
            expand_w = int(bw * (self.roi_expand - 1) / 2)
            expand_h = int(bh * (self.roi_expand - 1) / 2)
            
            roi_x = max(0, x - expand_w)
            roi_y = max(0, y - expand_h)
            roi_w = min(w - roi_x, bw + 2 * expand_w)
            roi_h = min(h - roi_y, bh + 2 * expand_h)
            
            # Extract ROI
            roi_frame = frame[roi_y:roi_y+roi_h, roi_x:roi_x+roi_w]
            if roi_frame.size > 0:
                # Process only ROI
                rgb_roi = cv2.cvtColor(roi_frame, cv2.COLOR_BGR2RGB)
                rgb_roi.flags.writeable = False
                results = self.hands.process(rgb_roi)
                
                if results.multi_hand_landmarks:
                    # Convert landmarks back to original coordinates
                    hand_landmarks = results.multi_hand_landmarks[0]
                    for landmark in hand_landmarks.landmark:
                        landmark.x = landmark.x * roi_w / w + roi_x / w
                        landmark.y = landmark.y * roi_h / h + roi_y / h
                    
                    return self._extract_landmarks(hand_landmarks, frame)
        
        # Process full frame
        rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        rgb_frame.flags.writeable = False
        results = self.hands.process(rgb_frame)
        
        if results.multi_hand_landmarks:
            return self._extract_landmarks(results.multi_hand_landmarks[0], frame)
        
        return None, None, False
    
    def _extract_landmarks(self, hand_landmarks, frame: np.ndarray) -> Tuple[np.ndarray, Tuple[int, int, int, int], bool]:
        """
        Extract landmarks and calculate bounding box.
        """
        h, w = frame.shape[:2]
        
        # Extract landmarks
        landmarks = []
        for landmark in hand_landmarks.landmark:
            landmarks.append([landmark.x, landmark.y, landmark.z])
        landmarks_array = np.array(landmarks)
        
        # Calculate bounding box
        xs = [lm[0] * w for lm in landmarks_array]
        ys = [lm[1] * h for lm in landmarks_array]
        
        x_min = max(0, int(min(xs) - 20))
        x_max = min(w, int(max(xs) + 20))
        y_min = max(0, int(min(ys) - 20))
        y_max = min(h, int(max(ys) + 20))
        
        bbox = (x_min, y_min, x_max - x_min, y_max - y_min)
        
        return landmarks_array, bbox, True
    
    def _update_cache(self, landmarks: np.ndarray):
        """Update landmark cache."""
        cache_key = hash(landmarks.tobytes())
        self.landmark_cache[cache_key] = landmarks
        if len(self.landmark_cache) > self.cache_size:
            self.landmark_cache.pop(next(iter(self.landmark_cache)))
    
    def draw_green_box(self, frame: np.ndarray, bbox: Optional[Tuple[int, int, int, int]] = None) -> np.ndarray:
        """
        Draw optimized green box with gradient effect.
        """
        if bbox is None:
            bbox = self.last_bbox
        
        if bbox:
            x, y, w, h = bbox
            
            # Draw outer glow effect
            for i in range(3, 0, -1):
                alpha = 0.3 / i
                overlay = frame.copy()
                cv2.rectangle(overlay, (x - i, y - i), (x + w + i, y + h + i), (0, 255, 0), -1)
                cv2.addWeighted(overlay, alpha, frame, 1 - alpha, 0, frame)
            
            # Draw main rectangle
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            
            # Draw corner accents
            corner_len = min(20, w // 4, h // 4)
            cv2.line(frame, (x, y), (x + corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x, y), (x, y + corner_len), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y), (x + w - corner_len, y), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y), (x + w, y + corner_len), (0, 255, 0), 3)
            cv2.line(frame, (x, y + h), (x + corner_len, y + h), (0, 255, 0), 3)
            cv2.line(frame, (x, y + h), (x, y + h - corner_len), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y + h), (x + w - corner_len, y + h), (0, 255, 0), 3)
            cv2.line(frame, (x + w, y + h), (x + w, y + h - corner_len), (0, 255, 0), 3)
        
        return frame
    
    def get_performance_metrics(self) -> dict:
        """Get performance metrics."""
        avg_processing = np.mean(self.metrics['processing_time']) if self.metrics['processing_time'] else 0
        return {
            'avg_processing_time_ms': avg_processing,
            'frame_skip': self.frame_skip,
            'roi_tracking': self.roi_tracking,
            'cache_size': len(self.landmark_cache)
        }
    
    def close(self):
        """Clean up resources."""
        self.executor.shutdown(wait=False)
        self.hands.close()