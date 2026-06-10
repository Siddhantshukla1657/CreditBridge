import axios from 'axios'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '',
  headers: { 'Content-Type': 'application/json' },
  timeout: 15000,
})

export const scoreApplicant = (payload) => api.post('/score', payload).then(r => r.data)
export const getScore = (id) => api.get(`/score/${id}`).then(r => r.data)
export const getModelCard = () => api.get('/model-card').then(r => r.data)
export const getHealth = () => api.get('/health').then(r => r.data)

export default api
