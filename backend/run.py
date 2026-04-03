#!/usr/bin/env python3
"""
Entry point for running the FastAPI application with performance monitoring.
"""

import uvicorn
from app.config import config
from app.performance_monitor import performance_monitor

if __name__ == "__main__":
    print(f"""
    ╔═══════════════════════════════════════════════════════════╗
    ║     Sign Language Translation API - Starting Server        ║
    ╚═══════════════════════════════════════════════════════════╝
    
    Server Configuration:
    • Host: {config.HOST}
    • Port: {config.PORT}
    • Model Path: {config.MODEL_PATH}
    • Sequence Length: {config.SEQUENCE_LENGTH} frames
    • Supported Gestures: {len(config.GESTURE_CLASSES)}
    
    Features:
    ✅ Real-time LSTM gesture recognition
    ✅ Advanced NLP sentence formation
    ✅ Performance monitoring
    ✅ Gesture recording & playback
    ✅ Optimized hand tracking with ROI
    
    WebSocket endpoint: ws://{config.HOST if config.HOST != '0.0.0.0' else 'localhost'}:{config.PORT}/ws
    API Documentation: http://{config.HOST if config.HOST != '0.0.0.0' else 'localhost'}:{config.PORT}/docs
    
    Press Ctrl+C to stop the server.
    """)
    
    # Start performance monitoring
    performance_monitor.start_monitoring()
    
    try:
        uvicorn.run(
            "app.main:app",
            host=config.HOST,
            port=config.PORT,
            reload=True,
            log_level="info"
        )
    finally:
        performance_monitor.stop_monitoring()