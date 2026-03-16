import { Prism as SyntaxHighlighter } from 'react-syntax-highlighter'
import { oneDark } from 'react-syntax-highlighter/dist/esm/styles/prism'
import { useStore } from '../store'
import { FileCode2 } from 'lucide-react'

const EXT_LANG = {
  py: 'python', js: 'javascript', ts: 'typescript',
  jsx: 'jsx', tsx: 'tsx', json: 'json',
  md: 'markdown', css: 'css', html: 'html',
}

export default function FileViewPage() {
  const { activeFile, activeFileContent } = useStore()

  if (!activeFile || !activeFileContent) return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center">
        <FileCode2 size={24} className="text-slate-600 mx-auto mb-2" />
        <p className="text-sm text-slate-600">Select a file from the tree</p>
      </div>
    </div>
  )

  const ext = activeFile.name.split('.').pop() || ''
  const lang = EXT_LANG[ext] || 'text'

  return (
    <div className="h-full flex flex-col">
      <div className="px-4 py-2.5 border-b border-white/5 bg-surface-900 flex items-center gap-2">
        <FileCode2 size={13} className="text-brand-400" />
        <span className="text-xs font-mono text-slate-300">{activeFile.path}</span>
      </div>
      <div className="flex-1 overflow-auto">
        <SyntaxHighlighter
          language={lang}
          style={oneDark}
          showLineNumbers
          customStyle={{
            margin: 0, borderRadius: 0,
            background: '#0c0e16',
            fontSize: '12px',
            minHeight: '100%',
          }}
          lineNumberStyle={{ color: '#3d4560', minWidth: '3em' }}
        >
          {activeFileContent}
        </SyntaxHighlighter>
      </div>
    </div>
  )
}
