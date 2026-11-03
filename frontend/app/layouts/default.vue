<script setup lang="ts">
import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'
import ScrollRuler from '~/components/ui/ScrollRuler.vue'
import { useSmoothScroll } from '~/composables/useSmoothScroll'

useSmoothScroll()

const seam = useRouteSeam()
// 从登录页进入时，顶栏与页面内容一起延后淡入
const enteringFromLogin = seam.value.phase === 'away' || seam.value.phase === 'clearing'

const { t, locale } = useI18n()
const preferences = useState<Record<string, unknown>>('panel-preferences', () => ({}))
const panelName = computed(() => 'ATMOSPHERE')
useHead(() => ({ title: panelName.value }))

const now = ref(new Date())
// null 表示鼠标还没移动过
const pointer = ref<{ x: number; y: number } | null>(null)
const menu = ref(false)
const paletteOpen = ref(false)
const paletteTrigger = ref<HTMLElement | null>(null)
const palettePanel = ref<HTMLElement | null>(null)
const menuTrigger = ref<HTMLElement | null>(null)
const menuPanel = ref<HTMLElement | null>(null)
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
let pointerFrame = 0
let pendingPointer: { x: number; y: number } | null = null

function trackPointer(event: PointerEvent) {
  pendingPointer = { x: Math.round(event.clientX), y: Math.round(event.clientY) }
  if (pointerFrame) return
  pointerFrame = requestAnimationFrame(() => {
    pointerFrame = 0
    if (pendingPointer) pointer.value = pendingPointer
  })
}

const coordinates = computed(() => ({
  x: pointer.value ? String(pointer.value.x).padStart(4, '0') : '----',
  y: pointer.value ? String(pointer.value.y).padStart(4, '0') : '----',
}))

const themeOptions = computed(() => [
  { label: 'SYSTEM', value: 'system' },
  { label: 'DARK', value: 'dark' },
  { label: 'LIGHT', value: 'light' },
])

// 点击 PALETTE 面板或用户菜单以外的区域时自动收起
function closePopovers(event: MouseEvent) {
  const node = event.target as Node | null
  if (!node) return
  if (paletteOpen.value && !paletteTrigger.value?.contains(node) && !palettePanel.value?.contains(node))
    paletteOpen.value = false
  if (menu.value && !menuTrigger.value?.contains(node) && !menuPanel.value?.contains(node)) menu.value = false
}

onMounted(() => {
  // 默认布局读取面板偏好，不覆盖用户已保存的语言选择。
  useApi()
    .request<{ settings: Record<string, unknown> }>('/api/panel/settings')
    .then((result) => {
      preferences.value = result.settings
      if (!localStorage.getItem('preferred-language'))
        locale.value = String(result.settings.default_locale || 'zh') as 'zh' | 'en' | 'ja'
    })
    .catch(() => {})
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  window.addEventListener('pointermove', trackPointer, { passive: true })
  document.addEventListener('click', closePopovers)
  const saved = localStorage.getItem('custom-theme')
  if (saved) {
    try {
      customColors.value = JSON.parse(saved)
    } catch {
      /* ignore malformed local preference */
    }
  }
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('pointermove', trackPointer)
  document.removeEventListener('click', closePopovers)
  if (pointerFrame) cancelAnimationFrame(pointerFrame)
})

function applyColor(field: (typeof fields)[number], value: string) {
  customColors.value[field.key] = value
  document.documentElement.style.setProperty(field.variable, value)
  localStorage.setItem('custom-theme', JSON.stringify(customColors.value))
}

