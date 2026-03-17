import { useState, useRef, useEffect } from "react";
import { Send, User, Mic, Radio, Globe, Paperclip, Loader2, X } from "lucide-react";
import { useWebSocket } from "../../hooks/useWebSocket";
import { useVoice } from "../../hooks/useVoice";
import ReactMarkdown from "react-markdown";
import remarkGfm from "remark-gfm";
import jarvisPic from "../../assets/jarvis.png";

export default function ChatPanel() {
  const [input, setInput] = useState("");
  const [language, setLanguage] = useState<"en" | "hi">("en");
  const [attachedFiles, setAttachedFiles] = useState<{name: string, id: string}[]>([]);
  const [isUploading, setIsUploading] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const {
    isRecording,
    isProcessing,
    isSpeaking,
    isAutoMode,
    isListeningWakeWord,
    toggleAutoMode,
    startRecording,
    stopRecording,
    playSynthesizedSpeech,
  } = useVoice(language);
  const { messages, isConnected, isGenerating, sendMessage } = useWebSocket(
    `${import.meta.env.VITE_WS_BASE_URL}/chat/stream`,
    playSynthesizedSpeech,
  );
  const messagesEndRef = useRef<HTMLDivElement>(null);

  // Auto-scroll to bottom
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (
      input.trim() &&
      !isGenerating &&
      isConnected &&
      !isRecording &&
      !isProcessing &&
      !isSpeaking
    ) {
      sendMessage(input, false, language, attachedFiles.map(f => f.id));
      setInput("");
      setAttachedFiles([]);
    }
  };

  const handleFileUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (!file) return;
    
    setIsUploading(true);
    const formData = new FormData();
    formData.append("file", file);
    
    try {
      const response = await fetch(`${import.meta.env.VITE_WS_BASE_URL.replace("ws://", "http://").replace("/chat/stream", "/upload")}`, {
        method: "POST",
        body: formData,
      });
      
      const data = await response.json();
      if (data.file_id) {
        setAttachedFiles(prev => [...prev, { name: data.filename, id: data.file_id }]);
      }
    } catch (error) {
      console.error("Upload failed", error);
      // Fallback relative path for deployed/CORS proxy usage
      try {
        const responseFall = await fetch("/api/v1/upload", {
          method: "POST",
          body: formData,
        });
        const dataFall = await responseFall.json();
        if (dataFall.file_id) {
          setAttachedFiles(prev => [...prev, { name: dataFall.filename, id: dataFall.file_id }]);
        }
      } catch (err2) {
         console.error("Upload fallback failed", err2);
      }
    } finally {
      setIsUploading(false);
      // Reset input
      if (fileInputRef.current) {
         fileInputRef.current.value = "";
      }
    }
  };

  const toggleRecording = async () => {
    if (isRecording) {
      const transcribedText = await stopRecording();
      if (transcribedText) {
        sendMessage(transcribedText, true, language);
      }
    } else {
      startRecording();
    }
  };

  return (
    <div className="flex flex-col h-full pl-4 pr-4 pb-4">
      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto w-full max-w-4xl mx-auto space-y-6 pt-6 pb-20 no-scrollbar relative min-h-0">
        {messages.length > 0 && (
          <div className="absolute inset-0 pointer-events-none flex items-center justify-center opacity-[0.05] z-0">
            <img
              src={jarvisPic}
              alt=""
              className="w-[500px] h-[500px] object-contain"
            />
          </div>
        )}

        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full text-slate-500">
            <div className="relative mb-8">
              <div className="absolute inset-0 bg-sky-500/20 blur-[80px] rounded-full"></div>
              <img
                src={jarvisPic}
                alt="JARVIS Core"
                className={`w-64 h-64 object-contain rounded-full transition-all duration-1000 ${
                  isListeningWakeWord || isRecording
                    ? "animate-pulse scale-110 jarvis-glow"
                    : "opacity-80"
                }`}
              />
            </div>
            <p className="text-xl font-light tracking-[0.2em] text-sky-400/80 mb-2">
              J . A . R . V . I . S .
            </p>
            <p className="text-sm tracking-widest opacity-50 uppercase">
              {isRecording
                ? language === "hi" ? "निर्देश रिकॉर्ड हो रहा है..." : "Recording Directive..."
                : isListeningWakeWord
                  ? language === "hi" ? "वेक वर्ड की प्रतीक्षा..." : "Awaiting Wake Word..."
                  : language === "hi" ? "सिस्टम ऑनलाइन" : "System Online"}
            </p>
          </div>
        ) : (
          messages.map((msg, i) => (
            <div
              key={i}
              className={`flex items-start gap-4 p-4 rounded-xl ${
                msg.role === "model"
                  ? "bg-slate-800/60 border border-slate-700/50"
                  : "bg-transparent"
              }`}
            >
              <div
                className={`flex items-center justify-center shrink-0 w-10 h-10 ${
                  msg.role === "model"
                    ? ""
                    : "p-2 rounded-lg bg-slate-700 text-slate-300"
                } relative z-10`}
              >
                {msg.role === "model" ? (
                  <img
                    src={jarvisPic}
                    className="w-10 h-10 object-contain rounded-full"
                    alt="JARVIS"
                  />
                ) : (
                  <User size={20} />
                )}
              </div>
              <div className="flex-1 overflow-hidden relative z-10">
                <p className="text-sm font-medium mb-1 text-slate-400">
                  {msg.role === "model" ? "JARVIS" : "USER"}
                </p>
                <div className="text-slate-200 leading-relaxed prose prose-invert prose-p:leading-relaxed prose-pre:bg-slate-900 prose-pre:border prose-pre:border-slate-700 prose-sky max-w-none">
                  <ReactMarkdown remarkPlugins={[remarkGfm]}>
                    {msg.content}
                  </ReactMarkdown>
                </div>
              </div>
            </div>
          ))
        )}
        <div ref={messagesEndRef} />
      </div>

      {/* Input Area */}
      <div className="max-w-4xl w-full mx-auto relative bottom-0">
        <form
          onSubmit={handleSubmit}
          className="relative flex flex-col gap-2"
        >
          {attachedFiles.length > 0 && (
            <div className="flex flex-wrap gap-2 px-2 pb-1">
              {attachedFiles.map((file, idx) => (
                <div key={idx} className="flex items-center gap-2 bg-slate-800 border border-slate-700 rounded-lg px-3 py-1.5 text-xs text-sky-400">
                  <Paperclip size={12} />
                  <span className="truncate max-w-[150px]">{file.name}</span>
                  <button 
                    type="button" 
                    onClick={() => setAttachedFiles(prev => prev.filter((_, i) => i !== idx))}
                    className="hover:text-red-400 transition-colors ml-1"
                  >
                    <X size={14} />
                  </button>
                </div>
              ))}
            </div>
          )}
          
          <div className="relative flex items-center gap-2">
          
          <input 
            type="file" 
            ref={fileInputRef} 
            onChange={handleFileUpload}
            className="hidden" 
          />
          
          <button
            type="button"
            onClick={() => fileInputRef.current?.click()}
            disabled={!isConnected || isUploading}
            className={`p-4 rounded-2xl transition-all shadow-lg shrink-0 ${
              isUploading ? "opacity-50 cursor-wait bg-slate-800 text-slate-400" : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-sky-400 hover:border-sky-500/50"
            }`}
             title="Attach File"
          >
            {isUploading ? <Loader2 size={24} className="animate-spin" /> : <Paperclip size={24} />}
          </button>
          <button
            type="button"
            onClick={() => setLanguage((prev) => (prev === "en" ? "hi" : "en"))}
            className={`p-4 rounded-2xl transition-all shadow-lg shrink-0 bg-slate-800 text-slate-400 border border-slate-700 hover:text-sky-400 hover:border-sky-500/50`}
            title={language === "en" ? "Switch to Hindi" : "अंग्रेजी में बदलें"}
          >
            <div className="relative">
              <Globe size={24} />
              <span className="absolute -bottom-1 -right-2 text-[10px] font-bold bg-slate-900 px-1 rounded-md text-sky-400">
                {language.toUpperCase()}
              </span>
            </div>
          </button>

          <button
            type="button"
            onClick={toggleAutoMode}
            disabled={!isConnected}
            className={`p-4 rounded-2xl transition-all shadow-lg shrink-0 ${
              isAutoMode
                ? "bg-sky-500/20 text-sky-400 border border-sky-500/50"
                : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-sky-400 hover:border-sky-500/50"
            } disabled:opacity-50`}
            title={
              isAutoMode
                ? "Disable Auto Mode"
                : "Enable Auto Mode (Say 'JARVIS')"
            }
          >
            <Radio
              size={24}
              className={isListeningWakeWord ? "animate-pulse" : ""}
            />
          </button>

          <button
            type="button"
            onClick={toggleRecording}
            disabled={
              !isConnected || isGenerating || isProcessing || isSpeaking
            }
            className={`p-4 rounded-2xl transition-all shadow-lg shrink-0 ${
              isRecording
                ? "bg-red-500/20 text-red-500 border border-red-500/50 animate-pulse"
                : "bg-slate-800 text-slate-400 border border-slate-700 hover:text-sky-400 hover:border-sky-500/50"
            } disabled:opacity-50`}
            title={isRecording ? "Stop Recording" : "Speak to JARVIS"}
          >
            <Mic size={24} />
          </button>

          <div className="relative flex-1">
            <input
              type="text"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              disabled={
                !isConnected ||
                isGenerating ||
                isRecording ||
                isProcessing ||
                isSpeaking
              }
              placeholder={
                !isConnected
                  ? language === "hi" ? "जार्विस कोर से जुड़ रहा है..." : "Connecting to JARVIS Core..."
                  : isSpeaking
                    ? language === "hi" ? "जार्विस बोल रहा है..." : "JARVIS is speaking..."
                    : isProcessing
                      ? language === "hi" ? "ऑडियो ट्रांसक्राइब हो रहा है..." : "Transcribing audio..."
                      : isRecording
                        ? language === "hi" ? "सुन रहा हूँ..." : "Listening..."
                        : isListeningWakeWord
                          ? language === "hi" ? "'JARVIS' का इंतज़ार..." : "Waiting for 'JARVIS'..."
                          : language === "hi" ? "अपना कमांड टाइप करें..." : "Type your command..."
              }
              className="w-full bg-slate-800 border border-slate-700 rounded-2xl pl-6 pr-16 py-4 text-slate-200 placeholder-slate-500 focus:outline-none focus:ring-2 focus:ring-sky-500 focus:border-transparent transition-all disabled:opacity-50"
            />
            <button
              type="submit"
              disabled={
                !input.trim() ||
                !isConnected ||
                isGenerating ||
                isRecording ||
                isProcessing ||
                isSpeaking
              }
              className="absolute right-2 top-2 p-2 text-sky-400 hover:text-sky-300 hover:bg-slate-700 rounded-xl disabled:opacity-50 disabled:hover:bg-transparent transition-all"
            >
              <Send size={20} />
            </button>
          </div>
          </div>
        </form>
        <div className="flex justify-between items-center mt-2 px-2 text-xs text-slate-500">
          <div className="flex items-center gap-2">
            <div
              className={`w-2 h-2 rounded-full ${isConnected ? "bg-emerald-500 jarvis-glow" : "bg-red-500"}`}
            />
            {isConnected ? "Core Connected" : "Offline"}
          </div>
          <div>JARVIS OS v2.0</div>
        </div>
      </div>
    </div>
  );
}
