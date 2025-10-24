import { useState, useEffect, useRef } from "react";
import { Settings, Plug, PlugZap, ArrowUp, ArrowDown, AlertTriangle } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { cn } from "@/lib/utils";
import { useMotorByNumber, updateMotorPosition, useConnectionStatus } from "@/hooks/useConnectionStatus";
import { toast } from "sonner";

interface MotorCardProps {
  motorNumber: 0 | 1; // 0 left, 1 right
  position: "left" | "right";
  onPositionChange?: (position: "left" | "right") => void;
  wsRef: React.RefObject<WebSocket | null>;
}

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';

export const MotorCard = ({ motorNumber, position, onPositionChange, wsRef }: MotorCardProps) => {
  const motorConnection = useMotorByNumber(motorNumber);
  const { availablePorts } = useConnectionStatus();
  const [isUpdatingPosition, setIsUpdatingPosition] = useState(false);
  const [selectedPort, setSelectedPort] = useState<string | undefined>(undefined);
  const [isArduinoConnected, setIsArduinoConnected] = useState(false);
  const [isConnecting, setIsConnecting] = useState(false);
  const intervalRef = useRef<NodeJS.Timeout | null>(null);

  // Use real-time connection data from backend or local selection
  const isConnected = motorConnection?.connected || isArduinoConnected;
  const port = motorConnection?.port || selectedPort;

  // Notify parent of position changes from backend
  useEffect(() => {
    if (position) {
      onPositionChange?.(position);
    }
  }, [position, onPositionChange]);

  // Cleanup interval on unmount
  useEffect(() => {
    return () => {
      if (intervalRef.current) {
        clearInterval(intervalRef.current);
        intervalRef.current = null;
      }
    };
  }, []);

  const handlePortSelect = async (portDevice: string) => {
    setSelectedPort(portDevice);
    setIsConnecting(true);

    try {
      // Send connect message via existing WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({
          action: 'connect',
          port: portDevice,
          motor: motorNumber
        }));

        // Listen for connection response
        const handleMessage = (event: MessageEvent) => {
          try {
            const data = JSON.parse(event.data);
            if (data.action === 'connect' && data.motor === motorNumber) {
              if (data.success) {
                setIsArduinoConnected(true);
                setIsConnecting(false);
                toast.success(`Motor ${motorNumber} connected on ${portDevice}`);
                // Notify parent with position
                onPositionChange?.(position);
              } else {
                setIsArduinoConnected(false);
                setIsConnecting(false);
                setSelectedPort(undefined);
                toast.error(data.error || `Failed to connect motor ${motorNumber}`);
              }
              wsRef.current?.removeEventListener('message', handleMessage);
            }
          } catch (error) {
            console.error('Error parsing WebSocket message:', error);
          }
        };

        wsRef.current.addEventListener('message', handleMessage);

        // Timeout after 5 seconds
        setTimeout(() => {
          if (isConnecting) {
            setIsConnecting(false);
            setSelectedPort(undefined);
            toast.error('Connection timeout');
            wsRef.current?.removeEventListener('message', handleMessage);
          }
        }, 5000);
      } else {
        throw new Error('WebSocket not connected');
      }
    } catch (error) {
      console.error('Error connecting to Arduino:', error);
      setIsConnecting(false);
      setSelectedPort(undefined);
      toast.error(`Failed to connect to Arduino on ${portDevice}`);
    }
  };

  const sendCommand = (command: 'f' | 'b') => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        action: 'command',
        motor: motorNumber,
        command
      }));
    }
  };

  const handleMouseDown = (command: 'f' | 'b') => {
    // Send immediately on press
    sendCommand(command);

    // Send repeatedly while holding
    intervalRef.current = setInterval(() => {
      sendCommand(command);
    }, 100); // Send every 100ms
  };

  const handleMouseUp = () => {
    // Stop sending when released
    if (intervalRef.current) {
      clearInterval(intervalRef.current);
      intervalRef.current = null;
    }
  };

  return (
    <Card className="p-6 border-2 transition-all duration-300 hover:border-primary/50">
      <div className="space-y-6">
        {/* Header */}
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div
              className={cn(
                "relative p-3 rounded-xl transition-all duration-500",
                isConnected
                  ? "bg-success/20 text-success"
                  : "bg-muted text-muted-foreground"
              )}
            >
              {isConnected ? (
                <PlugZap className="w-6 h-6 animate-pulse" />
              ) : (
                <Plug className="w-6 h-6" />
              )}
              {isConnected && (
                <div className="absolute -top-1 -right-1 w-3 h-3 bg-success rounded-full animate-pulse" />
              )}
            </div>
            <div>
              <h3 className="text-xl font-semibold">{motorNumber === 0 ? "Left Motor" : "Right Motor"}</h3>
              <p className="text-sm text-muted-foreground">
                {isConnected ? "Connected" : "Disconnected"}
              </p>
            </div>
          </div>
          <Settings className="w-5 h-5 text-muted-foreground" />
        </div>

        {/* Connection Status Bar */}
        <div className="relative h-2 bg-secondary rounded-full overflow-hidden">
          <div
            className={cn(
              "absolute inset-y-0 left-0 transition-all duration-500",
              isConnected
                ? "w-full bg-gradient-to-r from-success to-success/50"
                : "w-0 bg-destructive"
            )}
          />
        </div>

        {/* Port Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Motor Port</label>
          <Select
            value={selectedPort}
            onValueChange={handlePortSelect}
            disabled={availablePorts.length === 0}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder={availablePorts.length === 0 ? "No ports available" : "Select port"} />
            </SelectTrigger>
            <SelectContent>
              {availablePorts.map((port) => (
                <SelectItem key={port.device} value={port.device}>
                  {port.device}
                </SelectItem>
              ))}
            </SelectContent>
          </Select>
        </div>

        {/* Warning Alert when port is selected */}
        {isArduinoConnected && (
          <Alert className="border-yellow-500 bg-yellow-500/10">
            <AlertTriangle className="h-4 w-4 text-yellow-500" />
            <AlertDescription className="text-sm font-medium">
              Attention! Keep the potentiometer disconnected during initial positioning configuration
            </AlertDescription>
          </Alert>
        )}

        {/* Motor Control Actions */}
        <div className="flex gap-3">
          <Button
            onMouseDown={() => handleMouseDown('f')}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onTouchStart={() => handleMouseDown('f')}
            onTouchEnd={handleMouseUp}
            disabled={!isArduinoConnected || isConnecting}
            className="flex-1"
            variant="default"
          >
            <ArrowDown className="w-4 h-4 mr-2" />
            Forward
          </Button>
          <Button
            onMouseDown={() => handleMouseDown('b')}
            onMouseUp={handleMouseUp}
            onMouseLeave={handleMouseUp}
            onTouchStart={() => handleMouseDown('b')}
            onTouchEnd={handleMouseUp}
            disabled={!isArduinoConnected || isConnecting}
            className="flex-1"
            variant="default"
          >
            <ArrowUp className="w-4 h-4 mr-2" />
            Backward
          </Button>
        </div>

        {/* Status Indicator */}
        <div
          className={cn(
            "flex items-center gap-2 p-3 rounded-lg border-2 transition-all duration-300",
            isConnected
              ? "border-success/50 bg-success/10"
              : "border-destructive/50 bg-destructive/10"
          )}
        >
          <div
            className={cn(
              "w-2 h-2 rounded-full",
              isConnected ? "bg-success animate-pulse" : "bg-destructive"
            )}
          />
          <span className="text-sm font-medium">
            {isConnected
              ? `Connected ${selectedPort ? `(${selectedPort})` : ""}`
              : "Awaiting connection"}
          </span>
        </div>
      </div>
    </Card>
  );
};
