import axios from 'axios'

// Relative baseURL: dev uses the Vite proxy, prod uses the nginx reverse proxy.
const http = axios.create({ baseURL: '', timeout: 180000 })

const data = (p) => p.then((r) => r.data)

export const api = {
  createProject: (payload) => data(http.post('/api/projects', payload)),
  regenerate: (id) => data(http.post(`/api/projects/${id}/regenerate`)),
  selectIdea: (id, ideaId) => data(http.post(`/api/projects/${id}/select`, { idea_id: ideaId })),
  modifyIdea: (id, idea) => data(http.post(`/api/projects/${id}/modify`, { idea })),
  getDebate: (id) => data(http.get(`/api/projects/${id}/debate`)),
  getBlueprint: (id) => data(http.get(`/api/projects/${id}/blueprint`)),
  getMetrics: (id) => data(http.get(`/api/projects/${id}/metrics`)),
  adaptPersona: (id, persona) => data(http.post(`/api/projects/${id}/persona`, { persona })),
  runBaseline: (id) => data(http.post(`/api/projects/${id}/baseline`)),
  getEvaluation: (id) => data(http.post(`/api/projects/${id}/evaluation`)),
  listProjects: () => data(http.get('/api/projects')),
}

export function errMsg(e) {
  return e?.response?.data?.detail || e?.message || 'Request failed'
}
