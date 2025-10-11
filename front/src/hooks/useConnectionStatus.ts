import { useState, useEffect, useRef } from 'react';

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

const API_BASE_URL = 'http://100.93.112.98:8000';

export const useConnectionStatus = () => {
  const [connections, setConnections] = useState<ConnectionState>({});
  const [isConnected, setIsConnected] = useState(false);
  const eventSourceRef = useRef<EventSource | null>(null);

  useEffect(() => {
    // Create SSE connection
    const eventSource = new EventSource(`${API_BASE_URL}/api/events/connections/`);
    eventSourceRef.current = eventSource;

    eventSource.onopen = () => {
      console.log('SSE connection established');
      setIsConnected(true);
    };

    eventSource.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);

        if (data.type === 'init' || data.type === 'update') {
          setConnections(data.connections);
        }
      } catch (error) {
        console.error('Error parsing SSE message:', error);
      }
    };

    eventSource.onerror = (error) => {
      console.error('SSE error:', error);
      setIsConnected(false);

      // Reconnect after 5 seconds
      setTimeout(() => {
        if (eventSourceRef.current?.readyState === EventSource.CLOSED) {
          eventSource.close();
          // The effect will recreate the connection on next render
        }
      }, 5000);
    };

    // Cleanup on unmount
    return () => {
      eventSource.close();
      eventSourceRef.current = null;
    };
  }, []);

  return {
    connections,
    isConnected,
  };
};

export const useMotorByNumber = (motorNumber: 1 | 2) => {
  const { connections } = useConnectionStatus();

  // Find connection with matching motor_number
  const motorConnection = Object.values(connections).find(
    (conn) => conn.motor_number === motorNumber
  );

  return motorConnection || null;
};

export const updateMotorPosition = async (port: string, position: 'left' | 'right') => {
  try {
    const response = await fetch(`${API_BASE_URL}/api/connections/${encodeURIComponent(port)}/position/`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ position }),
    });

    if (!response.ok) {
      throw new Error('Failed to update motor position');
    }

    return await response.json();
  } catch (error) {
    console.error('Error updating motor position:', error);
    throw error;
  }
};
