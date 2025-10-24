import { useState, useEffect, useRef } from "react";
import { Play, Square, Activity } from "lucide-react";
import { MotorCard } from "@/components/MotorCard";
import { Button } from "@/components/ui/button";
import { toast } from "sonner";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:9000';

const Index = () => {
  const [isListening, setIsListening] = useState(false);
  const [motor1Position, setMotor1Position] = useState<"left" | "right" | undefined>();
  const [motor2Position, setMotor2Position] = useState<"left" | "right" | undefined>();
  const wsRef = useRef<WebSocket | null>(null);

  // Create WebSocket connection on mount
  useEffect(() => {
    const wsUrl = API_BASE_URL.replace(/^http/, 'ws');
    const ws = new WebSocket(`${wsUrl}/ws/arduino/`);
    wsRef.current = ws;

    ws.onopen = () => {
      console.log('WebSocket connected');
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
      toast.error('Failed to connect to Arduino WebSocket');
    };

    ws.onclose = () => {
      console.log('WebSocket disconnected');
    };

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data);
        console.log('WebSocket message:', data);

        // Handle start action response
        console.log("here i m" , data);
        if (data.action === 'start') {
          if (data.success) {
            setIsListening(true);
            toast.success(data.message || 'Physics monitoring started');
          } else {
            setIsListening(false);
            toast.error(data.error || 'Failed to start listening');
          }
        }
      } catch (error) {
        console.error('Error parsing WebSocket message:', error);
      }
    };

    return () => {
      ws.close();
    };
  }, []);

  const handleStartListening = () => {
    if (!isListening) {
      // Send start message via WebSocket
      if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
        wsRef.current.send(JSON.stringify({ action: 'start' }));
        // Wait for server response to set isListening
      } else {
        toast.error("WebSocket not connected");
      }
    } else {
      setIsListening(false);
      toast.success("Stopped listening to movements");
    }
  };

  return (
    <div className="min-h-screen bg-background p-6">
      <div className="max-w-6xl mx-auto space-y-8">
        {/* Header */}
        <div className="text-center space-y-4">
          <div className="inline-flex items-center justify-center p-3 bg-primary/20 rounded-2xl mb-4">
            <Activity className="w-8 h-8 text-primary" />
          </div>
          <h1 className="text-4xl font-bold tracking-tight">Car Simulator Control</h1>
          <p className="text-lg text-muted-foreground max-w-2xl mx-auto">
            Configure and manage your dual motor connections for real-time simulation
          </p>
        </div>

        {/* Motor Cards Grid */}
        <div className="grid md:grid-cols-2 gap-6">
          <MotorCard motorNumber={0} position="left" onPositionChange={setMotor1Position} wsRef={wsRef} />
          <MotorCard motorNumber={1} position="right" onPositionChange={setMotor2Position} wsRef={wsRef} />
        </div>

        {/* Main Control Panel */}
        <div className="bg-card border-2 rounded-2xl p-8 space-y-6">
          <div className="flex items-center justify-between">
            <div>
              <h2 className="text-2xl font-semibold mb-2">Movement Listener</h2>
              <p className="text-muted-foreground">
                Start listening to motor movements and inputs
              </p>
            </div>
            <div
              className={`flex items-center gap-2 px-4 py-2 rounded-full border-2 transition-all duration-300 ${
                isListening
                  ? "border-success/50 bg-success/10"
                  : "border-border bg-secondary"
              }`}
            >
              <div
                className={`w-3 h-3 rounded-full ${
                  isListening ? "bg-success animate-pulse" : "bg-muted-foreground"
                }`}
              />
              <span className="text-sm font-medium">
                {isListening ? "Active" : "Idle"}
              </span>
            </div>
          </div>

          <Button
            onClick={handleStartListening}
            size="lg"
            className="w-full h-14 text-lg font-semibold"
            variant={isListening ? "destructive" : "default"}
          >
            {isListening ? (
              <>
                <Square className="w-5 h-5 mr-2" />
                Stop Listening
              </>
            ) : (
              <>
                <Play className="w-5 h-5 mr-2" />
                Start Listening
              </>
            )}
          </Button>

          {/* Status Info */}
          {isListening && (
            <div className="flex items-center justify-center gap-2 text-sm text-muted-foreground animate-in fade-in slide-in-from-bottom-4">
              <Activity className="w-4 h-4 animate-pulse" />
              <span>Monitoring motor movements...</span>
            </div>
          )}
        </div>

        {/* Connection Summary */}
        <div className="grid sm:grid-cols-3 gap-4 text-center">
          <div className="bg-card border rounded-xl p-4">
            <div className="text-2xl font-bold text-primary mb-1">2</div>
            <div className="text-sm text-muted-foreground">Total Motors</div>
          </div>
          <div className="bg-card border rounded-xl p-4">
            <div className="text-2xl font-bold text-success mb-1">
              {[motor1Position, motor2Position].filter(Boolean).length}
            </div>
            <div className="text-sm text-muted-foreground">Configured</div>
          </div>
          <div className="bg-card border rounded-xl p-4">
            <div className="text-2xl font-bold text-warning mb-1">
              {isListening ? "1" : "0"}
            </div>
            <div className="text-sm text-muted-foreground">Active Sessions</div>
          </div>
        </div>
      </div>
    </div>
  );
};

export default Index;
