export default defineNuxtRouteMiddleware(async (to) => {
  const { request } = useApi()
  if (to.path === '/login') return
  try {
    await request('/api/me', { timeout: 5000 })
  } catch {
    return navigateTo('/login', { replace: true })
  }
})
