export function useAuth() {
  const { request } = useApi()
  const user = useState<{ username: string } | null>('auth-user', () => null)
  const error = ref('')
  const loading = ref(false)
  async function login(username: string, password: string) {
    loading.value = true
    error.value = ''
    try {
      const result = await request<{ user: { username: string } }>('/api/login', {
        method: 'POST',
        body: { username, password },
        timeout: 8000,
      })
      user.value = result.user
      return result
    } catch (cause: unknown) {
      const err = cause as { data?: { message?: string }; message?: string }
      error.value = err.data?.message || err.message || '登录失败'
      throw cause
    } finally {
      loading.value = false
    }
  }
  async function logout() {
    await request('/api/logout', { method: 'POST' })
    user.value = null
  }
  async function me() {
    const result = await request<{ user: { username: string } }>('/api/me')
    user.value = result.user
    return result
  }
  return { user, error, loading, login, logout, me }
}
