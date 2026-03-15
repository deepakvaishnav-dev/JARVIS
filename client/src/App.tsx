import ChatPanel from "./components/ChatPanel";
import { Settings, Mic, LayoutDashboard } from "lucide-react";
import { Toaster } from "react-hot-toast";
import jarvisPic from "./assets/jarvis.png";

function App() {
  return (
    <div className="flex h-screen w-full bg-[#0f172a] overflow-hidden font-sans text-slate-200">
      {/* Sidebar - Simulated Navigation */}
      <div className="w-20 lg:w-64 border-r border-slate-800 bg-[#0f172a]/80 backdrop-blur-xl flex flex-col pt-6 z-10">
        <div className="flex items-center gap-3 px-6 mb-12">
          <div className="shrink-0 relative">
            <div className="absolute inset-0 bg-sky-500/20 blur-md rounded-full"></div>
            <img
              src={jarvisPic}
              alt="JARVIS Core"
              className="w-10 h-10 object-contain jarvis-glow rounded-full"
            />
          </div>
          <h1 className="text-xl font-bold bg-clip-text text-transparent bg-linear-gradient-to-r from-sky-400 to-emerald-400 hidden lg:block uppercase tracking-wider">
            JARVIS OS
          </h1>
        </div>

        <nav className="flex-1 px-4 space-y-2">
          <NavItem
            icon={<LayoutDashboard size={22} />}
            label="Workspace"
            active
          />
          <NavItem icon={<Mic size={22} />} label="Voice Control" />
          <NavItem icon={<Settings size={22} />} label="Settings" />
        </nav>
      </div>

      {/* Main Content */}
      <main className="flex-1 relative bg-linear-gradient-to-b from-[#0f172a] to-[#020617] flex flex-col">
        {/* Top bar */}
        <header className="h-16 border-b border-slate-800/80 w-full flex items-center px-6 justify-between shrink-0">
          <div className="text-sm font-medium text-slate-400">
            Current Module:{" "}
            <span className="text-sky-400 ml-2">Core Chat Interface</span>
          </div>
        </header>

        {/* Chat Area */}
        <div className="flex-1 overflow-hidden">
          <ChatPanel />
        </div>
      </main>
      
      {/* Global Toast Notifications */}
      <Toaster 
        position="top-right"
        toastOptions={{
          style: {
            background: '#1e293b',
            color: '#e2e8f0',
            border: '1px solid #334155'
          }
        }}
      />
    </div>
  );
}

function NavItem({
  icon,
  label,
  active = false,
}: {
  icon: React.ReactNode;
  label: string;
  active?: boolean;
}) {
  return (
    <button
      className={`w-full flex items-center gap-3 px-4 py-3 rounded-xl transition-all ${active ? "bg-sky-500/10 text-sky-400 border border-sky-500/20" : "text-slate-400 hover:bg-slate-800/50 hover:text-slate-200"}`}
    >
      <div className={`${active ? "jarvis-glow" : ""}`}>{icon}</div>
      <span className="hidden lg:block font-medium">{label}</span>
    </button>
  );
}

export default App;
