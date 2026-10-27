<script setup lang="ts">

import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'

const now = ref(new Date())
const menu = ref(false)
const paletteOpen = ref(false)
const colorMode = useColorMode()
const customColors = ref({
  textPrimary: '#e9dfc6',
  textSecondary: '#a4aaa3',
  surface: '#1c252d',
  background: '#11151b',
})
const fields = [
  { label: 'TEXT1', key: 'textPrimary', variable: '--text-primary' },
  { label: 'TEXT2', key: 'textSecondary', variable: '--text-secondary' },
  { label: 'UI COLOR', key: 'surface', variable: '--surface' },
  { label: 'BACKGROUND', key: 'background', variable: '--background' },
] as const
let timer: ReturnType<typeof setInterval> | undefined

const themeOptions = computed(() => [
  { label: 'SYSTEM', value: 'system' },
  { label: 'DARK', value: 'dark' },
  { label: 'LIGHT', value: 'light' },
])

onMounted(() => {
  timer = setInterval(() => { now.value = new Date() }, 1000)
  const saved = localStorage.getItem('custom-theme')
  if (saved) {
    try { customColors.value = JSON.parse(saved) } catch { /* ignore malformed local preference */ }
  }
})

onUnmounted(() => { if (timer) clearInterval(timer) })

function applyColor(field: typeof fields[number], value: string) {
  customColors.value[field.key] = value
  document.documentElement.style.setProperty(field.variable, value)
  localStorage.setItem('custom-theme', JSON.stringify(customColors.value))
}

function selectTheme(value: 'system' | 'dark' | 'light') {
  colorMode.preference = value
  localStorage.removeItem('custom-theme')
  paletteOpen.value = true
}

async function logout() {
  await $fetch('/api/logout', { method: 'POST', credentials: 'include' })
  await navigateTo('/login')
}
</script>

<template>
  <div class="relative min-h-screen overflow-hidden bg-background text-text-primary">
    <StarfieldBackground />
    <header class="relative z-10 flex h-20 items-center justify-between border-b border-border px-8">
      <div class="flex items-center gap-5">
        <span class="text-brand">✦</span>
        <strong class="font-mono tracking-[0.18em]">ATMOSPHERE</strong>
        <small class="font-mono text-xs tracking-[0.18em] text-text-secondary">MC SERVER OPERATIONS / 02</small>
      </div>
      <div class="relative flex items-center gap-4 font-mono text-xs text-text-secondary">
        <button type="button" class="border border-border px-3 py-2 hover:border-brand hover:text-brand" @click="paletteOpen = !paletteOpen">
          ◒ PALETTE
        </button>
        <span class="hidden lg:inline">CPU 12% · RAM 4.2G</span>
        <span class="text-data-live">● SIGNAL / OK</span>
        <span class="hidden md:inline">{{ now.toLocaleTimeString('en-GB') }}</span>
        <button type="button" class="border border-border px-2 py-1 hover:border-brand hover:text-brand" @click="menu = !menu">A</button>
        <div v-if="menu" class="absolute right-0 top-12 z-30 w-36 border border-border bg-surface p-2 shadow-2xl">
          <button type="button" class="block w-full px-3 py-2 text-left text-xs hover:bg-background hover:text-text-primary" @click="logout">登出</button>
        </div>
        <Transition name="palette-fade">
          <div v-if="paletteOpen" class="absolute right-0 top-12 z-20 w-64 border border-border bg-surface p-5 shadow-2xl">
            <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">APPEARANCE</p>
            <div class="space-y-1 border-b border-border pb-4">
              <button v-for="theme in themeOptions" :key="theme.value" type="button" class="flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-[10px] text-text-secondary hover:bg-background hover:text-brand" :class="colorMode.preference === theme.value ? 'border border-brand text-text-primary' : 'border border-transparent'" @click="selectTheme(theme.value as 'system' | 'dark' | 'light')">
                <span>◌</span>{{ theme.label }}
              </button>
            </div>
            <p class="mb-3 mt-4 font-mono text-[9px] tracking-[0.2em] text-text-secondary">CUSTOM COLORS</p>
            <div class="grid grid-cols-4 gap-3">
              <label v-for="field in fields" :key="field.variable" class="group relative flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-border shadow-lg hover:scale-110" :title="field.label">
                <input type="color" class="absolute inset-0 h-full w-full cursor-pointer opacity-0" :value="customColors[field.key]" @input="applyColor(field, ($event.target as HTMLInputElement).value)">
                <span class="pointer-events-none h-7 w-7 rounded-full" :style="{ backgroundColor: customColors[field.key] }" />
              </label>
            </div>
          </div>
        </Transition>
      </div>
    </header>
    <slot />
  </div>
</template>

<style scoped>
.palette-fade-enter-active,
.palette-fade-leave-active { transition: opacity 180ms ease, transform 180ms ease; }
.palette-fade-enter-from,
.palette-fade-leave-to { opacity: 0; transform: translateY(-8px) scale(0.98); }
</style>