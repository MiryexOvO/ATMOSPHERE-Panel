import { instancePath } from '~/utils/apiPath'
import { hasCJK, translateBackendKey } from '~/utils/backendMessages'

export function useApi() {
  const config = useRuntimeConfig()
  // i18n 在少数上下文可能不可用，此时保持默认语言。
  let getLocale: () => string = () => 'zh'
  try {
    const { locale } = useI18n()
    getLocale = () => locale.value
  } catch {}
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

  const getErrorMessage = (cause: unknown, fallback = t('msg_request_failed')) => {
    const err = cause as { data?: { message?: string; detail?: string | { msg: string }[] }; message?: string }
    const raw =
      err.data?.message ||
      (typeof err.data?.detail === 'string'
        ? err.data.detail
        : Array.isArray(err.data?.detail)
          ? err.data.detail.map((item) => item.msg).join('; ')
          : '') ||
      err.message ||
      ''
    // 后端只返回中文时，按当前语言翻译；没有收录则回退到调用方的本地化文案。
    const key = translateBackendKey(raw)
    if (key) return t(key)
    if (getLocale() !== 'zh' && hasCJK(raw)) return fallback
    return raw || fallback
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
