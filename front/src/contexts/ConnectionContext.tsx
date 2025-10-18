import { createContext, useContext, useState, useEffect, useRef, ReactNode } from 'react';

export interface MotorConnection {
  port: string;
  connected: boolean;
  motor_number: number | null;
  position: 'left' | 'right' | null;
  connected_at: string;
  last_command: any | null;
}

export interface ConnectionState {
  [port: string]: MotorConnection;
}

export interface AvailablePort {
  device: string;
  description: string;
  hwid: string;
}

interface ConnectionContextType {
  connections: ConnectionState;
  isConnected: boolean;
  availablePorts: AvailablePort[];
}

const ConnectionContext = createContext<ConnectionContextType | undefined>(undefined);

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';

export const ConnectionProvider = ({ children }: { children: ReactNode }) => {
  const [connections, setConnections] = useState<ConnectionState>({});
  const [isConnected, setIsConnected] = useState(false);
  const [availablePorts, setAvailablePorts] = useState<AvailablePort[]>([]);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let isCancelled = false;
    let reconnectTimeout: NodeJS.Timeout;

    const connectWebSocket = () => {
      // Create WebSocket connection
      const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
      const ws = new WebSocket(`${wsUrl}/ws/available-ports/`);
      wsRef.current = ws;

      ws.onopen = () => {
        if (isCancelled) return;
        console.log('WebSocket connection established');
        setIsConnected(true);
      };

      ws.onmessage = (event) => {
        if (isCancelled) return;
        try {
          const data = JSON.parse(event.data);
          console.log('WebSocket data:', data);

          // Update available ports if present
          if (data.ports && Array.isArray(data.ports)) {
            setAvailablePorts(data.ports);
          }
        } catch (error) {
          console.error('Error parsing WebSocket message:', error);
        }
      };

      ws.onerror = (error) => {
        if (isCancelled) return;
        console.error('WebSocket error:', error);
      };

      ws.onclose = () => {
        if (isCancelled) return;
        console.log('WebSocket connection closed');
        setIsConnected(false);

        // Reconnect after 5 seconds
        reconnectTimeout = setTimeout(() => {
          if (!isCancelled) {
            console.log('Reconnecting WebSocket...');
            connectWebSocket();
          }
        }, 5000);
      };
    };

    connectWebSocket();

    // Cleanup on unmount
    return () => {
      isCancelled = true;
      clearTimeout(reconnectTimeout);
      if (wsRef.current) {
        wsRef.current.close();
        wsRef.current = null;
      }
    };
  }, []);

  return (
    <ConnectionContext.Provider value={{ connections, isConnected, availablePorts }}>
      {children}
    </ConnectionContext.Provider>
  );
};

export const useConnectionStatus = () => {
  const context = useContext(ConnectionContext);
  if (context === undefined) {
    throw new Error('useConnectionStatus must be used within a ConnectionProvider');
  }
  return context;
};
