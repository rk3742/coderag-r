import { useState } from 'react'
import { ChevronRight, ChevronDown, FileCode2, FolderOpen, Folder } from 'lucide-react'
import { useStore } from '../../store'
import { api } from '../../utils/api'
import clsx from 'clsx'

const LANG_COLORS = {
  python: 'text-blue-400', javascript: 'text-yellow-400',
  typescript: 'text-blue-300', react: 'text-cyan-400',
  'react-ts': 'text-cyan-300', json: 'text-slate-400',
  markdown: 'text-slate-500', css: 'text-pink-400', html: 'text-orange-400',
}

function FileNode({ node, depth = 0 }) {
  const [open, setOpen] = useState(depth < 2)
  const { activeRepo, activeFile, setActiveFile } = useStore()

  async function handleClick() {
    if (node.type === 'directory') { setOpen(o => !o); return }
    try {
      const res = await api.getFileContent(activeRepo.id, node.path)
      setActiveFile(node, res.content)
    } catch {}
  }

  const isActive = activeFile?.path === node.path
  const color = LANG_COLORS[node.language] || 'text-slate-400'

  if (node.type === 'directory') {
    return (
      <div>
        <div
          onClick={handleClick}
          className="flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer hover:bg-white/5 text-slate-400 hover:text-slate-200 transition-colors"
          style={{ paddingLeft: `${depth * 12 + 8}px` }}
        >
          {open ? <ChevronDown size={12} /> : <ChevronRight size={12} />}
          {open ? <FolderOpen size={13} className="text-amber-400/70" /> : <Folder size={13} className="text-amber-400/70" />}
          <span className="text-xs truncate">{node.name}</span>
        </div>
        {open && node.children?.map((child, i) => (
          <FileNode key={i} node={child} depth={depth + 1} />
        ))}
      </div>
    )
  }

  return (
    <div
      onClick={handleClick}
      className={clsx(
        'flex items-center gap-1.5 px-2 py-1 rounded cursor-pointer transition-colors text-xs',
        isActive ? 'bg-brand-500/15 text-brand-300' : 'text-slate-500 hover:text-slate-300 hover:bg-white/4'
      )}
      style={{ paddingLeft: `${depth * 12 + 20}px` }}
    >
      <FileCode2 size={12} className={color} />
      <span className="truncate">{node.name}</span>
    </div>
  )
}

export default function FileTree() {
  const { fileTree, activeRepo } = useStore()

  if (!activeRepo) return (
    <div className="h-full flex items-center justify-center p-6 text-center">
      <p className="text-xs text-slate-600">Select a repository</p>
    </div>
  )

  if (activeRepo.status !== 'ready') return (
    <div className="h-full flex items-center justify-center p-6 text-center">
      <div>
        <div className="w-6 h-6 border-2 border-brand-500/40 border-t-brand-500 rounded-full animate-spin mx-auto mb-3" />
        <p className="text-xs text-slate-500">Indexing repository...</p>
        <p className="text-xs text-slate-600 mt-1">{activeRepo.status}</p>
      </div>
    </div>
  )

  if (!fileTree) return (
    <div className="h-full flex items-center justify-center">
      <div className="w-4 h-4 border-2 border-brand-500/40 border-t-brand-500 rounded-full animate-spin" />
    </div>
  )

  return (
    <div className="h-full flex flex-col">
      <div className="px-3 py-2.5 border-b border-white/5">
        <p className="text-xs font-medium text-slate-400 truncate">{activeRepo.name}</p>
        <div className="flex gap-2 mt-1 flex-wrap">
          {activeRepo.languages?.map(l => (
            <span key={l} className={`text-xs ${LANG_COLORS[l] || 'text-slate-500'}`}>{l}</span>
          ))}
        </div>
      </div>
      <div className="flex-1 overflow-y-auto py-2">
        {fileTree.children?.map((node, i) => (
          <FileNode key={i} node={node} depth={0} />
        ))}
      </div>
      <div className="px-3 py-2 border-t border-white/5 text-xs text-slate-600">
        {activeRepo.file_count} files · {activeRepo.function_count} functions
      </div>
    </div>
  )
}
