import { useState, useEffect } from 'react'
import { BarChart3, Play, Loader2, CheckCircle2, XCircle, GitBranch, Network, Search, Zap, Trophy, Clock } from 'lucide-react'
import { useStore } from '../store'
import { api } from '../utils/api'

const MODE_META = {
  tree:   { label: 'Tree',   Icon: GitBranch, color: '#34d399', bg: 'rgba(16,185,129,0.1)'  },
  graph:  { label: 'Graph',  Icon: Network,   color: '#fbbf24', bg: 'rgba(245,158,11,0.1)'  },
  vector: { label: 'Vector', Icon: Search,    color: '#a78bfa', bg: 'rgba(124,58,237,0.1)'  },
}

const TYPE_COLORS = {
  architecture: '#67e8f9',
  dependency:   '#fbbf24',
  search:       '#a78bfa',
  general:      '#94a3b8',
}

function ScoreBar({ score, color }) {
  return (
    <div className="flex items-center gap-2">
      <div className="flex-1 rounded-full overflow-hidden" style={{background:'rgba(255,255,255,0.06)', height:6}}>
        <div className="h-full rounded-full transition-all duration-700" style={{width:`${Math.round(score * 100)}%`, background: color}} />
      </div>
      <span className="text-xs font-mono font-bold w-8 text-right" style={{color}}>{Math.round(score * 100)}%</span>
    </div>
  )
}

function ModeCard({ mode, results }) {
  if (!results || results.length === 0) return null
  const meta = MODE_META[mode]
  const avgScore = results.reduce((s, r) => s + r.overall_score, 0) / results.length
  const passRate = results.filter(r => r.passed).length / results.length
  const avgTime  = results.reduce((s, r) => s + r.response_time_ms, 0) / results.length

  return (
    <div className="rounded-2xl border p-5 transition-all hover:border-opacity-60" style={{background:'var(--surface-2)', borderColor: meta.color + '30'}}>
      {/* Header */}
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2.5">
          <div className="w-9 h-9 rounded-xl flex items-center justify-center" style={{background: meta.bg}}>
            <meta.Icon size={16} style={{color: meta.color}} />
          </div>
          <div>
            <div className="font-bold text-sm text-white">{meta.label} mode</div>
            <div className="text-xs" style={{color:'#475569'}}>{results.length} questions</div>
          </div>
        </div>
        <div className="text-right">
          <div className="text-2xl font-bold" style={{color: meta.color}}>{Math.round(avgScore * 100)}%</div>
          <div className="text-xs" style={{color:'#475569'}}>avg score</div>
        </div>
      </div>

      {/* Stats row */}
      <div className="grid grid-cols-2 gap-3 mb-4">
        <div className="rounded-xl p-3" style={{background:'var(--surface-3)'}}>
          <div className="text-xs mb-1" style={{color:'#475569'}}>Pass rate</div>
          <div className="font-bold text-sm" style={{color: passRate > 0.6 ? '#34d399' : passRate > 0.4 ? '#fbbf24' : '#fb7185'}}>{Math.round(passRate * 100)}%</div>
        </div>
        <div className="rounded-xl p-3" style={{background:'var(--surface-3)'}}>
          <div className="text-xs mb-1" style={{color:'#475569'}}>Avg time</div>
          <div className="font-bold text-sm text-white">{Math.round(avgTime / 1000)}s</div>
        </div>
      </div>

      {/* Score bar */}
      <ScoreBar score={avgScore} color={meta.color} />
    </div>
  )
}

function QuestionRow({ result }) {
  const modeMeta = MODE_META[result.forced_mode]
  const typeColor = TYPE_COLORS[result.question_type] || '#94a3b8'

  return (
    <div className="flex items-center gap-3 py-3 border-b" style={{borderColor:'var(--border)'}}>
      <div className="flex-shrink-0">
        {result.passed
          ? <CheckCircle2 size={14} style={{color:'#34d399'}} />
          : <XCircle size={14} style={{color:'#fb7185'}} />
        }
      </div>
      <div className="flex-1 min-w-0">
        <div className="text-xs text-white truncate">{result.question}</div>
        <div className="flex items-center gap-2 mt-1">
          <span className="text-xs px-2 py-0.5 rounded-full" style={{background: typeColor + '15', color: typeColor}}>{result.question_type}</span>
          {modeMeta && (
            <span className="text-xs px-2 py-0.5 rounded-full flex items-center gap-1" style={{background: modeMeta.bg, color: modeMeta.color}}>
              <modeMeta.Icon size={9} />{modeMeta.label}
            </span>
          )}
        </div>
      </div>
      <div className="flex-shrink-0 text-right">
        <div className="text-xs font-bold" style={{color: result.overall_score > 0.6 ? '#34d399' : result.overall_score > 0.35 ? '#fbbf24' : '#fb7185'}}>
          {Math.round(result.overall_score * 100)}%
        </div>
        <div className="text-xs" style={{color:'#475569'}}>{Math.round(result.response_time_ms / 1000)}s</div>
      </div>
    </div>
  )
}

