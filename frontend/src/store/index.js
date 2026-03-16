import { create } from 'zustand'

export const useStore = create((set, get) => ({
  repos: [], activeRepo: null,
  setRepos: (repos) => set({ repos }),
  setActiveRepo: (repo) => set({ activeRepo: repo, messages: [], activeFile: null }),
  fileTree: null, activeFile: null, activeFileContent: null,
  setFileTree: (tree) => set({ fileTree: tree }),
  setActiveFile: (file, content) => set({ activeFile: file, activeFileContent: content }),
  messages: [], isStreaming: false,
  addMessage: (msg) => set((s) => ({ messages: [...s.messages, msg] })),
  updateLastMessage: (patch) => set((s) => {
    const msgs = [...s.messages]
    if (msgs.length > 0) msgs[msgs.length - 1] = { ...msgs[msgs.length - 1], ...(typeof patch === 'function' ? patch(msgs[msgs.length - 1]) : patch) }
    return { messages: msgs }
  }),
  setStreaming: (v) => set({ isStreaming: v }),
  clearMessages: () => set({ messages: [] }),
  queryMode: 'auto', setQueryMode: (m) => set({ queryMode: m }),
  showGraph: false, toggleGraph: () => set((s) => ({ showGraph: !s.showGraph })),
  sidebarOpen: true, toggleSidebar: () => set((s) => ({ sidebarOpen: !s.sidebarOpen })),
}))
