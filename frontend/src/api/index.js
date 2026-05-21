import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000,
})

api.interceptors.response.use(
  (response) => response.data,
  (error) => {
    const msg = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(msg)
    return Promise.reject(error)
  }
)

export const authApi = {
  login: (data) => api.post('/auth/login', data),
  register: (data) => api.post('/auth/register', data),
  getMe: (token) => api.get('/auth/me', { params: { token } }),
  listUsers: () => api.get('/auth/users'),
  toggleUser: (id) => api.put(`/auth/users/${id}/toggle`),
}

export const bookApi = {
  list: (params) => api.get('/books', { params }),
  get: (id) => api.get(`/books/${id}`),
  create: (data) => api.post('/books', data),
  update: (id, data) => api.put(`/books/${id}`, data),
  delete: (id) => api.delete(`/books/${id}`),
  importPages: (id, formData) => api.post(`/books/${id}/pages`, formData, {
    headers: { 'Content-Type': 'multipart/form-data' },
    timeout: 300000,
  }),
  getPages: (id, params) => api.get(`/books/${id}/pages`, { params }),
  getPage: (bookId, pageId) => api.get(`/books/${bookId}/pages/${pageId}`),
  updatePageText: (bookId, pageId, data) => api.put(`/books/${bookId}/pages/${pageId}/text`, data),
  deletePage: (bookId, pageId) => api.delete(`/books/${bookId}/pages/${pageId}`),
  togglePageReview: (bookId, pageId) => api.put(`/books/${bookId}/pages/${pageId}/review`),
  completeBook: (id) => api.post(`/books/${id}/complete`),
  startOcr: (id, data) => api.post(`/books/${id}/ocr`, { book_id: id, ...data }),
  getTasks: (id) => api.get(`/books/${id}/tasks`),
  getStats: () => api.get('/books/stats'),
  getCategories: () => api.get('/books/categories'),
  getPageImage: (bookId, pageId) => `/api/books/${bookId}/pages/${pageId}/image`,
  getPageThumbnail: (bookId, pageId) => `/api/books/${bookId}/pages/${pageId}/thumbnail`,
  getCoverUrl: (id) => `/api/books/${id}/cover`,
}

export const ocrApi = {
  getStatus: () => api.get('/ocr/status'),
  getOptions: () => api.get('/ocr/options'),
  search: (data) => api.post('/ocr/search', data),
}

export const exportApi = {
  exportBook: (data) => api.post('/export', data),
  downloadUrl: (filename) => `/api/export/download/${filename}`,
}

export const recycleApi = {
  list: (params) => api.get('/recycle', { params }),
  restore: (id) => api.post(`/recycle/${id}/restore`),
  permanentDelete: (id) => api.delete(`/recycle/${id}`),
  listPages: (params) => api.get('/recycle/pages', { params }),
  restorePage: (id) => api.post(`/recycle/pages/${id}/restore`),
  permanentDeletePage: (id) => api.delete(`/recycle/pages/${id}`),
}

export default api
