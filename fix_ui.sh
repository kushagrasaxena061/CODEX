#!/bin/bash

echo "=========================================="
echo " PHASE 26: WIRING THE FRONTEND UI         "
echo "=========================================="

cat << 'INNER_EOF' > frontend/src/App.jsx
import { useState } from 'react';

function App() {
  const [prompt, setPrompt] = useState('');
  const [chat, setChat] = useState([{role: 'system', content: 'Ready. What would you like to build?'}]);
  const [status, setStatus] = useState('IDLE');
  const [terminal, setTerminal] = useState('> Terminal output will appear here...');

  const sendPrompt = async () => {
    if (!prompt) return;
    const userMsg = prompt;
    setPrompt('');
    setChat(prev => [...prev, {role: 'user', content: userMsg}]);
    setStatus('WORKING...');
    setTerminal('> Executing task...\n> Planning...\n> Coding...\n');

    try {
      const res = await fetch('http://127.0.0.1:8000/api/chat', {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({prompt: userMsg})
      });
      const data = await res.json();
      
      setChat(prev => [...prev, {role: 'system', content: data.message || 'Task complete.'}]);
      
      if (data.data && data.data.terminal_logs && data.data.terminal_logs.length > 0) {
        setTerminal(data.data.terminal_logs.join('\n\n'));
      } else if (data.data && data.data.files_changed) {
        setTerminal(`> Files Modified:\n${data.data.files_changed.join('\n')}\n\n> No terminal output.`);
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
    <div className="flex h-screen bg-[#1e1e1e] text-white font-sans">
      <div className="flex-1 flex flex-col border-r border-[#333]">
        <div className="p-4 border-b border-[#333] bg-[#252526] font-bold">Project: Codex Foundation</div>
        <div className="flex-1 p-4 overflow-y-auto flex flex-col gap-4">
          {chat.map((msg, i) => (
            <div key={i} className={`p-3 rounded max-w-[80%] ${msg.role === 'user' ? 'bg-[#0e639c] self-end' : 'bg-[#333] self-start'}`}>
              {msg.content}
            </div>
          ))}
        </div>
        <div className="p-4 bg-[#252526]">
          <div className="flex bg-[#3c3c3c] rounded border border-[#555] overflow-hidden">
            <input 
              type="text" 
              value={prompt} 
              onChange={e => setPrompt(e.target.value)}
              onKeyDown={e => e.key === 'Enter' && sendPrompt()}
              className="flex-1 bg-transparent p-3 outline-none"
              placeholder="Ask the AI to build or change something..."
              disabled={status !== 'IDLE'}
            />
            <button onClick={sendPrompt} className="p-4 hover:bg-[#555] font-bold" disabled={status !== 'IDLE'}>SEND</button>
          </div>
        </div>
      </div>
      <div className="w-1/3 flex flex-col bg-[#1e1e1e]">
        <div className="p-4 border-b border-[#333] bg-[#252526] text-sm text-gray-400 font-bold">Agent Status: {status}</div>
        <div className="flex-1 p-4 overflow-y-auto text-[#4af626] font-mono text-sm whitespace-pre-wrap">
          {terminal}
        </div>
      </div>
    </div>
  );
}
export default App;
INNER_EOF

echo "UI Fixed! Run ./launch_codex.sh again to see the terminal output live in the browser."
