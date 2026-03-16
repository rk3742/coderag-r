import { useEffect, useRef } from 'react'
import { api } from '../utils/api'
import { useStore } from '../store'

export function useRepoPoll(repoId, interval = 2000) {
  const setRepos = useStore(s => s.setRepos)
  const repos = useStore(s => s.repos)
  const activeRepo = useStore(s => s.activeRepo)
  const setActiveRepo = useStore(s => s.setActiveRepo)
  const timerRef = useRef(null)

  useEffect(() => {
    if (!repoId) return
    const repo = repos.find(r => r.id === repoId)
    if (repo?.status === 'ready' || repo?.status === 'failed') return

    const poll = async () => {
      try {
        const updated = await api.getRepo(repoId)
        setRepos(repos.map(r => r.id === repoId ? updated : r))
        if (activeRepo?.id === repoId) setActiveRepo(updated)
        if (updated.status === 'ready' || updated.status === 'failed') {
          clearInterval(timerRef.current)
        }
      } catch {}
    }

    timerRef.current = setInterval(poll, interval)
    return () => clearInterval(timerRef.current)
  }, [repoId, repos])
}

export function useAllRepoPoll(interval = 3000) {
  const repos = useStore(s => s.repos)
  const setRepos = useStore(s => s.setRepos)

  useEffect(() => {
    const pending = repos.filter(r => r.status === 'indexing' || r.status === 'pending')
    if (pending.length === 0) return

    const timer = setInterval(async () => {
      try {
        const updated = await api.listRepos()
        setRepos(updated)
      } catch {}
    }, interval)

    return () => clearInterval(timer)
  }, [repos])
}
