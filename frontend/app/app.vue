<script setup lang="ts">
const colorMode = useColorMode()
const authTransition = useState('auth-transition', () => 'idle')
const isRouteTransitioning = useState('route-transitioning', () => false)
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
  <NuxtLayout>
    <div class="app-transition-shell" :class="`app-transition-${authTransition}`">
      <NuxtPage :transition="false" />
      <div v-if="authTransition === 'expanding'" class="dashboard-reveal-surface" aria-hidden="true" />
    </div>
    <div class="global-route-overlay" :class="{ 'is-visible': isRouteTransitioning }" aria-hidden="true" />
    <div id="route-card-handoff" aria-hidden="true" />
  </NuxtLayout>
</template>

<style>
.app-transition-shell { perspective: 1000px; transform-style: preserve-3d; }
.dashboard-reveal-surface { position: fixed; inset: 0; z-index: 40; pointer-events: none; background: transparent; opacity: 1; clip-path: inset(100% 0 0 0); animation: dashboard-surface-reveal 800ms cubic-bezier(.22,.8,.2,1) forwards; }
.global-auth-lock { position: fixed; inset: 0; z-index: 9999; pointer-events: all; cursor: progress; background: transparent; }
.global-route-overlay { position: fixed; inset: 0; z-index: 10000; pointer-events: none; background: #0b0f14; opacity: 0; transition: opacity 180ms ease; }
.global-route-overlay.is-visible { opacity: 1; pointer-events: all; }
.route-card-clone { position: fixed; z-index: 10001; margin: 0; pointer-events: none; transform-origin: center; animation: route-card-expand 760ms cubic-bezier(.22,.8,.2,1) forwards; }
.route-card-clone::after { content: ''; position: absolute; inset: 0; pointer-events: none; background: linear-gradient(180deg, transparent 49.7%, rgba(255,255,255,.85) 50%, transparent 50.3%); animation: route-card-scan 760ms linear forwards; }
@keyframes route-card-expand { 0% { clip-path: inset(0); opacity: 1; transform: translate(0,0) scale(1); } 35% { clip-path: inset(0 0 100% 0); opacity: 1; transform: translate(0,0) scale(1); } 36% { clip-path: inset(0); opacity: 1; transform: translate(0,0) scale(1); } 100% { clip-path: inset(0); opacity: 1; transform: translate(0,0) scale(1); } }
@keyframes route-card-scan { from { transform: translateY(-100%); opacity: 0; } 15% { opacity: 1; } to { transform: translateY(100%); opacity: 0; } }
.auth-transition-card { position: relative; z-index: 50; }
.auth-transition-card.is-expanding { animation: outer-shell-erase 800ms cubic-bezier(.4,0,1,1) forwards; }
.auth-transition-card.is-expanding .login-glass-card { animation: inner-card-expand 800ms cubic-bezier(.22,.8,.2,1) 260ms forwards; }
.app-transition-expanding .auth-transition-card { animation: shell-erase 800ms cubic-bezier(.4,0,1,1) forwards; box-shadow: 0 0 100px rgba(0,0,0,.9); }
.app-transition-expanding .auth-transition-card::before { content: ''; position: absolute; inset: 0; z-index: -1; background: transparent; pointer-events: none; }
.app-transition-expanding .auth-transition-content { animation: content-fade-out 200ms ease-out forwards; }
.app-transition-expanding .auth-transition-card::after { content: ''; position: absolute; inset: 0; z-index: 50; pointer-events: none; background: linear-gradient(180deg, transparent 49.9%, rgba(255,255,255,.8) 50%, transparent 50.1%); animation: auth-scan 800ms ease-out forwards; opacity: 0; }
@keyframes content-fade-out { 0% { opacity: 1; transform: translateY(0); filter: blur(0); } 100% { opacity: 0; transform: translateY(-20px); filter: blur(4px); } }
@keyframes shell-erase { 0% { opacity: 1; clip-path: inset(0 0 0 0); } 100% { opacity: 0; clip-path: inset(0 0 100% 0); } }
@keyframes outer-shell-erase { 0% { opacity: 1; clip-path: inset(0 0 0 0); } 100% { opacity: 0; clip-path: inset(0 0 100% 0); } }
@keyframes inner-card-expand { 0% { transform: translate(0,0) scale(1); opacity: 1; } 100% { transform: translate(-30vw,-30vh) scale(2.8); opacity: 1; } }
@keyframes auth-scan { 0% { opacity: 0; transform: translateY(-110%); } 30% { opacity: .9; } 100% { opacity: 0; transform: translateY(110%); } }
@keyframes dashboard-surface-reveal { 0% { clip-path: inset(100% 0 0 0); } 100% { clip-path: inset(0 0 0 0); } }
@media (prefers-reduced-motion: reduce) { .app-transition-expanding .auth-transition-card { animation: none; opacity: 0; } .app-transition-expanding .auth-transition-card::after { display: none; } }
</style>