function selectTheme(value: 'system' | 'dark' | 'light') {
  colorMode.preference = value
  localStorage.removeItem('custom-theme')
  // 即使再次选择当前模式，也要清除自定义颜色的残留。
  const light = value === 'light' || (value === 'system' && window.matchMedia('(prefers-color-scheme: light)').matches)
  customColors.value = light
    ? { textPrimary: '#27313b', textSecondary: '#626e78', surface: '#ffffff', background: '#f1f4f6' }
    : { textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' }
  for (const field of fields) document.documentElement.style.setProperty(field.variable, customColors.value[field.key])
  document.documentElement.style.setProperty('--brand', customColors.value.textPrimary)
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
    <ScrollRuler />
    <header
      class="relative z-10 flex h-20 items-center justify-between border-b border-border px-8"
      :class="{ 'layout-enter': enteringFromLogin }"
    >
      <div class="flex items-center gap-5">
        <span class="text-brand">✦</span>
        <strong class="font-mono tracking-[0.18em]">{{ panelName }}</strong>
        <small class="font-mono text-xs tracking-[0.18em] text-text-secondary">MC SERVER OPERATIONS / 02</small>
      </div>
      <div class="relative flex items-center gap-4 font-mono text-xs text-text-secondary">
        <button
          ref="paletteTrigger"
          type="button"
          class="border border-border px-3 py-2 hover:border-brand hover:text-brand"
          @click="paletteOpen = !paletteOpen"
        >
          ◒ PALETTE
        </button>
        <span class="hidden items-center leading-none tabular-nums lg:inline-flex">
          <span class="mr-2 translate-y-[-1.5px] leading-none">⌖</span>
          <span class="leading-none">[</span>
          <span class="px-2 leading-none">{{ coordinates.x }} N / {{ coordinates.y }} W</span>
          <span class="leading-none">]</span>
        </span>
        <span class="flex items-center gap-1.5 leading-none text-data-live">
          <span class="translate-y-[-1.5px] leading-none">●</span>
          <span class="leading-none">SIGNAL / OK</span>
        </span>
        <span class="hidden md:inline">{{ now.toLocaleTimeString('en-GB') }}</span>
        <button
          ref="menuTrigger"
          type="button"
          class="border border-border px-2 py-1 hover:border-brand hover:text-brand"
          @click="menu = !menu"
        >
          A
        </button>
        <Transition name="palette-fade">
          <div
            v-if="menu"
            ref="menuPanel"
            class="absolute top-12 right-0 z-30 w-36 border border-border bg-surface p-2 shadow-2xl"
          >
            <button
              type="button"
              class="block w-full px-3 py-2 text-left text-xs hover:bg-background hover:text-text-primary"
              @click="logout"
            >
              {{ t('logout') }}
            </button>
          </div>
        </Transition>
        <Transition name="palette-fade">
          <div
            v-if="paletteOpen"
            ref="palettePanel"
            class="absolute top-12 right-0 z-20 w-64 border border-border bg-surface p-5 shadow-2xl"
          >
            <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">APPEARANCE</p>
            <div class="space-y-1 border-b border-border pb-4">
              <button
                v-for="theme in themeOptions"
                :key="theme.value"
                type="button"
                class="flex w-full items-center gap-2 px-3 py-2 text-left font-mono text-[10px] text-text-secondary hover:bg-background hover:text-brand"
                :class="
                  colorMode.preference === theme.value
                    ? 'border border-brand text-text-primary'
                    : 'border border-transparent'
                "
                @click="selectTheme(theme.value as 'system' | 'dark' | 'light')"
              >
                <span>◌</span>{{ theme.label }}
              </button>
            </div>
            <p class="mt-4 mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">CUSTOM COLORS</p>
            <div class="grid grid-cols-4 gap-3">
              <label
                v-for="field in fields"
                :key="field.variable"
                class="group relative flex h-9 w-9 cursor-pointer items-center justify-center rounded-full border border-border shadow-lg hover:scale-110"
                :title="field.label"
              >
                <input
                  type="color"
                  class="absolute inset-0 h-full w-full cursor-pointer opacity-0"
                  :value="customColors[field.key]"
                  @input="applyColor(field, ($event.target as HTMLInputElement).value)"
                />
                <span
                  class="pointer-events-none h-7 w-7 rounded-full"
                  :style="{ backgroundColor: customColors[field.key] }"
                />
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
.layout-enter {
  animation: layout-enter 700ms cubic-bezier(0.22, 1, 0.36, 1) 320ms both;
}
@keyframes layout-enter {
  from {
    opacity: 0;
  }
  to {
    opacity: 1;
  }
}
.palette-fade-enter-active,
.palette-fade-leave-active {
  transition:
    opacity 180ms ease,
    transform 180ms ease;
}
.palette-fade-enter-from,
.palette-fade-leave-to {
  opacity: 0;
  transform: translateY(-8px) scale(0.98);
}
</style>
