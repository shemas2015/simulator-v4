import { useState, useEffect } from "react";
import { Settings, Loader2, Plug, PlugZap } from "lucide-react";
import { Card } from "@/components/ui/card";
import { Button } from "@/components/ui/button";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { cn } from "@/lib/utils";
import { useMotorByNumber, updateMotorPosition } from "@/hooks/useConnectionStatus";
import { toast } from "sonner";

interface MotorCardProps {
  motorNumber: 1 | 2;
  onPositionChange?: (position: "left" | "right") => void;
}

export const MotorCard = ({ motorNumber, onPositionChange }: MotorCardProps) => {
  const motorConnection = useMotorByNumber(motorNumber);
  const [isTesting, setIsTesting] = useState(false);
  const [isUpdatingPosition, setIsUpdatingPosition] = useState(false);

  // Use real-time connection data from backend
  const isConnected = motorConnection?.connected || false;
  const position = motorConnection?.position || undefined;
  const port = motorConnection?.port;

  // Notify parent of position changes from backend
  useEffect(() => {
    if (position) {
      onPositionChange?.(position);
    }
  }, [position, onPositionChange]);

  const handleTestConnection = async () => {
    setIsTesting(true);
    // Simulate connection test
    await new Promise((resolve) => setTimeout(resolve, 2000));
    setIsTesting(false);
    toast.success("Connection test completed");
  };

  const handlePositionChange = async (value: "left" | "right") => {
    if (!port) {
      toast.error("No motor port available");
      return;
    }

    setIsUpdatingPosition(true);
    try {
      await updateMotorPosition(port, value);
      toast.success(`Motor position updated to ${value}`);
    } catch (error) {
      toast.error("Failed to update motor position");
      console.error(error);
    } finally {
      setIsUpdatingPosition(false);
    }
  };

  const handleDisconnect = () => {
    toast.info("Disconnect motor from backend to update status");
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
              <h3 className="text-xl font-semibold">Motor {motorNumber}</h3>
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

        {/* Position Selection */}
        <div className="space-y-2">
          <label className="text-sm font-medium">Motor Position</label>
          <Select
            value={position}
            onValueChange={handlePositionChange}
            disabled={!isConnected || isUpdatingPosition}
          >
            <SelectTrigger className="w-full">
              <SelectValue placeholder="Select position" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="left">Left Motor</SelectItem>
              <SelectItem value="right">Right Motor</SelectItem>
            </SelectContent>
          </Select>
        </div>

        {/* Actions */}
        <div className="flex gap-3">
          {!isConnected ? (
            <Button
              onClick={handleTestConnection}
              disabled={isTesting}
              className="flex-1"
              variant={isTesting ? "secondary" : "default"}
            >
              {isTesting ? (
                <>
                  <Loader2 className="w-4 h-4 mr-2 animate-spin" />
                  Testing...
                </>
              ) : (
                "Test Connection"
              )}
            </Button>
          ) : (
            <Button
              onClick={handleDisconnect}
              variant="destructive"
              className="flex-1"
            >
              Disconnect
            </Button>
          )}
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
              ? `Ready ${position ? `(${position})` : ""}`
              : "Awaiting connection"}
          </span>
        </div>
      </div>
    </Card>
  );
};
