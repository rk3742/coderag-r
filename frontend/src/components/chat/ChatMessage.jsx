import ReactMarkdown from 'react-markdown'
import remarkGfm from 'remark-gfm'
import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { nightOwl } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { FileCode2, Cpu, User, GitBranch, Network, Search, Sparkles, Shield, AlertTriangle, XCircle } from 'lucide-react'
import clsx from 'clsx'

const MODE_META = {
  tree:   { label: 'Tree reasoning',  Icon: GitBranch, cls: 'badge-tree',   glow: 'rgba(16,185,129,0.2)',  line: '#10b981' },
  graph:  { label: 'Graph traversal', Icon: Network,   cls: 'badge-graph',  glow: 'rgba(245,158,11,0.2)',  line: '#f59e0b' },
  vector: { label: 'Vector search',   Icon: Search,    cls: 'badge-vector', glow: 'rgba(124,58,237,0.2)',  line: '#7c3aed' },
  'graph-seed':     { label: 'Graph seed',     Icon: Network, cls: 'badge-graph',  glow: 'rgba(245,158,11,0.2)',  line: '#f59e0b' },
  'graph-expanded': { label: 'Graph expanded', Icon: Network, cls: 'badge-graph',  glow: 'rgba(245,158,11,0.2)',  line: '#f59e0b' },
}

const CONFIDENCE_META = {
  high:   { Icon: Shield,        cls: 'badge-high',   label: 'High confidence'   },
  medium: { Icon: AlertTriangle, cls: 'badge-medium', label: 'Medium confidence' },
  low:    { Icon: AlertTriangle, cls: 'badge-low',    label: 'Low confidence'    },
  none:   { Icon: XCircle,       cls: 'badge-none',   label: 'No match found'    },
}

function CitationCard({ c, index }) {
  const score = Math.round((c.relevance_score || 0) * 100)
  const hue = score > 60 ? '#34d399' : score > 35 ? '#fbbf24' : '#fb7185'
  return (
    <div className="rounded-xl overflow-hidden border transition-all hover:border-violet-500/30 hover:shadow-lg" style={{background:'var(--surface-3)', borderColor:'var(--border)', boxShadow: 'none'}}>
      {/* Top stripe */}
      <div className="h-0.5" style={{background:`linear-gradient(90deg, ${hue}, transparent)`}} />
      <div className="p-3">
        <div className="flex items-start justify-between gap-2 mb-2">
          <div className="flex items-center gap-1.5 min-w-0">
            <FileCode2 size={11} style={{color:'#a78bfa', flexShrink:0}} />
            <span className="text-xs truncate font-mono" style={{color:'#94a3b8'}}>{c.file}</span>
          </div>
          <div className="text-xs font-bold flex-shrink-0" style={{color: hue}}>{score}%</div>
        </div>
        <div className="text-xs font-mono mb-2" style={{color:'#64748b'}}>
          {c.function_name} · L{c.start_line}–{c.end_line}
        </div>
        <pre className="text-xs font-mono rounded-lg p-2 overflow-x-auto line-clamp-3" style={{background:'var(--surface-0)', color:'#94a3b8', fontSize:'11px'}}>
          {c.snippet}
        </pre>
      </div>
    </div>
  )
}

