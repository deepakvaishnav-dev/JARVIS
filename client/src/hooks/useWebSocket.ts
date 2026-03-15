import { useState, useEffect, useRef } from "react";
import toast from "react-hot-toast";

export interface ChatMessage {
  id: string;
  role: "user" | "model";
  content: string;
}

export function useWebSocket(url: string, onComplete?: (text: string) => void) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [isConnected, setIsConnected] = useState(false);
  const [isGenerating, setIsGenerating] = useState(false);
  const ws = useRef<WebSocket | null>(null);
  const currentResponseRef = useRef("");
  const shouldSpeakRef = useRef(false);

  useEffect(() => {
    let reconnectTimeout: ReturnType<typeof setTimeout>;
    let pingInterval: ReturnType<typeof setInterval>;
    let isMounted = true;

    function connect() {
      if (!isMounted) return;

      if (ws.current) {
        const oldWs = ws.current;
        oldWs.onclose = null; // Prevent reconnect logic from firing
        if (oldWs.readyState === WebSocket.OPEN) {
          oldWs.close();
        } else if (oldWs.readyState === WebSocket.CONNECTING) {
          oldWs.onopen = () => {
             oldWs.close();
          };
        }
      }

      ws.current = new WebSocket(url);

      ws.current.onopen = () => {
        if (!isMounted) {
          ws.current?.close();
          return;
        }
        console.log("Connected to JARVIS WS");
        setIsConnected(true);

        // Start heartbeat
        pingInterval = setInterval(() => {
          if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send("__ping__");
          }
        }, 30000);
      };

      ws.current.onclose = () => {
        if (!isMounted) return;
        console.log("Disconnected from JARVIS WS");
        setIsConnected(false);
        clearInterval(pingInterval);

        // Reconnect after 2 seconds only if still mounted
        clearTimeout(reconnectTimeout);
        reconnectTimeout = setTimeout(connect, 2000);
      };

      ws.current.onmessage = (event) => {
        if (!isMounted) return;
        const data = JSON.parse(event.data);

        // Ignore heartbeats
        if (data.pong) return;

        if (data.error) {
          console.error("WS Error:", data.error);
          toast.error(data.error);
          setIsGenerating(false);
          return;
        }

        if (data.done) {
          setIsGenerating(false);
          // Trigger TTS callback using the accumulated buffer
          if (
            onComplete &&
            currentResponseRef.current &&
            shouldSpeakRef.current
          ) {
            // Strip the markdown status indicators used by Orchestrator if necessary
            // or just pass as-is.
            const textToSpeak = currentResponseRef.current.replace(
              /\*.*?\*\n\n/g,
              "",
            );
            setTimeout(() => onComplete(textToSpeak), 10);
          }
          currentResponseRef.current = ""; // Reset for next response
          return;
        }

        if (data.token) {
          currentResponseRef.current += data.token;
          setMessages((prev) => {
            const newMessages = [...prev];
            const lastMsgIdx = newMessages.length - 1;
            const lastMsg = newMessages[lastMsgIdx];
            if (lastMsg && lastMsg.role === "model") {
              const updatedMsg = {
                ...lastMsg,
                content: lastMsg.content + data.token,
              };
              newMessages[lastMsgIdx] = updatedMsg;
            }
            return newMessages;
          });
        }
      };
    }

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimeout);
      clearInterval(pingInterval);
      if (ws.current) {
        const oldWs = ws.current;
        oldWs.onclose = null; // Prevent reconnect logic from firing on unmount
        if (oldWs.readyState === WebSocket.OPEN) {
          oldWs.close();
        } else if (oldWs.readyState === WebSocket.CONNECTING) {
          // If we close while connecting, it throws the warning.
          // Better to set onopen to close it immediately once established.
          oldWs.onopen = () => {
             oldWs.close();
          };
        }
      }
    };
  }, [url, onComplete]);

  const sendMessage = (text: string, isVoice: boolean = false) => {
    if (ws.current && isConnected) {
      const newUserMsg: ChatMessage = {
        id: Date.now().toString(),
        role: "user",
        content: text,
      };
      const emptyModelMsg: ChatMessage = {
        id: (Date.now() + 1).toString(),
        role: "model",
        content: "",
      };

      setMessages((prev) => [...prev, newUserMsg, emptyModelMsg]);
      setIsGenerating(true);
      currentResponseRef.current = "";
      shouldSpeakRef.current = isVoice;
      ws.current.send(text);
    }
  };

  return { messages, isConnected, isGenerating, sendMessage };
}
