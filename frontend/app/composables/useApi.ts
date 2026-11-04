import { instancePath } from '~/utils/apiPath'

export function useApi() {
  const config = useRuntimeConfig()
  const token = useCookie<string | null>('mc_panel_session')

  const request = async <T>(url: string, options: Parameters<typeof $fetch<T>>[1] = {}) => {
    try {
      return await $fetch<T>(url, {
        credentials: 'include',
        baseURL: config.public.apiBase || undefined,
        headers: token.value ? { Authorization: `Bearer ${token.value}` } : undefined,
        ...options,
      })
    } catch (error: unknown) {
      return Promise.reject(error)
    }
  }

  const getErrorMessage = (cause: unknown, fallback = '请求失败') => {
    const err = cause as { data?: { message?: string; detail?: string | { msg: string }[] }; message?: string }
    return (
      err.data?.message ||
      (typeof err.data?.detail === 'string'
        ? err.data.detail
        : Array.isArray(err.data?.detail)
          ? err.data.detail.map((item) => item.msg).join('; ')
          : '') ||
      err.message ||
      fallback
    )
  }

  return { request, getErrorMessage }
}

type InstanceIdSource = string | (() => string)

// API 封装
// id 编码和前缀处理
export function useInstanceApi(instanceId: InstanceIdSource) {
  const { request, getErrorMessage } = useApi()

  const resolveId = () => (typeof instanceId === 'function' ? instanceId() : instanceId)
  // 生成实例路径，供 EventSource、下载链接等无法走 request 的场景使用
  const path = (suffix = '') => instancePath(resolveId(), suffix)
  // 实例请求
  const instanceRequest = <T>(suffix: string, options: Parameters<typeof request<T>>[1] = {}) =>
    request<T>(path(suffix), options)

  return { request, instanceRequest, path, getErrorMessage }
}
