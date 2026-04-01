/**
 * WebSocket service for real-time communication with Python backend
 */

export type Prediction = {
  gesture: string;
  confidence: number;
  hand_detected: boolean;
  frame: string;
  buffer_status: {
    buffer_size: number;
    max_size: number;
    is_ready: boolean;
  };
};

export type WebSocketMessage = {
  type: 'prediction' | 'error' | 'reset_ack' | 'pong' | 'status';
  gesture?: string;
  confidence?: number;
  hand_detected?: boolean;
  frame?: string;
  error?: string;
  message?: string;
  timestamp?: string;
  buffer_status?: any;
};

export type WebSocketCallbacks = {
  onPrediction?: (prediction: Prediction) => void;
  onError?: (error: string) => void;
  onConnected?: () => void;
  onDisconnected?: () => void;
  onResetAck?: (message: string) => void;
};

class WebSocketService {
  private ws: WebSocket | null = null;
  private callbacks: WebSocketCallbacks = {};
  private reconnectAttempts = 0;
  private maxReconnectAttempts = 5;
  private reconnectDelay = 1000;
  private pingInterval: NodeJS.Timeout | null = null;
  private isConnected = false;

  /**
   * Connect to the WebSocket server
   */
  connect(wsUrl: string): Promise<void> {
    return new Promise((resolve, reject) => {
      try {
        this.ws = new WebSocket(wsUrl);

        this.ws.onopen = () => {
          console.log('WebSocket connected');
          this.isConnected = true;
          this.reconnectAttempts = 0;
          
          // Start ping interval to keep connection alive
          this.startPingInterval();
          
          if (this.callbacks.onConnected) {
            this.callbacks.onConnected();
          }
          resolve();
        };

        this.ws.onmessage = (event) => {
          try {
            const data = JSON.parse(event.data) as WebSocketMessage;
            this.handleMessage(data);
          } catch (e) {
            console.error('Failed to parse WebSocket message:', e);
          }
        };

        this.ws.onerror = (error) => {
          console.error('WebSocket error:', error);
          if (this.callbacks.onError) {
            this.callbacks.onError('WebSocket connection error');
          }
          reject(error);
        };

        this.ws.onclose = () => {
          console.log('WebSocket disconnected');
          this.isConnected = false;
          this.stopPingInterval();
          
          if (this.callbacks.onDisconnected) {
            this.callbacks.onDisconnected();
          }
          
          // Attempt reconnect
          if (this.reconnectAttempts < this.maxReconnectAttempts) {
            setTimeout(() => {
              this.reconnectAttempts++;
              console.log(`Attempting to reconnect (${this.reconnectAttempts}/${this.maxReconnectAttempts})...`);
              this.connect(wsUrl).catch(console.error);
            }, this.reconnectDelay * this.reconnectAttempts);
          }
        };
      } catch (error) {
        reject(error);
      }
    });
  }

  /**
   * Handle incoming WebSocket messages
   */
  private handleMessage(data: WebSocketMessage): void {
    switch (data.type) {
      case 'prediction':
        if (this.callbacks.onPrediction && data.gesture !== undefined) {
          this.callbacks.onPrediction({
            gesture: data.gesture,
            confidence: data.confidence || 0,
            hand_detected: data.hand_detected || false,
            frame: data.frame || '',
            buffer_status: data.buffer_status || { buffer_size: 0, max_size: 30, is_ready: false }
          });
        }
        break;
      
      case 'error':
        if (this.callbacks.onError) {
          this.callbacks.onError(data.error || 'Unknown error');
        }
        break;
      
      case 'reset_ack':
        if (this.callbacks.onResetAck) {
          this.callbacks.onResetAck(data.message || 'Reset successful');
        }
        break;
      
      case 'pong':
        // Ping response - keep connection alive
        break;
      
      case 'status':
        // Status update - can be used for debugging
        console.log('Server status:', data);
        break;
      
      default:
        console.log('Unknown message type:', data.type);
    }
  }

  /**
   * Send a video frame to the server
   */
  sendFrame(base64Frame: string): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'frame',
        data: base64Frame
      }));
    }
  }

  /**
   * Reset the gesture buffer on the server
   */
  resetBuffer(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'reset'
      }));
    }
  }

  /**
   * Get server status
   */
  getStatus(): void {
    if (this.ws && this.ws.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify({
        type: 'get_status'
      }));
    }
  }

  /**
   * Start ping interval to keep connection alive
   */
  private startPingInterval(): void {
    this.pingInterval = setInterval(() => {
      if (this.ws && this.ws.readyState === WebSocket.OPEN) {
        this.ws.send(JSON.stringify({
          type: 'ping',
          timestamp: Date.now()
        }));
      }
    }, 20000); // Ping every 20 seconds
  }

  /**
   * Stop ping interval
   */
  private stopPingInterval(): void {
    if (this.pingInterval) {
      clearInterval(this.pingInterval);
      this.pingInterval = null;
    }
  }

  /**
   * Set callbacks for WebSocket events
   */
  setCallbacks(callbacks: WebSocketCallbacks): void {
    this.callbacks = { ...this.callbacks, ...callbacks };
  }

  /**
   * Disconnect from the server
   */
  disconnect(): void {
    this.stopPingInterval();
    if (this.ws) {
      this.ws.close();
      this.ws = null;
    }
    this.isConnected = false;
  }

  /**
   * Check if connected
   */
  get isConnectedToServer(): boolean {
    return this.isConnected && this.ws?.readyState === WebSocket.OPEN;
  }
}

// Singleton instance
export const websocketService = new WebSocketService();