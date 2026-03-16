import { useState, useRef, useEffect } from 'react'
import { Send, GitBranch, Network, Search, Sparkles, ChevronDown } from 'lucide-react'
import { useStore } from '../../store'
import clsx from 'clsx'

const MODES = [
  { id:'auto',   label:'Auto',   Icon:Sparkles,  desc:'LLM picks best mode',     color:'#a78bfa', bg:'rgba(124,58,237,0.15)'  },
  { id:'tree',   label:'Tree',   Icon:GitBranch, desc:'Navigate AST structure',  color:'#34d399', bg:'rgba(16,185,129,0.15)'  },
  { id:'graph',  label:'Graph',  Icon:Network,   desc:'Follow call chains',      color:'#fbbf24', bg:'rgba(245,158,11,0.15)'  },
  { id:'vector', label:'Vector', Icon:Search,    desc:'Semantic similarity',     color:'#a78bfa', bg:'rgba(124,58,237,0.15)'  },
]

const SUGGESTIONS = [
  'How is authentication handled?',
  'Trace the full booking flow',
  'Where is the database configured?',
  'What calls the main controller?',
  'Find all JWT token usage',
]

export default function ChatInput({ onSend }) {
  const [text, setText] = useState('')
  const [showModes, setShowModes] = useState(false)
  const { queryMode, setQueryMode, isStreaming, activeRepo } = useStore()
  const textRef = useRef()
  const modeRef = useRef()
  const currentMode = MODES.find(m => m.id === queryMode) || MODES[0]

  useEffect(() => {
    const handler = e => { if (!modeRef.current?.contains(e.target)) setShowModes(false) }
    document.addEventListener('mousedown', handler)
    return () => document.removeEventListener('mousedown', handler)
  }, [])

  function submit() {
    if (!text.trim() || isStreaming || !activeRepo) return
    onSend(text.trim())
    setText('')
    textRef.current?.focus()
  }

  const disabled = !activeRepo || activeRepo.status !== 'ready' || isStreaming

  return (
    <div className="border-t p-4 space-y-3" style={{background:'var(--surface-1)', borderColor:'var(--border)'}}>
      {/* Suggestion chips */}
      <div className="flex gap-2 overflow-x-auto pb-1" style={{scrollbarWidth:'none'}}>
        {SUGGESTIONS.map((s, i) => (
          <button key={i} onClick={() => { setText(s); textRef.current?.focus() }} disabled={disabled}
            className="flex-shrink-0 text-xs px-3 py-1.5 rounded-full border transition-all hover:border-violet-500/40 disabled:opacity-30"
            style={{background:'var(--surface-3)', borderColor:'var(--border)', color:'#64748b', whiteSpace:'nowrap'}}
          >
            {s}
          </button>
        ))}
      </div>

      {/* Input row */}
      <div className="flex gap-2 items-end">
        {/* Mode pill */}
        <div ref={modeRef} className="relative flex-shrink-0">
          <button onClick={() => setShowModes(v => !v)} disabled={disabled}
            className="flex items-center gap-2 px-3 py-2.5 rounded-xl border transition-all disabled:opacity-40"
            style={{background: currentMode.bg, borderColor: currentMode.color + '40', color: currentMode.color}}
          >
            <currentMode.Icon size={13} />
            <span className="text-xs font-semibold hidden sm:inline">{currentMode.label}</span>
            <ChevronDown size={11} style={{color:'inherit', opacity:0.6}} />
          </button>

          {showModes && (
            <div className="absolute bottom-full mb-2 left-0 rounded-2xl border p-1.5 w-56 shadow-2xl z-50 animate-slide-up"
              style={{background:'var(--surface-2)', borderColor:'var(--border)', boxShadow:'0 20px 60px rgba(0,0,0,0.5)'}}>
              {MODES.map(m => (
                <button key={m.id} onClick={() => { setQueryMode(m.id); setShowModes(false) }}
                  className="w-full flex items-center gap-3 px-3 py-2.5 rounded-xl transition-all text-left"
                  style={{background: queryMode === m.id ? m.bg : 'transparent'}}
                >
                  <div className="w-7 h-7 rounded-lg flex items-center justify-center flex-shrink-0" style={{background: m.bg}}>
                    <m.Icon size={13} style={{color: m.color}} />
                  </div>
                  <div>
                    <div className="text-xs font-semibold" style={{color: m.color}}>{m.label}</div>
                    <div className="text-xs" style={{color:'#475569'}}>{m.desc}</div>
                  </div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Textarea */}
        <div className="flex-1 relative">
          <textarea ref={textRef} value={text}
            onChange={e => setText(e.target.value)}
            onKeyDown={e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); submit() } }}
            disabled={disabled} rows={1}
            placeholder={
              !activeRepo ? 'Select a repository first...' :
              activeRepo.status !== 'ready' ? 'Indexing in progress...' :
              'Ask anything about the codebase...'
            }
            className="input resize-none py-2.5 pr-12 leading-relaxed"
            style={{minHeight:'44px', maxHeight:'128px', fontFamily:"'Space Grotesk', sans-serif"}}
            onInput={e => { e.target.style.height = 'auto'; e.target.style.height = Math.min(e.target.scrollHeight, 128) + 'px' }}
          />
          <button onClick={submit} disabled={disabled || !text.trim()}
            className="absolute right-2 bottom-2 w-8 h-8 rounded-xl flex items-center justify-center transition-all active:scale-90"
            style={{background: (!disabled && text.trim()) ? 'linear-gradient(135deg,#7c3aed,#4f46e5)' : 'var(--surface-3)', boxShadow: (!disabled && text.trim()) ? '0 4px 15px rgba(124,58,237,0.4)' : 'none'}}
          >
            <Send size={13} className="text-white" style={{opacity: (!disabled && text.trim()) ? 1 : 0.3}} />
          </button>
        </div>
      </div>
    </div>
  )
}
