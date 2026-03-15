import { useState, useRef, useCallback, useEffect } from "react";
import toast from "react-hot-toast";

// Add missing types for Web Speech API
interface SpeechRecognitionEvent extends Event {
  resultIndex: number;
  results: {
    [index: number]: {
      [index: number]: {
        transcript: string;
      };
    };
  };
}

interface SpeechRecognitionErrorEvent extends Event {
  error: string;
}

interface SpeechRecognitionInstance extends EventTarget {
  continuous: boolean;
  interimResults: boolean;
  lang: string;
  start: () => void;
  stop: () => void;
  onresult:
    | ((this: SpeechRecognitionInstance, ev: SpeechRecognitionEvent) => void)
    | null;
  onend: ((this: SpeechRecognitionInstance, ev: Event) => void) | null;
  onerror:
    | ((
        this: SpeechRecognitionInstance,
        ev: SpeechRecognitionErrorEvent,
      ) => void)
    | null;
}

declare global {
  interface Window {
    SpeechRecognition?: new () => SpeechRecognitionInstance;
    webkitSpeechRecognition?: new () => SpeechRecognitionInstance;
  }
}

export function useVoice() {
  const [isRecording, setIsRecording] = useState(false);
  const [isProcessing, setIsProcessing] = useState(false);
  const [isAutoMode, setIsAutoMode] = useState(false);
  const [isListeningWakeWord, setIsListeningWakeWord] = useState(false);
  const [isSpeaking, setIsSpeaking] = useState(false);

  const mediaRecorderRef = useRef<MediaRecorder | null>(null);
  const audioChunksRef = useRef<Blob[]>([]);
  const recognitionRef = useRef<SpeechRecognitionInstance | null>(null);
  const shouldListenRef = useRef(false);

  const startWakeWordListening = useCallback(() => {
    if (recognitionRef.current && !isListeningWakeWord) {
      try {
        recognitionRef.current.start();
        setIsListeningWakeWord(true);
      } catch {
        // Ignore "already started" error
      }
    }
  }, [isListeningWakeWord]);

  const stopWakeWordListening = useCallback(() => {
    if (recognitionRef.current && isListeningWakeWord) {
      try {
        recognitionRef.current.stop();
        setIsListeningWakeWord(false);
      } catch {
        // Ignore error
      }
    }
  }, [isListeningWakeWord]);

  const startRecording = useCallback(async () => {
    try {
      // Must definitely stop wake word listening before grabbing mic
      stopWakeWordListening();
      shouldListenRef.current = false;

      const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
      mediaRecorderRef.current = new MediaRecorder(stream, {
        mimeType: "audio/webm",
      });
      audioChunksRef.current = [];

      mediaRecorderRef.current.ondataavailable = (event) => {
        if (event.data.size > 0) {
          audioChunksRef.current.push(event.data);
        }
      };

      mediaRecorderRef.current.start();
      setIsRecording(true);
    } catch (err: unknown) {
      console.error("Error accessing microphone:", err);
      toast.error("Microphone access denied or unavailable.");
      // Fallback if mic permission denied
    }
  }, [stopWakeWordListening]);

  // Initialize SpeechRecognition for Wake Word
  useEffect(() => {
    const SpeechRecognition =
      window.SpeechRecognition || window.webkitSpeechRecognition;
    if (SpeechRecognition) {
      const recognition = new SpeechRecognition();
      recognition.continuous = true;
      recognition.interimResults = true;
      recognition.lang = "en-US";

      recognition.onresult = (event: SpeechRecognitionEvent) => {
        const current = event.resultIndex;
        const transcript =
          event.results[current]?.[0]?.transcript.toLowerCase() || "";

        if (
          transcript.includes("jarvis") ||
          transcript.includes("hey jarvis")
        ) {
          // console.log("Wake word detected!");
          // Stop wake word listening and start recording actual command
          startRecording();
        }
      };

      recognition.onend = () => {
        setIsListeningWakeWord(false);
        // Restart if auto mode is still desired
        if (shouldListenRef.current) {
          startWakeWordListening();
        }
      };

      recognition.onerror = (event: SpeechRecognitionErrorEvent) => {
        if (event.error === "not-allowed" || event.error === "audio-capture") {
          setIsAutoMode(false);
          shouldListenRef.current = false;
        }
      };

      recognitionRef.current = recognition;
    } else {
      console.warn("Speech Recognition API not supported in this browser.");
      toast.error("Wake word feature is not supported in this browser.");
    }

    return () => {
      shouldListenRef.current = false;
      if (recognitionRef.current) {
        recognitionRef.current.stop();
      }
    };
  }, [startRecording, startWakeWordListening]);

  // Sync ref with state block
  useEffect(() => {
    shouldListenRef.current =
      isAutoMode && !isRecording && !isProcessing && !isSpeaking;
    let timer: ReturnType<typeof setTimeout>;

    if (shouldListenRef.current && !isListeningWakeWord) {
      // Small delay to ensure mic is fully released by other components
      timer = setTimeout(startWakeWordListening, 500);
    } else if (!shouldListenRef.current && isListeningWakeWord) {
      stopWakeWordListening();
    }

    return () => clearTimeout(timer);
  }, [
    isAutoMode,
    isRecording,
    isProcessing,
    isSpeaking,
    isListeningWakeWord,
    startWakeWordListening,
    stopWakeWordListening,
  ]);

  const toggleAutoMode = useCallback(() => {
    setIsAutoMode((prev) => !prev);
  }, []);

  const stopRecording = useCallback(async (): Promise<string | null> => {
    return new Promise((resolve) => {
      if (!mediaRecorderRef.current) {
        resolve(null);
        return;
      }

      mediaRecorderRef.current.onstop = async () => {
        setIsRecording(false);
        setIsProcessing(true);

        const audioBlob = new Blob(audioChunksRef.current, {
          type: "audio/webm",
        });
        audioChunksRef.current = [];

        // Send to backend STT endpoint
        const formData = new FormData();
        formData.append("file", audioBlob, "recording.webm");

        try {
          const response = await fetch(
            `${import.meta.env.VITE_API_BASE_URL}/voice/transcribe`,
            {
              method: "POST",
              body: formData,
            },
          );

          if (!response.ok) {
            let errorMsg = `HTTP error! status: ${response.status}`;
            if (response.status === 429) {
                errorMsg = "Rate limit exceeded for transcription. Please wait a moment.";
            } else if (response.status >= 500) {
                errorMsg = "Server error during transcription.";
            }
            throw new Error(errorMsg);
          }

          const data = await response.json();
          setIsProcessing(false);
          resolve(data.text);
        } catch (error: unknown) {
          console.error("Transcription error:", error);
          const errorMessage = error instanceof Error ? error.message : "Failed to transcribe audio.";
          toast.error(errorMessage);
          setIsProcessing(false);
          resolve(null);
        }
      };

      mediaRecorderRef.current.stop();
      // Stop all tracks to release mic
      mediaRecorderRef.current.stream
        .getTracks()
        .forEach((track) => track.stop());
    });
  }, []);

  const playSynthesizedSpeech = useCallback((text: string) => {
    if (!text.trim()) return;

    setIsSpeaking(true);
    const audioUrl = `${import.meta.env.VITE_API_BASE_URL}/voice/synthesize`;

    fetch(audioUrl, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ text, voice: "en-US-ChristopherNeural" }),
    })
      .then((response) => response.blob())
      .then((blob) => {
        const url = URL.createObjectURL(blob);
        const audio = new Audio(url);

        audio.onplay = () => console.log("Playing JARVIS response...");
        audio.onended = () => {
          URL.revokeObjectURL(url);
          setIsSpeaking(false);
        };
        audio.onerror = () => setIsSpeaking(false);

        audio.play().catch((e) => {
          console.error("Audio playback prevented by browser:", e);
          toast.error("Browser blocked audio playback.");
          setIsSpeaking(false);
        });
      })
      .catch((err) => {
        console.error("TTS fetch error:", err);
        // Do not spam toast for network Abort, only for genuine bad fetch
        toast.error("Failed to fetch synthetic voice. Server may be down.");
        setIsSpeaking(false);
      });
  }, []);

  return {
    isRecording,
    isProcessing,
    isSpeaking,
    isAutoMode,
    isListeningWakeWord,
    toggleAutoMode,
    startRecording,
    stopRecording,
    playSynthesizedSpeech,
  };
}
