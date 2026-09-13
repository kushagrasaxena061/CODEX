import { useState, useRef, useEffect } from 'react';

function App() {
  const [prompt, setPrompt] = useState('');
  const [chat, setChat] = useState([{role: 'system', content: 'Ready. Upload a workspace (ZIP) or ask me to build something new.'}]);
  const [status, setStatus] = useState('IDLE');
  const [terminal, setTerminal] = useState('> Terminal output will appear here...');
  const fileInputRef = useRef(null);
  const chatEndRef = useRef(null);

  useEffect(() => {
    chatEndRef.current?.scrollIntoView({ behavior: "smooth" });
  }, [chat]);

  const handleUpload = async (e) => {
    const file = e.target.files[0];
    if (!file) return;
    setStatus('UPLOADING...');
    setTerminal('> Uploading to isolated workspace...');
    
    const formData = new FormData();
    formData.append('file', file);
    
    try {
      const res = await fetch('http://localhost:8000/api/workspace/upload', {
        method: 'POST',
        body: formData
      });
      const data = await res.json();
      setTerminal(`> ${data.message}`);
      setChat(prev => [...prev, {role: 'system', content: 'Workspace uploaded and memory reset safely.'}]);
    } catch (error) {
      setTerminal(`> Upload failed: ${error.message}`);
    }
    setStatus('IDLE');
  };

  const handleDownload = () => {
    window.open('http://localhost:8000/api/workspace/download', '_blank');
  };

  const sendPrompt = async () => {
    if (!prompt.trim()) return;
    const userMsg = prompt;
    setPrompt('');
    setChat(prev => [...prev, {role: 'user', content: userMsg}]);
    setStatus('WORKING...');
    setTerminal('> Architect is planning tasks for agents...\n');

    try {
      const res = await fetch('http://localhost:8000/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: userMsg})
      });
      const data = await res.json();
      
      setChat(prev => [...prev, {role: 'system', content: data.message || 'Task complete.'}]);
      
      if (data.data && data.data.terminal_logs && data.data.terminal_logs.length > 0) {
        setTerminal(data.data.terminal_logs.join('\n\n'));
      } else {
        setTerminal('> Task completed with no terminal output.');
      }
    } catch (e) {
      setChat(prev => [...prev, {role: 'system', content: 'Error connecting to backend.'}]);
      setTerminal(`> Error: ${e.message}`);
    }
    setStatus('IDLE');
  };

  return (
    <div className="flex h-screen bg-[#050505] text-[#ececf1] font-sans antialiased overflow-hidden selection:bg-indigo-500/30">
      <style>{`
        ::-webkit-scrollbar { width: 6px; height: 6px; }
        ::-webkit-scrollbar-track { background: transparent; }
        ::-webkit-scrollbar-thumb { background: #333333; border-radius: 10px; }
        ::-webkit-scrollbar-thumb:hover { background: #444444; }
      `}</style>

      {/* Main Canvas Area */}
      <div className="flex-1 flex flex-col relative z-10 bg-gradient-to-b from-[#0a0a0c] to-[#050505]">
        
        {/* Sleek Header */}
        <header className="px-6 py-4 flex justify-between items-center z-20 absolute top-0 w-full">
          <div className="flex items-center gap-2">
            <div className="w-6 h-6 rounded bg-gradient-to-br from-indigo-500 to-purple-600 flex items-center justify-center shadow-lg shadow-indigo-500/20">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="white" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><polyline points="4 14 10 14 10 20"/><polyline points="20 10 14 10 14 4"/><line x1="14" y1="10" x2="21" y2="3"/><line x1="3" y1="21" x2="10" y2="14"/></svg>
            </div>
            <span className="font-semibold tracking-wide text-sm text-gray-200">CODEX</span>
          </div>
          <div className="flex gap-2">
            <input type="file" ref={fileInputRef} onChange={handleUpload} accept=".zip" className="hidden" />
            <button onClick={() => fileInputRef.current.click()} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium text-gray-400 hover:text-white hover:bg-white/5 border border-transparent hover:border-white/10 transition-all duration-200">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="17 8 12 3 7 8"/><line x1="12" y1="3" x2="12" y2="15"/></svg>
              Upload Workspace
            </button>
            <button onClick={handleDownload} className="flex items-center gap-1.5 px-3 py-1.5 rounded-md text-xs font-medium bg-[#ececf1] text-black hover:bg-white transition-all duration-200 shadow-sm">
              <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4"/><polyline points="7 10 12 15 17 10"/><line x1="12" y1="15" x2="12" y2="3"/></svg>
              Export
            </button>
          </div>
        </header>

        {/* Chat History Canvas */}
        <div className="flex-1 overflow-y-auto px-4 md:px-12 pt-24 pb-40 flex flex-col gap-8 w-full max-w-4xl mx-auto">
          {chat.map((msg, i) => (
            <div key={i} className={`flex w-full ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
              <div className={`relative max-w-[85%] text-[15px] leading-relaxed ${
                msg.role === 'user'
                  ? 'bg-[#2f2f32] text-white px-5 py-3 rounded-2xl rounded-tr-sm shadow-md'
                  : 'text-gray-300'
              }`}>
                {msg.role === 'system' && (
                  <div className="flex items-center gap-2 mb-1.5">
                    <div className="w-5 h-5 rounded-full bg-indigo-500/10 border border-indigo-500/20 flex items-center justify-center">
                      <svg width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="#818cf8" strokeWidth="2"><path d="M12 2v20M17 5H9.5a3.5 3.5 0 0 0 0 7h5a3.5 3.5 0 0 1 0 7H6"/></svg>
                    </div>
                    <span className="text-xs font-medium text-gray-500 uppercase tracking-wider">Codex Agent</span>
                  </div>
                )}
                <div className={msg.role === 'system' ? 'pl-7' : ''}>
                  {msg.content}
                </div>
              </div>
            </div>
          ))}
          <div ref={chatEndRef} />
        </div>

        {/* Floating Command Palette */}
        <div className="absolute bottom-8 left-0 w-full flex justify-center px-4 z-30 pointer-events-none">
          <div className="w-full max-w-3xl relative pointer-events-auto">
            <div className="absolute -inset-1 bg-gradient-to-r from-indigo-500/20 to-purple-500/20 rounded-2xl blur-lg opacity-50"></div>
            <div className="relative flex items-end bg-[#171719]/90 backdrop-blur-xl border border-white/10 rounded-2xl shadow-2xl focus-within:border-indigo-500/50 focus-within:bg-[#1c1c1e] transition-all duration-300">
              <textarea
                value={prompt}
                onChange={e => setPrompt(e.target.value)}
                onKeyDown={e => {
                  if (e.key === 'Enter' && !e.shiftKey) {
                    e.preventDefault();
                    sendPrompt();
                  }
                }}
                className="flex-1 bg-transparent p-4 text-[15px] text-gray-200 placeholder-gray-500 outline-none resize-none min-h-[56px] max-h-48 overflow-y-auto"
                placeholder="Ask Codex to build, edit, or debug..."
                disabled={status !== 'IDLE'}
                rows={1}
              />
              <div className="p-2.5">
                <button 
                  onClick={sendPrompt} 
                  disabled={status !== 'IDLE' || !prompt.trim()} 
                  className={`p-2 rounded-xl transition-all duration-200 flex items-center justify-center ${
                    status === 'IDLE' && prompt.trim() 
                    ? 'bg-white text-black hover:bg-gray-200 shadow-sm' 
                    : 'bg-white/5 text-gray-500 cursor-not-allowed'
                  }`}
                >
                  {status === 'WORKING...' ? (
                    <svg className="animate-spin" width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2"><path d="M21 12a9 9 0 1 1-6.219-8.56"/></svg>
                  ) : (
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2.5" strokeLinecap="round" strokeLinejoin="round"><line x1="12" y1="19" x2="12" y2="5"/><polyline points="5 12 12 5 19 12"/></svg>
                  )}
                </button>
              </div>
            </div>
            <div className="text-center mt-3 text-[11px] text-gray-500 font-medium">
              Codex can write code, run terminal commands, and manage your workspace.
            </div>
          </div>
        </div>
      </div>

      {/* Modern IDE Terminal Panel */}
      <div className="w-[420px] bg-[#0c0c0c] border-l border-white/5 flex flex-col shadow-2xl z-20 shrink-0">
        {/* Terminal Header */}
        <div className="h-14 px-4 border-b border-white/5 flex items-center justify-between bg-[#080808]">
          <div className="flex items-center gap-3">
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="#6b7280" strokeWidth="2"><polyline points="4 17 10 11 4 5"/><line x1="12" y1="19" x2="20" y2="19"/></svg>
            <span className="text-xs font-medium text-gray-400 uppercase tracking-wider">Output Console</span>
          </div>
          <div className="flex items-center gap-2">
            <div className={`w-2 h-2 rounded-full ${status === 'IDLE' ? 'bg-[#333]' : 'bg-indigo-500 animate-pulse shadow-[0_0_8px_rgba(99,102,241,0.8)]'}`}></div>
            <span className="text-[10px] font-bold text-gray-500 uppercase tracking-widest">{status}</span>
          </div>
        </div>
        
        {/* Terminal Output */}
        <div className="flex-1 p-5 overflow-y-auto bg-[#0a0a0a]">
          <pre className="font-mono text-[12px] text-[#d4d4d4] leading-relaxed whitespace-pre-wrap break-words">
            {terminal.split('\n').map((line, idx) => {
              // Add subtle syntax coloring for terminal lines
              let colorClass = "text-[#d4d4d4]"; // default IDE gray
              if (line.startsWith('>')) colorClass = "text-indigo-400 font-medium";
              else if (line.includes('error') || line.includes('Error') || line.includes('FAILED')) colorClass = "text-red-400";
              else if (line.includes('SUCCESS') || line.includes('VERIFIED')) colorClass = "text-emerald-400";
              else if (line.startsWith('$')) colorClass = "text-yellow-200/80";
              
              return (
                <div key={idx} className={`${colorClass} mb-0.5`}>
                  {line}
                </div>
              );
            })}
          </pre>
        </div>
      </div>
    </div>
  );
}
export default App;
