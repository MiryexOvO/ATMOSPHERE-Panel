<script setup lang="ts">
import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'
import ScrollRuler from '~/components/ui/ScrollRuler.vue'
import { useSmoothScroll } from '~/composables/useSmoothScroll'

useSmoothScroll()

const seam = useRouteSeam()
const authTransition = useState('auth-transition', () => 'idle')
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
// usePanelTheme 管理这些
const { colors: customColors, fields, themeOptions, selectTheme, applyColor } = usePanelTheme()
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
      if (!localStorage.getItem('preferred-language')) {
        const value = String(result.settings.default_locale || 'zh')
        locale.value = value as 'zh' | 'en' | 'ja'
        // 记住面板默认语言，下次打开登录页时沿用。
        localStorage.setItem('preferred-language', value)
      }
    })
    .catch(() => {})
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  window.addEventListener('pointermove', trackPointer, { passive: true })
  document.addEventListener('click', closePopovers)
})

onUnmounted(() => {
  if (timer) clearInterval(timer)
  window.removeEventListener('pointermove', trackPointer)
  document.removeEventListener('click', closePopovers)
  if (pointerFrame) cancelAnimationFrame(pointerFrame)
})

// 取色与主题切换统一交给 usePanelTheme，这里只处理面板开合。
function updateColor(field: (typeof fields)[number], value: string) {
  applyColor(field.key, value)
}

function chooseTheme(value: 'system' | 'dark' | 'light') {
  selectTheme(value)
  paletteOpen.value = true
}

// 登出：反向播放登录交接，框线从视口收拢回登录卡片，卡片由擦除状态还原
async function logout() {
  if (authTransition.value !== 'idle' || seam.value.phase !== 'idle') return
  const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (reducedMotion) {
    await $fetch('/api/logout', { method: 'POST', credentials: 'include' })
    await navigateTo('/login')
    return
  }
  // 覆盖阶段先沿用上次登录卡片尺寸，刷新后回退到常见尺寸
  const previous = seam.value
  const width = previous.w || Math.min(448, window.innerWidth - 64)
  const height = previous.h || 540
  const wait = (ms: number) => new Promise((resolve) => setTimeout(resolve, ms))
  const nextFrame = () => new Promise((resolve) => requestAnimationFrame(() => resolve(null)))
  try {
    // 1. 框线伸展开来、遮罩淡入，盖住仪表盘
    seam.value = { phase: 'sealing', x: 0, y: 0, w: width, h: height }
    await nextTick()
    await nextFrame()
    seam.value.phase = 'sealed'
    await wait(560)
    await $fetch('/api/logout', { method: 'POST', credentials: 'include' })
    // 2. 登录页先以擦除状态挂载，路由切换藏在遮罩后
    authTransition.value = 'restoring'
    await navigateTo('/login')
    await nextTick()
    let stage: DOMRect | undefined
    for (let frame = 0; frame < 12 && !stage; frame++) {
      stage = document.querySelector('.login-transition-stage')?.getBoundingClientRect()
      if (!stage) await nextFrame()
    }
    if (!stage) throw new Error('login stage missing')
    // 3. 框线飞回登录卡片两角，遮罩同步收拢
    seam.value = { phase: 'returning', x: stage.x, y: stage.y, w: stage.width, h: stage.height }
    await wait(800)
    // 4. 遮罩淡出，卡片反向还原
    seam.value.phase = 'at-card'
    authTransition.value = 'restoring-run'
    await wait(800)
  } catch {
    // 登出失败或页面结构异常时收回覆盖
    authTransition.value = 'idle'
    seam.value.phase = 'sealing'
    await wait(560)
  }
  seam.value.phase = 'idle'
  authTransition.value = 'idle'
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
                @click="chooseTheme(theme.value as 'system' | 'dark' | 'light')"
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
                  @input="updateColor(field, ($event.target as HTMLInputElement).value)"
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
