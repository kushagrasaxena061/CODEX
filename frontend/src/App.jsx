import { useState } from 'react'
import axios from 'axios'
import { Terminal, FolderGit2, Play, Settings, Send } from 'lucide-react'

const API_BASE = "http://127.0.0.1:8000/api"

function App() {
  const [prompt, setPrompt] = useState("")
  const [messages, setMessages] = useState([
    { role: 'ai', text: 'Ready. What would you like to build?' }
  ])
  const [status, setStatus] = useState("idle")

  const handleSend = async () => {
    if (!prompt.trim()) return
    
    const userMsg = prompt
    setPrompt("")
    setMessages(prev => [...prev, { role: 'user', text: userMsg }])
    setStatus("working")

    try {
      const response = await axios.post(`${API_BASE}/chat`, { prompt: userMsg })
      setMessages(prev => [...prev, { role: 'ai', text: `System: ${response.data.message}` }])
      setStatus("idle")
    } catch (error) {
      setMessages(prev => [...prev, { role: 'ai', text: 'Error connecting to backend.' }])
      setStatus("error")
    }
  }

  return (
    <div className="flex h-screen overflow-hidden bg-[#1e1e1e] text-gray-300 font-sans">
      
      {/* LEFT SIDEBAR */}
      <div className="w-16 flex flex-col items-center py-4 bg-[#252526] border-r border-[#333]">
        <FolderGit2 className="w-6 h-6 mb-8 text-gray-400 hover:text-white cursor-pointer" />
        <Terminal className="w-6 h-6 mb-8 text-gray-400 hover:text-white cursor-pointer" />
        <Settings className="w-6 h-6 mt-auto text-gray-400 hover:text-white cursor-pointer" />
      </div>

      {/* MAIN CHAT AREA */}
      <div className="flex-1 flex flex-col border-r border-[#333]">
        <div className="h-12 border-b border-[#333] flex items-center px-4 bg-[#252526]">
          <span className="font-semibold">Project: Codex Foundation</span>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.map((msg, i) => (
            <div key={i} className={`flex ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`max-w-[80%] rounded p-3 ${
                msg.role === 'user' ? 'bg-[#0e639c] text-white' : 'bg-[#2d2d2d] border border-[#444]'
              }`}>
                {msg.text}
              </div>
            </div>
          ))}
        </div>

        <div className="p-4 bg-[#252526] border-t border-[#333]">
          <div className="flex items-center bg-[#3c3c3c] rounded border border-[#555] overflow-hidden p-1">
            <input
              type="text"
              value={prompt}
              onChange={(e) => setPrompt(e.target.value)}
              onKeyDown={(e) => e.key === 'Enter' && handleSend()}
              placeholder="Ask the AI to build or change something..."
              className="flex-1 bg-transparent px-3 py-2 outline-none text-white placeholder-gray-400"
            />
            <button 
              onClick={handleSend}
              className="p-2 text-gray-400 hover:text-white transition-colors"
            >
              <Send className="w-5 h-5" />
            </button>
          </div>
        </div>
      </div>

      {/* RIGHT AGENT/TERMINAL PANEL */}
      <div className="w-80 flex flex-col bg-[#1e1e1e]">
        <div className="h-12 border-b border-[#333] flex items-center px-4 bg-[#252526]">
          <span className="font-semibold flex items-center gap-2">
            <Play className={`w-4 h-4 ${status === 'working' ? 'text-green-500 animate-pulse' : 'text-gray-500'}`} />
            Agent Status: {status.toUpperCase()}
          </span>
        </div>
        <div className="flex-1 p-4 font-mono text-xs text-green-400 overflow-y-auto">
          {">"} Terminal output will appear here...
        </div>
      </div>
    </div>
  )
}

export default App
