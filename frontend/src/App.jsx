import { useEffect, useState } from 'react'
import { MessageSquare, FileCode2, BarChart3 } from 'lucide-react'
import Sidebar from './components/layout/Sidebar'
import FileTree from './components/repo/FileTree'
import GraphPanel from './components/graph/GraphPanel'
import ChatPage from './pages/ChatPage'
import FileViewPage from './pages/FileViewPage'
import BenchmarkPage from './pages/BenchmarkPage'
import { useStore } from './store'
import { api } from './utils/api'
import { useAllRepoPoll } from './hooks/useRepoPoll'
import clsx from 'clsx'

const TABS = [
  { id: 'chat',      Icon: MessageSquare, label: 'Ask'       },
  { id: 'file',      Icon: FileCode2,     label: 'File'      },
  { id: 'benchmark', Icon: BarChart3,     label: 'Benchmark' },
]

export default function App() {
  const { setRepos, activeFile, showGraph } = useStore()
  const [tab, setTab] = useState('chat')
  useAllRepoPoll()

  useEffect(() => { if (activeFile) setTab('file') }, [activeFile])
  useEffect(() => { api.listRepos().then(setRepos).catch(() => {}) }, [])

  return (
    <div className="flex h-screen overflow-hidden" style={{background:'var(--surface-0)'}}>
      <Sidebar />

      {/* File tree */}
      <div className="w-52 h-screen flex-shrink-0 border-r overflow-hidden" style={{background:'var(--surface-1)', borderColor:'var(--border)'}}>
        <FileTree />
      </div>

      {/* Main area */}
      <div className="flex-1 flex flex-col min-w-0 h-screen overflow-hidden" style={{background:'var(--surface-0)'}}>
        {/* Tab bar */}
        <div className="flex items-center gap-1 px-3 py-2 border-b" style={{background:'var(--surface-1)', borderColor:'var(--border)'}}>
          {TABS.map(({ id, Icon, label }) => {
            const isActive = tab === id
            const displayLabel = id === 'file' && activeFile ? activeFile.name : label
            return (
              <button key={id} onClick={() => setTab(id)}
                className="flex items-center gap-1.5 px-3 py-1.5 rounded-lg text-xs font-medium transition-all"
                style={isActive
                  ? {background:'rgba(124,58,237,0.15)', color:'#a78bfa', border:'1px solid rgba(124,58,237,0.25)'}
                  : {color:'#475569', border:'1px solid transparent'}
                }
              >
                <Icon size={12} />
                <span className={id === 'file' ? 'max-w-24 truncate' : ''}>{displayLabel}</span>
              </button>
            )
          })}
        </div>

        {/* Pages */}
        <div className="flex-1 overflow-hidden">
          <div className={clsx('h-full', tab !== 'chat'      && 'hidden')}><ChatPage /></div>
          <div className={clsx('h-full', tab !== 'file'      && 'hidden')}><FileViewPage /></div>
          <div className={clsx('h-full', tab !== 'benchmark' && 'hidden')}><BenchmarkPage /></div>
        </div>
      </div>

      {/* Graph panel */}
      {showGraph && (
        <div className="w-96 flex-shrink-0 h-screen overflow-hidden animate-slide-up border-l" style={{borderColor:'var(--border)'}}>
          <GraphPanel />
        </div>
      )}
    </div>
  )
}
