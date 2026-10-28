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
    const err = cause as { data?: { message?: string }; message?: string }
    return err.data?.message || err.message || fallback
  }

  return { request, getErrorMessage }
}
