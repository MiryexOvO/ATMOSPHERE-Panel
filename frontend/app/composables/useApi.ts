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
