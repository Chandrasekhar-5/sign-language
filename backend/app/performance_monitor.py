"""
Real-time performance monitoring and optimization.
"""

import time
import threading
import psutil
import GPUtil
import logging
from typing import Dict, List, Optional
from collections import deque
from dataclasses import dataclass, field
import numpy as np

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetrics:
    """Performance metrics container."""
    timestamp: float = field(default_factory=time.time)
    cpu_percent: float = 0
    memory_percent: float = 0
    gpu_usage: Optional[float] = None
    inference_time_ms: float = 0
    fps: float = 0
    frame_processing_time_ms: float = 0
    buffer_size: int = 0
    queue_size: int = 0

class PerformanceMonitor:
    """
    Real-time performance monitoring and auto-optimization.
    """
    
    def __init__(self):
        """Initialize performance monitor."""
        self.metrics_history = deque(maxlen=300)  # 10 seconds at 30 FPS
        self.monitoring = False
        self.monitor_thread = None
        self.optimization_enabled = True
        
        # Performance thresholds
        self.thresholds = {
            'cpu_warning': 80,  # 80% CPU usage
            'cpu_critical': 90,
            'memory_warning': 80,
            'memory_critical': 90,
            'fps_min': 15,  # Minimum acceptable FPS
            'fps_target': 30,
            'inference_time_max': 50  # Max 50ms per inference
        }
        
        # Optimization suggestions
        self.optimizations = {
            'reduce_frame_skip': {'action': 'decrease', 'current': 2, 'min': 1},
            'reduce_processing_resolution': {'action': 'downscale', 'current': 1.0, 'min': 0.5},
            'disable_visualization': {'action': 'disable', 'current': True, 'min': False},
            'use_gpu_delegate': {'action': 'enable', 'current': True, 'min': True}
        }
        
    def start_monitoring(self):
        """Start performance monitoring in background thread."""
        if self.monitoring:
            return
        
        self.monitoring = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Performance monitoring started")
    
    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.monitoring = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=2)
        logger.info("Performance monitoring stopped")
    
    def _monitor_loop(self):
        """Main monitoring loop."""
        while self.monitoring:
            try:
                metrics = self.collect_metrics()
                self.metrics_history.append(metrics)
                
                # Check for performance issues
                if self.optimization_enabled:
                    self._check_and_optimize(metrics)
                
                time.sleep(1)  # Update every second
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def collect_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        metrics = PerformanceMetrics()
        
        # CPU usage
        metrics.cpu_percent = psutil.cpu_percent(interval=0.1)
        
        # Memory usage
        memory = psutil.virtual_memory()
        metrics.memory_percent = memory.percent
        
        # GPU usage (if available)
        try:
            gpus = GPUtil.getGPUs()
            if gpus:
                metrics.gpu_usage = gpus[0].load * 100
        except:
            pass
        
        return metrics
    
    def record_inference(self, inference_time_ms: float):
        """Record inference time."""
        if self.metrics_history:
            current = self.metrics_history[-1]
            current.inference_time_ms = inference_time_ms
    
    def record_frame_processing(self, processing_time_ms: float):
        """Record frame processing time."""
        if self.metrics_history:
            current = self.metrics_history[-1]
            current.frame_processing_time_ms = processing_time_ms
    
    def update_fps(self, fps: float):
        """Update current FPS."""
        if self.metrics_history:
            current = self.metrics_history[-1]
            current.fps = fps
    
    def _check_and_optimize(self, metrics: PerformanceMetrics):
        """Check metrics and suggest optimizations."""
        issues = []
        
        # Check CPU usage
        if metrics.cpu_percent > self.thresholds['cpu_critical']:
            issues.append(('critical', 'cpu', metrics.cpu_percent))
        elif metrics.cpu_percent > self.thresholds['cpu_warning']:
            issues.append(('warning', 'cpu', metrics.cpu_percent))
        
        # Check memory usage
        if metrics.memory_percent > self.thresholds['memory_critical']:
            issues.append(('critical', 'memory', metrics.memory_percent))
        elif metrics.memory_percent > self.thresholds['memory_warning']:
            issues.append(('warning', 'memory', metrics.memory_percent))
        
        # Check FPS
        if metrics.fps > 0 and metrics.fps < self.thresholds['fps_min']:
            issues.append(('critical', 'fps', metrics.fps))
        
        # Apply optimizations based on issues
        if issues:
            self._apply_optimizations(issues)
    
    def _apply_optimizations(self, issues: List[tuple]):
        """Apply optimizations based on detected issues."""
        critical_issues = [i for i in issues if i[0] == 'critical']
        
        if critical_issues:
            # Aggressive optimization
            self.optimizations['reduce_frame_skip']['current'] = max(
                self.optimizations['reduce_frame_skip']['min'],
                self.optimizations['reduce_frame_skip']['current'] + 1
            )
            self.optimizations['reduce_processing_resolution']['current'] = max(
                self.optimizations['reduce_processing_resolution']['min'],
                self.optimizations['reduce_processing_resolution']['current'] - 0.1
            )
            logger.warning(f"Aggressive optimization applied due to: {critical_issues}")
        
        elif issues:
            # Moderate optimization
            if any(i[1] == 'cpu' for i in issues):
                self.optimizations['reduce_frame_skip']['current'] = min(
                    4,
                    self.optimizations['reduce_frame_skip']['current'] + 1
                )
            logger.info(f"Moderate optimization applied")
    
    def get_current_metrics(self) -> Optional[PerformanceMetrics]:
        """Get current performance metrics."""
        if self.metrics_history:
            return self.metrics_history[-1]
        return None
    
    def get_average_metrics(self, window_seconds: int = 5) -> Dict:
        """Get average metrics over time window."""
        if not self.metrics_history:
            return {}
        
        # Calculate window size based on FPS
        window_size = min(len(self.metrics_history), window_seconds)
        recent = list(self.metrics_history)[-window_size:]
        
        return {
            'avg_cpu': np.mean([m.cpu_percent for m in recent]),
            'avg_memory': np.mean([m.memory_percent for m in recent]),
            'avg_inference_time': np.mean([m.inference_time_ms for m in recent if m.inference_time_ms > 0]),
            'avg_fps': np.mean([m.fps for m in recent if m.fps > 0]),
            'current_fps': recent[-1].fps if recent else 0
        }
    
    def get_optimization_status(self) -> Dict:
        """Get current optimization settings."""
        return self.optimizations

# Singleton instance
performance_monitor = PerformanceMonitor()