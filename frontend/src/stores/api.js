import axios from 'axios'

const CONTEXT_PATH = '/ztailog'

const api = axios.create({
  baseURL: CONTEXT_PATH + '/api',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})
// 下载文件时使用单独的配置
export const downloadApi = axios.create({
  baseURL: CONTEXT_PATH + '/api',
  timeout: 120000,  // 增加超时时间到 120 秒
  responseType: 'blob'
})
// 请求拦截器
api.interceptors.request.use(
  config => {
    return config
  },
  error => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  response => {
    return response
  },
  error => {
    console.error('API Error:', error)
    return Promise.reject(error)
  }
)

export default api
