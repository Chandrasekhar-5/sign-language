#!/usr/bin/env python3
"""
Entry point for running the FastAPI application.
"""

import uvicorn
from app.config import config

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
    
    WebSocket endpoint: ws://{config.HOST if config.HOST != '0.0.0.0' else 'localhost'}:{config.PORT}/ws
    API Documentation: http://{config.HOST if config.HOST != '0.0.0.0' else 'localhost'}:{config.PORT}/docs
    
    Press Ctrl+C to stop the server.
    """)
    
    uvicorn.run(
        "app.main:app",
        host=config.HOST,
        port=config.PORT,
        reload=True,
        log_level="info"
    )