export default function BenchmarkPage() {
  const { activeRepo } = useStore()
  const [running, setRunning] = useState(false)
  const [results, setResults] = useState(null)
  const [error, setError] = useState('')
  const [filterMode, setFilterMode] = useState('all')

  useEffect(() => {
    if (activeRepo?.id) loadResults()
  }, [activeRepo?.id])

  async function loadResults() {
    try {
      const data = await fetch(`/api/eval/results/${activeRepo.id}`).then(r => r.json())
      if (data.results) setResults(data)
    } catch {}
  }

  async function runBenchmark() {
    if (!activeRepo) return
    setRunning(true)
    setError('')
    try {
      await fetch('/api/eval/run', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ repo_id: activeRepo.id, modes: ['tree', 'graph', 'vector'] }),
      })
      // Poll for results every 10s
      const poll = setInterval(async () => {
        try {
          const data = await fetch(`/api/eval/results/${activeRepo.id}`).then(r => r.json())
          if (data.results && data.results.length > 0) {
            setResults(data)
            setRunning(false)
            clearInterval(poll)
          }
        } catch {}
      }, 10000)
      // Stop polling after 10 minutes
      setTimeout(() => { clearInterval(poll); setRunning(false) }, 600000)
    } catch (e) {
      setError(e.message)
      setRunning(false)
    }
  }

  if (!activeRepo) return (
    <div className="h-full flex items-center justify-center">
      <div className="text-center">
        <BarChart3 size={32} className="mx-auto mb-3" style={{color:'#4c4f7a'}} />
        <p className="text-sm" style={{color:'#475569'}}>Select a repository to run benchmarks</p>
      </div>
    </div>
  )

  // Group results by mode
  const byMode = results ? results.results.reduce((acc, r) => {
    acc[r.forced_mode] = acc[r.forced_mode] || []
    acc[r.forced_mode].push(r)
    return acc
  }, {}) : {}

  // Find best mode per question type
  const byType = results ? results.results.reduce((acc, r) => {
    if (!acc[r.question_type]) acc[r.question_type] = {}
    if (!acc[r.question_type][r.forced_mode]) acc[r.question_type][r.forced_mode] = []
    acc[r.question_type][r.forced_mode].push(r.overall_score)
    return acc
  }, {}) : {}

  const filteredResults = results?.results.filter(r => filterMode === 'all' || r.forced_mode === filterMode) || []

  return (
    <div className="h-full overflow-y-auto">
      <div className="max-w-4xl mx-auto px-6 py-6 space-y-6">

        {/* Header */}
        <div className="flex items-center justify-between">
          <div>
            <h1 className="text-lg font-bold text-white flex items-center gap-2">
              <BarChart3 size={18} style={{color:'#a78bfa'}} />
              Benchmark results
            </h1>
            <p className="text-xs mt-1" style={{color:'#475569'}}>
              {activeRepo.name} — compares Tree vs Graph vs Vector retrieval across 15 questions
            </p>
          </div>
          <button onClick={runBenchmark} disabled={running || activeRepo.status !== 'ready'} className="btn-primary">
            {running ? <><Loader2 size={14} className="animate-spin" />Running...</> : <><Play size={14} />Run benchmark</>}
          </button>
        </div>

        {error && (
          <div className="rounded-xl px-4 py-3 text-sm" style={{background:'rgba(244,63,94,0.08)', border:'1px solid rgba(244,63,94,0.2)', color:'#fb7185'}}>
            {error}
          </div>
        )}

        {running && (
          <div className="rounded-2xl border p-6 text-center" style={{background:'var(--surface-2)', borderColor:'rgba(124,58,237,0.2)'}}>
            <div className="w-10 h-10 border-2 rounded-full animate-spin mx-auto mb-3" style={{borderColor:'rgba(124,58,237,0.2)', borderTopColor:'#7c3aed'}} />
            <p className="text-sm font-medium text-white">Benchmark running...</p>
            <p className="text-xs mt-1" style={{color:'#475569'}}>Testing 15 questions × 3 modes = 45 queries. Takes ~5 minutes.</p>
            <p className="text-xs mt-1" style={{color:'#475569'}}>Check your VS Code terminal for live progress.</p>
          </div>
        )}

        {results && !running && (
          <>
            {/* Mode cards */}
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-3">
              {['tree', 'graph', 'vector'].map(mode => (
                <ModeCard key={mode} mode={mode} results={byMode[mode]} />
              ))}
            </div>

            {/* Best mode per question type */}
            {Object.keys(byType).length > 0 && (
              <div className="rounded-2xl border p-5" style={{background:'var(--surface-2)', borderColor:'var(--border)'}}>
                <div className="flex items-center gap-2 mb-4">
                  <Trophy size={15} style={{color:'#fbbf24'}} />
                  <h2 className="text-sm font-bold text-white">Best mode per question type</h2>
                </div>
                <div className="space-y-3">
                  {Object.entries(byType).map(([type, modeScores]) => {
                    const typeColor = TYPE_COLORS[type] || '#94a3b8'
                    const modeAvgs = Object.entries(modeScores).map(([m, scores]) => ({
                      mode: m, avg: scores.reduce((a, b) => a + b, 0) / scores.length
                    }))
                    const best = modeAvgs.sort((a, b) => b.avg - a.avg)[0]
                    const bestMeta = MODE_META[best?.mode]
                    return (
                      <div key={type} className="flex items-center gap-3">
                        <span className="text-xs font-medium w-24 flex-shrink-0" style={{color: typeColor}}>{type}</span>
                        <div className="flex-1 flex gap-2">
                          {modeAvgs.map(({ mode, avg }) => {
                            const m = MODE_META[mode]
                            return m ? (
                              <div key={mode} className="flex items-center gap-1.5 flex-1">
                                <div className="text-xs w-12" style={{color: m.color}}>{m.label}</div>
                                <ScoreBar score={avg} color={m.color} />
                              </div>
                            ) : null
                          })}
                        </div>
                        {bestMeta && (
                          <div className="flex items-center gap-1.5 px-3 py-1 rounded-full flex-shrink-0" style={{background: bestMeta.bg}}>
                            <Trophy size={10} style={{color: bestMeta.color}} />
                            <span className="text-xs font-bold" style={{color: bestMeta.color}}>{bestMeta.label} wins</span>
                          </div>
                        )}
                      </div>
                    )
                  })}
                </div>
              </div>
            )}

            {/* Question-level results */}
            <div className="rounded-2xl border" style={{background:'var(--surface-2)', borderColor:'var(--border)'}}>
              <div className="px-5 py-4 border-b flex items-center justify-between" style={{borderColor:'var(--border)'}}>
                <h2 className="text-sm font-bold text-white">All results ({filteredResults.length})</h2>
                <div className="flex gap-1">
                  {['all', 'tree', 'graph', 'vector'].map(m => {
                    const meta = MODE_META[m]
                    return (
                      <button key={m} onClick={() => setFilterMode(m)}
                        className="px-3 py-1 rounded-lg text-xs font-medium transition-all"
                        style={filterMode === m
                          ? {background: meta?.bg || 'rgba(124,58,237,0.15)', color: meta?.color || '#a78bfa'}
                          : {color:'#475569', background:'transparent'}
                        }
                      >
                        {m === 'all' ? 'All' : meta?.label}
                      </button>
                    )
                  })}
                </div>
              </div>
              <div className="px-5">
                {filteredResults.map((r, i) => <QuestionRow key={i} result={r} />)}
              </div>
            </div>

            <p className="text-xs text-center pb-4" style={{color:'#4c4f7a'}}>
              Results saved to backend/data/eval_results/ — use this data for your research paper
            </p>
          </>
        )}

        {!results && !running && (
          <div className="rounded-2xl border p-10 text-center" style={{background:'var(--surface-2)', borderColor:'var(--border)'}}>
            <BarChart3 size={28} className="mx-auto mb-3" style={{color:'#4c4f7a'}} />
            <p className="text-sm font-medium text-white mb-1">No benchmark results yet</p>
            <p className="text-xs mb-4" style={{color:'#475569'}}>Run the benchmark to see which retrieval mode performs best on this codebase.</p>
            <button onClick={runBenchmark} disabled={running || activeRepo.status !== 'ready'} className="btn-primary mx-auto">
              <Play size={14} />Run benchmark
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
