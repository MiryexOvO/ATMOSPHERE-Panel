export function useApi() {
  const request = <T>(url: string, options: Parameters<typeof $fetch<T>>[1] = {}) => $fetch<T>(url, { credentials: 'include', ...options })
  const getErrorMessage = (cause: unknown, fallback = '请求失败') => {
    const err = cause as { data?: { message?: string }; message?: string }
    return err.data?.message || err.message || fallback
  }
  return { request, getErrorMessage }
}
