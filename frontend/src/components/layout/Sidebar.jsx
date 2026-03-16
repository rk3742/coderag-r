import { useState } from 'react'
import { Code2, GitBranch, Plus, Trash2, Loader2, CheckCircle2, XCircle, Clock, Network, ChevronRight, Zap } from 'lucide-react'
import { useStore } from '../../store'
import { api } from '../../utils/api'
import AddRepoModal from '../repo/AddRepoModal'
import clsx from 'clsx'

const STATUS = {
  ready:    { icon: CheckCircle2, color: 'text-emerald-400', dot: 'bg-emerald-400' },
  indexing: { icon: Loader2,      color: 'text-amber-400',   dot: 'bg-amber-400', spin: true },
  pending:  { icon: Clock,        color: 'text-slate-500',   dot: 'bg-slate-500'  },
  failed:   { icon: XCircle,      color: 'text-rose-400',    dot: 'bg-rose-400'   },
}

export default function Sidebar() {
  const { repos, activeRepo, setActiveRepo, setRepos, setFileTree, toggleGraph, showGraph } = useStore()
  const [showAdd, setShowAdd] = useState(false)
  const [deleting, setDeleting] = useState(null)

  async function selectRepo(repo) {
    setActiveRepo(repo)
    if (repo.status === 'ready') {
      try { const tree = await api.getFileTree(repo.id); setFileTree(tree) } catch {}
    }
  }

  async function deleteRepo(e, id) {
    e.stopPropagation()
    setDeleting(id)
    try {
      await api.deleteRepo(id)
      setRepos(repos.filter(r => r.id !== id))
      if (activeRepo?.id === id) setActiveRepo(null)
    } catch {}
    setDeleting(null)
  }

  return (
    <>
      <aside className="w-60 h-screen flex flex-col flex-shrink-0 border-r" style={{background:'var(--surface-1)', borderColor:'var(--border)'}}>
        {/* Logo */}
        <div className="px-4 py-5 border-b" style={{borderColor:'var(--border)'}}>
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-xl flex items-center justify-center glow-violet" style={{background:'linear-gradient(135deg,#7c3aed,#4f46e5)'}}>
              <Code2 size={15} className="text-white" />
            </div>
            <div>
              <div className="font-bold text-sm text-white tracking-tight">CodeRAG<span className="text-violet-400">-R</span></div>
              <div className="text-xs" style={{color:'#4c4f7a'}}>Reasoning Copilot</div>
            </div>
          </div>
        </div>

        {/* Section header */}
        <div className="px-4 pt-5 pb-2 flex items-center justify-between">
          <span className="text-xs font-semibold tracking-widest uppercase" style={{color:'#4c4f7a'}}>Repos</span>
          <button onClick={() => setShowAdd(true)} className="w-6 h-6 rounded-lg flex items-center justify-center transition-all hover:scale-110" style={{background:'rgba(124,58,237,0.2)',color:'#a78bfa'}}>
            <Plus size={12} />
          </button>
        </div>

        {/* Repo list */}
        <div className="flex-1 overflow-y-auto px-3 space-y-1">
          {repos.length === 0 && (
            <div className="px-3 py-8 text-center">
              <div className="w-10 h-10 rounded-2xl mx-auto mb-3 flex items-center justify-center" style={{background:'rgba(124,58,237,0.1)'}}>
                <GitBranch size={18} style={{color:'#4c4f7a'}} />
              </div>
              <p className="text-xs" style={{color:'#4c4f7a'}}>No repos yet</p>
              <button onClick={() => setShowAdd(true)} className="mt-2 text-xs font-medium" style={{color:'#a78bfa'}}>
                Add your first →
              </button>
            </div>
          )}
          {repos.map(repo => {
            const cfg = STATUS[repo.status] || STATUS.pending
            const Icon = cfg.icon
            const isActive = activeRepo?.id === repo.id
            return (
              <div key={repo.id} onClick={() => selectRepo(repo)}
                className={clsx('sidebar-item group relative', isActive && 'active')}
              >
                <div className={`w-1.5 h-1.5 rounded-full flex-shrink-0 ${cfg.dot}`} />
                <span className="flex-1 truncate text-sm">{repo.name}</span>
                <div className="flex items-center gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
                  <button onClick={e => deleteRepo(e, repo.id)} className="p-1 rounded hover:text-rose-400 transition-colors" style={{color:'#475569'}}>
                    {deleting === repo.id ? <Loader2 size={11} className="animate-spin" /> : <Trash2 size={11} />}
                  </button>
                </div>
                {isActive && <ChevronRight size={12} style={{color:'#a78bfa'}} />}
              </div>
            )
          })}
        </div>

        {/* Graph toggle */}
        {activeRepo?.status === 'ready' && (
          <div className="px-3 pb-3 border-t pt-3" style={{borderColor:'var(--border)'}}>
            <button onClick={toggleGraph} className={clsx('sidebar-item w-full', showGraph && 'active')}>
              <Network size={14} />
              <span>Dependency graph</span>
            </button>
          </div>
        )}

        {/* Footer */}
        <div className="px-4 py-3 border-t" style={{borderColor:'var(--border)'}}>
          <div className="flex items-center gap-1.5">
            <Zap size={11} style={{color:'#4c4f7a'}} />
            <p className="text-xs" style={{color:'#4c4f7a'}}>Groq · Llama 3.3 70B · Free</p>
          </div>
        </div>
      </aside>
      {showAdd && <AddRepoModal onClose={() => setShowAdd(false)} />}
    </>
  )
}
