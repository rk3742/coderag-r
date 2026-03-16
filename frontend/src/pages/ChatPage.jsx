import { useEffect, useRef } from 'react'
import { Code2, Sparkles, GitBranch, Network, Search, Zap } from 'lucide-react'
import ChatMessage from '../components/chat/ChatMessage'
import ChatInput from '../components/chat/ChatInput'
import RepoHeader from '../components/repo/RepoHeader'
import { useStore } from '../store'
import { api } from '../utils/api'

export default function ChatPage() {
  const { activeRepo, messages, addMessage, updateLastMessage, setStreaming, isStreaming, queryMode } = useStore()
  const bottomRef = useRef()
  const contentRef = useRef('')

  useEffect(() => { bottomRef.current?.scrollIntoView({ behavior: 'smooth' }) }, [messages])

  function handleSend(question) {
    if (!activeRepo || isStreaming) return
    contentRef.current = ''
    addMessage({ role: 'user', content: question, id: Date.now() })
    addMessage({ role: 'assistant', content: '', streaming: true, citations: [], mode: null, reason: '', chunksRetrieved: 0, confidenceLevel: null, confidenceScore: null, id: Date.now() + 1 })
    setStreaming(true)

    api.streamQuery(activeRepo.id, question, queryMode, 8, (event) => {
      switch (event.type) {
        case 'route':
          updateLastMessage({ mode: event.mode, reason: event.reason })
          break
        case 'confidence':
          updateLastMessage({ confidenceLevel: event.level, confidenceScore: event.score, confidenceMessage: event.message })
          break
        case 'citations':
          updateLastMessage({ citations: event.citations, chunksRetrieved: event.chunks_retrieved })
          break
        case 'token':
          contentRef.current += event.content
          updateLastMessage({ content: contentRef.current })
          break
        case 'done':
          updateLastMessage({ streaming: false })
          setStreaming(false)
          contentRef.current = ''
          break
        case 'error':
          updateLastMessage({ role: 'error', content: event.content, streaming: false })
          setStreaming(false)
          contentRef.current = ''
          break
      }
    })
  }

  return (
    <div className="flex flex-col h-full">
      <RepoHeader />
      <div className="flex-1 overflow-y-auto">
        {messages.length === 0 ? (
          <EmptyState repo={activeRepo} />
        ) : (
          <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">
            {messages.map(msg => <ChatMessage key={msg.id} msg={msg} />)}
            <div ref={bottomRef} />
          </div>
        )}
      </div>
      <ChatInput onSend={handleSend} />
    </div>
  )
}

function EmptyState({ repo }) {
  if (!repo) return (
    <div className="h-full flex flex-col items-center justify-center p-8 text-center">
      <div className="animate-float mb-6">
        <div className="w-16 h-16 rounded-2xl flex items-center justify-center glow-violet mx-auto" style={{background:'linear-gradient(135deg,#7c3aed,#4f46e5)'}}>
          <Code2 size={28} className="text-white" />
        </div>
      </div>
      <h2 className="text-2xl font-bold mb-2" style={{background:'linear-gradient(135deg,#a78bfa,#67e8f9)', WebkitBackgroundClip:'text', WebkitTextFillColor:'transparent'}}>CodeRAG-R</h2>
      <p className="text-sm mb-1" style={{color:'#94a3b8'}}>Reasoning Codebase Copilot</p>
      <p className="text-xs max-w-xs" style={{color:'#475569'}}>Add a repository from the sidebar to start asking questions about any codebase.</p>
      <div className="mt-8 flex gap-3 flex-wrap justify-center">
        {[['Tree', GitBranch, '#34d399', 'rgba(16,185,129,0.1)'], ['Graph', Network, '#fbbf24', 'rgba(245,158,11,0.1)'], ['Vector', Search, '#a78bfa', 'rgba(124,58,237,0.1)']].map(([label, Icon, color, bg]) => (
          <div key={label} className="flex items-center gap-2 px-4 py-2 rounded-xl border text-xs font-medium" style={{background:bg, borderColor:color+'30', color}}>
            <Icon size={12} /> {label} retrieval
          </div>
        ))}
      </div>
    </div>
  )

  if (repo.status !== 'ready') return (
    <div className="h-full flex flex-col items-center justify-center p-8 text-center">
      <div className="relative mb-6">
        <div className="w-14 h-14 rounded-2xl flex items-center justify-center" style={{background:'rgba(124,58,237,0.1)', border:'1px solid rgba(124,58,237,0.2)'}}>
          <div className="w-6 h-6 border-2 rounded-full animate-spin" style={{borderColor:'rgba(124,58,237,0.2)', borderTopColor:'#7c3aed'}} />
        </div>
        <div className="absolute -inset-2 rounded-2xl animate-ping" style={{background:'rgba(124,58,237,0.05)'}} />
      </div>
      <p className="text-sm font-semibold text-white mb-1">Indexing {repo.name}...</p>
      <p className="text-xs" style={{color:'#475569'}}>Parsing AST · Building graph · Embedding chunks</p>
    </div>
  )

  const SAMPLE_QS = [
    'How is authentication handled?', 'Trace the full request-response flow',
    'Where is the database connection configured?', 'What would break if I changed the auth module?',
  ]

  return (
    <div className="h-full flex flex-col items-center justify-center p-8 text-center">
      <div className="w-14 h-14 rounded-2xl flex items-center justify-center mb-4 glow-violet" style={{background:'linear-gradient(135deg,#7c3aed,#4f46e5)'}}>
        <Sparkles size={22} className="text-white" />
      </div>
      <h2 className="text-base font-bold text-white mb-1">{repo.name} is ready</h2>
      <p className="text-xs mb-6" style={{color:'#475569'}}>{repo.file_count} files · {repo.function_count} functions · {repo.chunk_count} chunks</p>
      <div className="grid grid-cols-1 gap-2 max-w-sm w-full">
        {SAMPLE_QS.map((q, i) => (
          <button key={i} className="text-left text-xs px-4 py-3 rounded-xl border transition-all hover:border-violet-500/30 group"
            style={{background:'var(--surface-3)', borderColor:'var(--border)', color:'#94a3b8'}}
            onClick={() => {
              const el = document.querySelector('textarea')
              if (el) { Object.getOwnPropertyDescriptor(window.HTMLTextAreaElement.prototype, 'value').set.call(el, q); el.dispatchEvent(new Event('input', { bubbles: true })) }
            }}
          >
            <span className="group-hover:text-violet-300 transition-colors">{q}</span>
          </button>
        ))}
      </div>
    </div>
  )
}
