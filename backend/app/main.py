import cv2
import numpy as np
import asyncio
import logging
import json
import base64
from typing import Optional
from fastapi import FastAPI, WebSocket, WebSocketDisconnect, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
import uvicorn

from .config import config
from .websocket_manager import websocket_manager
from .hand_tracker import HandTracker
from .gesture_model import GestureModel
from .sentence_builder import sentence_builder
from typing import List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="Sign Language Translation API",
    description="Real-time sign language translation using MediaPipe and LSTM",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize components
hand_tracker = HandTracker()
gesture_model = GestureModel()

# Try to load trained model if available
try:
    if gesture_model.load_model(config.MODEL_PATH):
        logger.info(f"Model loaded successfully from {config.MODEL_PATH}")
    else:
        logger.warning(f"Could not load model from {config.MODEL_PATH}, using mock predictions")
except Exception as e:
    logger.warning(f"Error loading model: {e}, using mock predictions")


@app.post("/build-sentence")
async def build_sentence_endpoint(gestures: List[str]):
    """Build a sentence from a list of gestures."""
    sentence = sentence_builder.build_sentence(gestures)
    return {"sentence": sentence, "suggestions": sentence_builder.suggest_next_gestures(gestures)}

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "name": "Sign Language Translation API",
        "version": "1.0.0",
        "status": "running",
        "model_loaded": gesture_model.is_trained,
        "supported_gestures": config.GESTURE_CLASSES
    }

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "websocket_connections": websocket_manager.get_connection_count(),
        "model_loaded": gesture_model.is_trained
    }

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    """
    WebSocket endpoint for real-time video stream processing.
    Receives frames as base64 strings and returns gesture predictions.
    """
    client_id = f"client_{websocket_manager.get_connection_count() + 1}"
    await websocket_manager.connect(websocket, client_id)
    
    try:
        while True:
            # Receive message from client
            message = await websocket_manager.receive_message(websocket)
            
            # Handle different message types
            msg_type = message.get("type", "unknown")
            
            if msg_type == "frame":
                # Process video frame
                frame_data = message.get("data", "")
                if frame_data:
                    result = await process_frame(frame_data)
                    await websocket_manager.send_message(client_id, result)
            
            elif msg_type == "reset":
                # Reset gesture sequence
                gesture_model.reset()
                await websocket_manager.send_message(client_id, {
                    "type": "reset_ack",
                    "message": "Gesture buffer reset"
                })
            
            elif msg_type == "ping":
                # Respond to ping
                await websocket_manager.send_message(client_id, {
                    "type": "pong",
                    "timestamp": message.get("timestamp")
                })
            
            elif msg_type == "get_status":
                # Send current status
                await websocket_manager.send_message(client_id, {
                    "type": "status",
                    "buffer_status": gesture_model.get_buffer_status(),
                    "model_loaded": gesture_model.is_trained
                })
            
            else:
                logger.warning(f"Unknown message type: {msg_type}")
    
    except WebSocketDisconnect:
        logger.info(f"Client {client_id} disconnected")
    except Exception as e:
        logger.error(f"Error in WebSocket handler: {e}")
    finally:
        await websocket_manager.disconnect(client_id)

async def process_frame(base64_frame: str) -> dict:
    """
    Process a single video frame and return gesture prediction.
    
    Args:
        base64_frame: Base64 encoded JPEG image
        
    Returns:
        Dictionary with prediction results
    """
    try:
        # Decode base64 to image
        img_data = base64.b64decode(base64_frame.split(',')[1] if ',' in base64_frame else base64_frame)
        np_arr = np.frombuffer(img_data, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)
        
        if frame is None:
            return {"error": "Invalid frame data"}
        
        # Resize frame for consistent processing
        frame = cv2.resize(frame, (config.TARGET_WIDTH, config.TARGET_HEIGHT))
        
        # Process frame with hand tracker
        landmarks, bbox, hand_detected = hand_tracker.process_frame(frame)
        
        # Draw green box for visual feedback
        processed_frame = hand_tracker.draw_green_box(frame, bbox)
        
        # Get gesture prediction if landmarks detected
        gesture_name = "None"
        confidence = 0.0
        
        if landmarks is not None:
            prediction = gesture_model.add_landmarks(landmarks)
            if prediction:
                gesture_name, confidence = prediction
        
        # Encode processed frame back to base64 for client display
        _, buffer = cv2.imencode('.jpg', processed_frame, [cv2.IMWRITE_JPEG_QUALITY, 85])
        processed_base64 = base64.b64encode(buffer).decode('utf-8')
        
        return {
            "type": "prediction",
            "gesture": gesture_name,
            "confidence": float(confidence),
            "hand_detected": hand_detected,
            "frame": processed_base64,
            "buffer_status": gesture_model.get_buffer_status()
        }
    
    except Exception as e:
        logger.error(f"Error processing frame: {e}")
        return {
            "type": "error",
            "error": str(e),
            "gesture": "None",
            "confidence": 0.0
        }

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    logger.info("Shutting down...")
    hand_tracker.close()