export default function ChatMessage({ msg }) {
  if (msg.role === 'user') {
    return (
      <div className="flex gap-3 justify-end animate-slide-up">
        <div className="max-w-2xl">
          <div className="rounded-2xl rounded-tr-sm px-4 py-3" style={{background:'linear-gradient(135deg, rgba(124,58,237,0.25), rgba(79,70,229,0.25))', border:'1px solid rgba(124,58,237,0.3)'}}>
            <p className="text-sm" style={{color:'#e2e8f0', lineHeight:1.6}}>{msg.content}</p>
          </div>
        </div>
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{background:'rgba(124,58,237,0.2)', border:'1px solid rgba(124,58,237,0.3)'}}>
          <User size={14} style={{color:'#a78bfa'}} />
        </div>
      </div>
    )
  }

  if (msg.role === 'assistant') {
    const modeMeta = MODE_META[msg.mode]
    const confMeta = CONFIDENCE_META[msg.confidenceLevel]

    return (
      <div className="flex gap-3 animate-slide-up">
        {/* Avatar */}
        <div className="flex-shrink-0">
          <div className="w-8 h-8 rounded-full flex items-center justify-center glow-violet" style={{background:'linear-gradient(135deg,#7c3aed,#4f46e5)', border:'1px solid rgba(167,139,250,0.4)'}}>
            <Cpu size={14} className="text-white" />
          </div>
        </div>

        <div className="flex-1 min-w-0 space-y-3">
          {/* Meta row */}
          <div className="flex items-center gap-2 flex-wrap">
            {modeMeta && (
              <span className={`badge ${modeMeta.cls} flex items-center gap-1`}>
                <modeMeta.Icon size={10} />
                {modeMeta.label}
              </span>
            )}
            {confMeta && (
              <span className={`badge ${confMeta.cls} flex items-center gap-1`}>
                <confMeta.Icon size={10} />
                {confMeta.label}
              </span>
            )}
            {msg.reason && (
              <span className="text-xs italic truncate max-w-xs" style={{color:'#475569'}}>{msg.reason}</span>
            )}
          </div>

          {/* Typing indicator */}
          {msg.streaming && !msg.content && (
            <div className="flex gap-1.5 py-2 px-1">
              <div className="typing-dot" />
              <div className="typing-dot" />
              <div className="typing-dot" />
            </div>
          )}

          {/* Answer */}
          {msg.content && (
            <div className="prose-code text-sm">
              <ReactMarkdown
                remarkPlugins={[remarkGfm]}
                components={{
                  code({ node, inline, className, children, ...props }) {
                    const match = /language-(\w+)/.exec(className || '')
                    return !inline && match ? (
                      <SyntaxHighlighter style={nightOwl} language={match[1]} PreTag="div"
                        customStyle={{ margin:'10px 0', borderRadius:'12px', fontSize:'12px', background:'#0d0f1e', border:'1px solid rgba(255,255,255,0.06)' }}
                        {...props}
                      >
                        {String(children).replace(/\n$/, '')}
                      </SyntaxHighlighter>
                    ) : (
                      <code className="font-mono text-xs px-1.5 py-0.5 rounded" style={{background:'rgba(124,58,237,0.15)', color:'#a78bfa', border:'1px solid rgba(124,58,237,0.2)'}} {...props}>
                        {children}
                      </code>
                    )
                  },
                }}
              >
                {msg.content}
              </ReactMarkdown>
            </div>
          )}

          {/* Citations */}
          {msg.citations?.length > 0 && (
            <div>
              <div className="flex items-center gap-2 mb-2">
                <div className="h-px flex-1" style={{background:'linear-gradient(90deg, rgba(124,58,237,0.4), transparent)'}} />
                <span className="text-xs font-medium" style={{color:'#4c4f7a'}}>
                  {msg.citations.length} sources · {msg.chunksRetrieved} chunks
                </span>
                <div className="h-px flex-1" style={{background:'linear-gradient(90deg, transparent, rgba(124,58,237,0.4))'}} />
              </div>
              <div className="grid grid-cols-1 gap-2 sm:grid-cols-2">
                {msg.citations.map((c, i) => <CitationCard key={i} c={c} index={i} />)}
              </div>
            </div>
          )}
        </div>
      </div>
    )
  }

  if (msg.role === 'error') {
    return (
      <div className="flex gap-3 animate-slide-up">
        <div className="w-8 h-8 rounded-full flex items-center justify-center flex-shrink-0 mt-0.5" style={{background:'rgba(244,63,94,0.15)', border:'1px solid rgba(244,63,94,0.3)'}}>
          <Cpu size={14} style={{color:'#fb7185'}} />
        </div>
        <div className="rounded-xl px-4 py-3" style={{background:'rgba(244,63,94,0.08)', border:'1px solid rgba(244,63,94,0.2)'}}>
          <p className="text-sm" style={{color:'#fb7185'}}>{msg.content}</p>
        </div>
      </div>
    )
  }
  return null
}
