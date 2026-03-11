/**
 * WebSocket hook for real-time streaming communication
 */
import { useState, useEffect, useRef, useCallback } from 'react';

export function useWebSocket(url) {
    const [isConnected, setIsConnected] = useState(false);
    const [lastMessage, setLastMessage] = useState(null);
    const [events, setEvents] = useState([]);
    const wsRef = useRef(null);
    const reconnectRef = useRef(null);

    const connect = useCallback(() => {
        try {
            const ws = new WebSocket(url);
            wsRef.current = ws;

            ws.onopen = () => {
                setIsConnected(true);
                console.log('WebSocket connected');
            };

            ws.onmessage = (event) => {
                try {
                    const data = JSON.parse(event.data);
                    setLastMessage(data);
                    setEvents(prev => [...prev, { ...data, _receivedAt: new Date().toISOString() }]);
                } catch (e) {
                    console.error('WS parse error:', e);
                }
            };

            ws.onclose = () => {
                setIsConnected(false);
                // Auto-reconnect after 3 seconds
                reconnectRef.current = setTimeout(() => connect(), 3000);
            };

            ws.onerror = () => {
                setIsConnected(false);
            };
        } catch (e) {
            console.error('WS connection error:', e);
            setIsConnected(false);
        }
    }, [url]);

    useEffect(() => {
        connect();
        return () => {
            if (wsRef.current) wsRef.current.close();
            if (reconnectRef.current) clearTimeout(reconnectRef.current);
        };
    }, [connect]);

    const sendMessage = useCallback((data) => {
        if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
            wsRef.current.send(JSON.stringify(data));
        }
    }, []);

    const clearEvents = useCallback(() => setEvents([]), []);

    return { isConnected, lastMessage, events, sendMessage, clearEvents };
}
