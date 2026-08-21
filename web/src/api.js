// REST API 封装：dev 模式走 Vite 代理，生产同源部署
const BASE = ''

async function request(path, options = {}) {
  const res = await fetch(BASE + path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  })
  if (!res.ok) {
    const body = await res.json().catch(() => ({}))
    throw new Error(body.detail || `请求失败 ${res.status}`)
  }
  return res.json()
}

export const api = {
  health: () => request('/api/health'),
  summary: (params = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null),
    ).toString()
    return request(`/api/jobs/summary${q ? `?${q}` : ''}`)
  },
  jobs: (params = {}) => {
    const q = new URLSearchParams(
      Object.entries(params).filter(([, v]) => v !== '' && v != null),
    ).toString()
    return request(`/api/jobs${q ? `?${q}` : ''}`)
  },
  meta: () => request('/api/meta'),
  predict: (payload) =>
    request('/api/model/predict', { method: 'POST', body: JSON.stringify(payload) }),
}
