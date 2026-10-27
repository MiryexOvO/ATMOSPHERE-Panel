export default defineNuxtRouteMiddleware(async (to) => {
  if (to.path === '/login') return
  try {
    await $fetch('/api/me', { credentials: 'include', timeout: 5000 })
  } catch {
    return navigateTo('/login', { replace: true })
  }
})
