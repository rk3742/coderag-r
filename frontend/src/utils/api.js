const BASE = import.meta.env.VITE_API_URL ? `${import.meta.env.VITE_API_URL}/api` : '/api'

async function request(path, opts = {}) {
  const res = await fetch(`${BASE}${path}`, {
    headers: { 'Content-Type': 'application/json', ...opts.headers },
    ...opts,
  })
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }))
    throw new Error(err.detail || 'Request failed')
  }
  return res.json()
}

export const api = {
  // Repos
  listRepos: () => request('/repos/'),
  getRepo: (id) => request(`/repos/${id}`),
  addGithub: (github_url, name) => request('/repos/github', {
    method: 'POST',
    body: JSON.stringify({ github_url, name }),
  }),
  uploadZip: (file, name) => {
    const fd = new FormData()
    fd.append('file', file)
    fd.append('name', name)
    return fetch(`${BASE}/repos/upload`, { method: 'POST', body: fd }).then(r => r.json())
  },
  deleteRepo: (id) => request(`/repos/${id}`, { method: 'DELETE' }),
  getFileTree: (id) => request(`/repos/${id}/files`),
  getFileContent: (id, path) => request(`/repos/${id}/file?path=${encodeURIComponent(path)}`),
  getSummary: (id) => request(`/repos/${id}/summary`),

  // Graph
  getGraph: (id, maxNodes = 150) => request(`/graph/${id}?max_nodes=${maxNodes}`),

  // Streaming query
  streamQuery(repoId, question, mode = 'auto', topK = 8, onEvent) {
    const controller = new AbortController()
    fetch(`${BASE}/query/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ repo_id: repoId, question, mode, top_k: topK }),
      signal: controller.signal,
    }).then(async (res) => {
      if (!res.ok) {
        onEvent({ type: 'error', content: `HTTP ${res.status}` })
        return
      }
      const reader = res.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      while (true) {
        const { done, value } = await reader.read()
        if (done) break
        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()
        for (const line of lines) {
          if (line.startsWith('data: ')) {
            try {
              const data = JSON.parse(line.slice(6))
              onEvent(data)
            } catch {}
          }
        }
      }
    }).catch((e) => {
      if (e.name !== 'AbortError') onEvent({ type: 'error', content: e.message })
    })
    return () => controller.abort()
  },
}
setInterval(() => {
  fetch(`${BASE.replace('/api', '')}/health`).catch(() => {})
}, 10 * 60 * 1000)