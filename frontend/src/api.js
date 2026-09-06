import axios from 'axios'

// Relative baseURL: dev uses the Vite proxy, prod uses the nginx reverse proxy.
const http = axios.create({ baseURL: '', timeout: 180000 })

const data = (p) => p.then((r) => r.data)

export const api = {
  createProject: (payload) => data(http.post('/api/projects', payload)),
  regenerate: (id) => data(http.post(`/api/projects/${id}/regenerate`)),
  selectIdea: (id, ideaId) => data(http.post(`/api/projects/${id}/select`, { idea_id: ideaId })),
  modifyIdea: (id, idea) => data(http.post(`/api/projects/${id}/modify`, { idea })),
  getEvaluations: (id) => data(http.get(`/api/projects/${id}/evaluations`)),
  getDebate: (id) => data(http.get(`/api/projects/${id}/debate`)),
  getBlueprint: (id) => data(http.get(`/api/projects/${id}/blueprint`)),
  getAlignment: (id) => data(http.get(`/api/projects/${id}/alignment`)),
  adaptPersona: (id, persona) => data(http.post(`/api/projects/${id}/persona`, { persona })),
  listProjects: () => data(http.get('/api/projects')),
  // Blueprint document export (opens the download in a new tab).
  exportDocxUrl: (id) => `/api/projects/${id}/export/docx`,
  exportPdfUrl: (id) => `/api/projects/${id}/export/pdf`,
}

export function errMsg(e) {
  return e?.response?.data?.detail || e?.message || 'Request failed'
}
