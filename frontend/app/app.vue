<script setup lang="ts">
const colorMode = useColorMode()
const defaults = {
  dark: { textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' },
  light: { textPrimary: '#17233a', textSecondary: '#59636b', surface: '#fffdf7', background: '#e9e4d8' },
}
function applyTheme(colors: typeof defaults.dark) {
  const root = document.documentElement
  root.style.setProperty('--text-primary', colors.textPrimary)
  root.style.setProperty('--text-secondary', colors.textSecondary)
  root.style.setProperty('--surface', colors.surface)
  root.style.setProperty('--background', colors.background)
  root.style.setProperty('--brand', colors.textPrimary)
}
onMounted(() => {
  const saved = localStorage.getItem('custom-theme')
  if (saved) {
    try {
      applyTheme(JSON.parse(saved))
    } catch {
      applyTheme(defaults.dark)
    }
  } else applyTheme(defaults[colorMode.value === 'light' ? 'light' : 'dark'])
})
watch(
  () => colorMode.value,
  (mode) => {
    if (import.meta.client && !localStorage.getItem('custom-theme'))
      applyTheme(defaults[mode === 'light' ? 'light' : 'dark'])
  },
)
</script>
<template>
  <NuxtLayout><NuxtPage :transition="{ name: 'route', mode: 'out-in' }" /></NuxtLayout>
</template>
