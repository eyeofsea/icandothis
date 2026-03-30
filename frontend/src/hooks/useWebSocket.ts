'use client';

import { useEffect, useRef, useState, useCallback } from 'react';
import { io, Socket } from 'socket.io-client';
import { DisruptionEvent } from '@/lib/types';
import { useDisruptionStore } from '@/stores/disruptionStore';

const WS_URL = process.env.NEXT_PUBLIC_WS_URL || 'http://localhost:8000';

export function useWebSocket() {
  const socketRef = useRef<Socket | null>(null);
  const [connected, setConnected] = useState(false);
  const [alerts, setAlerts] = useState<{ id: string; severity: string; message: string; timestamp: string }[]>([]);
  const addDisruption = useDisruptionStore((s) => s.addDisruption);

  const connect = useCallback(() => {
    if (socketRef.current?.connected) return;

    const socket = io(WS_URL, {
      transports: ['websocket', 'polling'],
      reconnection: true,
      reconnectionDelay: 2000,
      reconnectionAttempts: 10,
    });

    socket.on('connect', () => setConnected(true));
    socket.on('disconnect', () => setConnected(false));

    socket.on('disruption', (data: DisruptionEvent) => {
      addDisruption(data);
      setAlerts((prev) => [
        { id: data.id, severity: String(data.severity), message: `${data.name}: ${data.description}`, timestamp: new Date().toISOString() },
        ...prev.slice(0, 49),
      ]);
    });

    socket.on('alert', (data: { id: string; severity: string; message: string }) => {
      setAlerts((prev) => [
        { ...data, timestamp: new Date().toISOString() },
        ...prev.slice(0, 49),
      ]);
    });

    socketRef.current = socket;
  }, [addDisruption]);

  useEffect(() => {
    connect();
    return () => {
      socketRef.current?.disconnect();
    };
  }, [connect]);

  return { connected, alerts, socket: socketRef.current };
}
