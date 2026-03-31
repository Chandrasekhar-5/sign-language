import asyncio
import logging
import json
from typing import Dict, Set, Optional
from datetime import datetime
from fastapi import WebSocket, WebSocketDisconnect

logger = logging.getLogger(__name__)

class WebSocketManager:
    """
    Manages WebSocket connections and message broadcasting.
    Handles multiple client connections with connection pooling.
    """
    
    def __init__(self):
        self.active_connections: Dict[str, WebSocket] = {}
        self.connection_metadata: Dict[str, dict] = {}
        self._lock = asyncio.Lock()
    
    async def connect(self, websocket: WebSocket, client_id: str) -> None:
        """
        Accept a new WebSocket connection and store it.
        
        Args:
            websocket: The WebSocket connection
            client_id: Unique identifier for the client
        """
        await websocket.accept()
        async with self._lock:
            self.active_connections[client_id] = websocket
            self.connection_metadata[client_id] = {
                "connected_at": datetime.now().isoformat(),
                "last_activity": datetime.now().isoformat()
            }
        logger.info(f"Client {client_id} connected. Total connections: {len(self.active_connections)}")
    
    async def disconnect(self, client_id: str) -> None:
        """Remove a client connection."""
        async with self._lock:
            if client_id in self.active_connections:
                del self.active_connections[client_id]
            if client_id in self.connection_metadata:
                del self.connection_metadata[client_id]
        logger.info(f"Client {client_id} disconnected. Total connections: {len(self.active_connections)}")
    
    async def send_message(self, client_id: str, message: dict) -> bool:
        """
        Send a message to a specific client.
        
        Args:
            client_id: The client to send to
            message: Dictionary message to send (will be JSON serialized)
            
        Returns:
            bool: True if message was sent successfully
        """
        if client_id not in self.active_connections:
            logger.warning(f"Attempted to send to non-existent client {client_id}")
            return False
        
        try:
            await self.active_connections[client_id].send_json(message)
            async with self._lock:
                if client_id in self.connection_metadata:
                    self.connection_metadata[client_id]["last_activity"] = datetime.now().isoformat()
            return True
        except Exception as e:
            logger.error(f"Error sending message to {client_id}: {e}")
            await self.disconnect(client_id)
            return False
    
    async def broadcast(self, message: dict, exclude_client: Optional[str] = None) -> None:
        """
        Send a message to all connected clients.
        
        Args:
            message: Dictionary message to broadcast
            exclude_client: Optional client ID to exclude from broadcast
        """
        disconnected_clients = []
        
        for client_id, connection in self.active_connections.items():
            if client_id == exclude_client:
                continue
                
            try:
                await connection.send_json(message)
            except Exception as e:
                logger.error(f"Error broadcasting to {client_id}: {e}")
                disconnected_clients.append(client_id)
        
        # Clean up disconnected clients
        for client_id in disconnected_clients:
            await self.disconnect(client_id)
    
    async def receive_message(self, websocket: WebSocket) -> dict:
        """
        Receive and parse a message from a client.
        
        Args:
            websocket: The WebSocket connection
            
        Returns:
            dict: Parsed message
        """
        try:
            data = await websocket.receive_text()
            return json.loads(data)
        except json.JSONDecodeError as e:
            logger.error(f"Invalid JSON received: {e}")
            return {"error": "Invalid JSON format"}
        except WebSocketDisconnect:
            raise
        except Exception as e:
            logger.error(f"Error receiving message: {e}")
            return {"error": str(e)}
    
    def get_connection_count(self) -> int:
        """Get the number of active connections."""
        return len(self.active_connections)
    
    def get_connection_info(self, client_id: str) -> Optional[dict]:
        """Get metadata for a specific connection."""
        return self.connection_metadata.get(client_id)

# Singleton instance
websocket_manager = WebSocketManager()