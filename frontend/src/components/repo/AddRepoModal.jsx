import { useState, useRef } from 'react'
import { X, Github, Upload, Loader2 } from 'lucide-react'
import { api } from '../../utils/api'
import { useStore } from '../../store'

export default function AddRepoModal({ onClose }) {
  const [tab, setTab] = useState('github')
  const [url, setUrl] = useState('')
  const [name, setName] = useState('')
  const [file, setFile] = useState(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState('')
  const { repos, setRepos } = useStore()
  const fileRef = useRef()

  async function submit(e) {
    e.preventDefault()
    setError('')
    setLoading(true)
    try {
      let repo
      if (tab === 'github') {
        if (!url.startsWith('https://github.com')) throw new Error('Enter a valid GitHub URL')
        repo = await api.addGithub(url, name || undefined)
      } else {
        if (!file) throw new Error('Select a .zip file')
        repo = await api.uploadZip(file, name || file.name.replace('.zip', ''))
      }
      setRepos([...repos, repo])
      onClose()
    } catch (err) {
      setError(err.message)
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="fixed inset-0 bg-black/60 backdrop-blur-sm flex items-center justify-center z-50 p-4 animate-fade-in">
      <div className="card w-full max-w-md p-6 animate-slide-up">
        <div className="flex items-center justify-between mb-5">
          <h2 className="font-semibold text-slate-100">Add repository</h2>
          <button onClick={onClose} className="btn-ghost p-1.5"><X size={16} /></button>
        </div>

        {/* Tabs */}
        <div className="flex gap-1 bg-surface-800 p-1 rounded-lg mb-5">
          {[['github', Github, 'GitHub URL'], ['zip', Upload, 'Upload ZIP']].map(([key, Icon, label]) => (
            <button
              key={key}
              onClick={() => setTab(key)}
              className={`flex-1 flex items-center justify-center gap-2 py-1.5 rounded-md text-sm transition-all ${
                tab === key ? 'bg-brand-500 text-white' : 'text-slate-400 hover:text-slate-200'
              }`}
            >
              <Icon size={14} />{label}
            </button>
          ))}
        </div>

        <form onSubmit={submit} className="space-y-4">
          {tab === 'github' ? (
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">GitHub URL</label>
              <input
                className="input"
                placeholder="https://github.com/username/repo"
                value={url}
                onChange={e => setUrl(e.target.value)}
                required
              />
            </div>
          ) : (
            <div>
              <label className="block text-xs text-slate-400 mb-1.5">ZIP file</label>
              <div
                onClick={() => fileRef.current?.click()}
                className="border-2 border-dashed border-white/10 rounded-lg p-6 text-center cursor-pointer hover:border-brand-500/40 transition-colors"
              >
                <Upload size={20} className="text-slate-500 mx-auto mb-2" />
                <p className="text-sm text-slate-400">
                  {file ? file.name : 'Click to select .zip file'}
                </p>
              </div>
              <input ref={fileRef} type="file" accept=".zip" className="hidden"
                onChange={e => setFile(e.target.files[0])} />
            </div>
          )}

          <div>
            <label className="block text-xs text-slate-400 mb-1.5">Name (optional)</label>
            <input
              className="input"
              placeholder="my-project"
              value={name}
              onChange={e => setName(e.target.value)}
            />
          </div>

          {error && (
            <div className="bg-red-500/10 border border-red-500/20 rounded-lg px-3 py-2 text-sm text-red-400">
              {error}
            </div>
          )}

          <div className="flex gap-3 pt-1">
            <button type="button" onClick={onClose} className="btn-ghost flex-1 justify-center py-2">
              Cancel
            </button>
            <button type="submit" disabled={loading} className="btn-primary flex-1 justify-center">
              {loading ? <><Loader2 size={14} className="animate-spin" /> Indexing...</> : 'Add repo'}
            </button>
          </div>
        </form>
      </div>
    </div>
  )
}
