// Re-export from context for backward compatibility
import { useConnectionStatus as useConnectionStatusContext } from '@/contexts/ConnectionContext';
export { useConnectionStatus, ConnectionProvider } from '@/contexts/ConnectionContext';
export type { MotorConnection, ConnectionState } from '@/contexts/ConnectionContext';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';

export const useMotorByNumber = (motorNumber: 0 | 1) => {
  const { connections } = useConnectionStatusContext();

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
