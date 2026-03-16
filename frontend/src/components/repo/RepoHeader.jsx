import { Loader2, CheckCircle2, XCircle, Clock, GitBranch, FileCode2, Cpu, Layers } from 'lucide-react'
import { useStore } from '../../store'
import clsx from 'clsx'

const STATUS_CONFIG = {
  ready:    { icon: CheckCircle2, label: 'Ready',    cls: 'badge-ready'    },
  indexing: { icon: Loader2,      label: 'Indexing', cls: 'badge-indexing' },
  pending:  { icon: Clock,        label: 'Pending',  cls: 'badge-pending'  },
  failed:   { icon: XCircle,      label: 'Failed',   cls: 'badge-failed'   },
}

export default function RepoHeader() {
  const { activeRepo } = useStore()
  if (!activeRepo) return null

  const cfg = STATUS_CONFIG[activeRepo.status] || STATUS_CONFIG.pending
  const Icon = cfg.icon

  return (
    <div className="px-4 py-2.5 border-b border-white/5 bg-surface-900 flex items-center gap-4 flex-wrap">
      <div className="flex items-center gap-2">
        <GitBranch size={13} className="text-slate-500" />
        <span className="text-sm font-medium text-slate-200">{activeRepo.name}</span>
        <span className={`badge ${cfg.cls} flex items-center gap-1`}>
          <Icon size={10} className={activeRepo.status === 'indexing' ? 'animate-spin' : ''} />
          {cfg.label}
        </span>
      </div>

      {activeRepo.status === 'ready' && (
        <div className="flex items-center gap-4 ml-auto text-xs text-slate-500">
          <span className="flex items-center gap-1.5">
            <FileCode2 size={11} /> {activeRepo.file_count} files
          </span>
          <span className="flex items-center gap-1.5">
            <Cpu size={11} /> {activeRepo.function_count} functions
          </span>
          <span className="flex items-center gap-1.5">
            <Layers size={11} /> {activeRepo.chunk_count} chunks
          </span>
        </div>
      )}

      {activeRepo.status === 'failed' && (
        <p className="text-xs text-red-400 ml-auto">{activeRepo.error}</p>
      )}
    </div>
  )
}
