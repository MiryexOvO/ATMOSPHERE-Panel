<script setup lang="ts">
import { Icon } from '@iconify/vue'
import DotField from '~/components/ui/DotField.vue'

definePageMeta({ layout: 'auth' })

const username = ref('Atmo7')
const password = ref('')
const error = ref('')
const loading = ref(false)
const apiOnline = ref(false)
const showPassword = ref(false)
const paletteOpen = ref(false)
const now = ref(new Date())
const colorMode = useColorMode()
const { request, getErrorMessage } = useApi()
const customColors = ref({
  textPrimary: '#e9dfc6',
  textSecondary: '#a4aaa3',
  surface: '#1c252d',
  background: '#11151b',
})
const colorFields = [
  { label: 'TEXT1', variable: 'text-primary', key: 'textPrimary' },
  { label: 'TEXT2', variable: 'text-secondary', key: 'textSecondary' },
  { label: 'UI COLOR', variable: 'surface', key: 'surface' },
  { label: 'BACKGROUND', variable: 'background', key: 'background' },
] as const
const themeOptions = [
  { label: 'SYSTEM', value: 'system' },
  { label: 'DARK', value: 'dark' },
  { label: 'LIGHT', value: 'light' },
] as const
function selectTheme(value: 'system' | 'dark' | 'light') {
  colorMode.preference = value
  localStorage.removeItem('custom-theme')
  const colors =
    value === 'light'
      ? { textPrimary: '#17233a', textSecondary: '#59636b', surface: '#fffdf7', background: '#e9e4d8' }
      : { textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' }
  customColors.value = colors
  for (const field of colorFields) document.documentElement.style.setProperty('--' + field.variable, colors[field.key])
  document.documentElement.style.setProperty('--brand', colors.textPrimary)
}
const { t, locale, setLocale } = useI18n()
const languages = [
  { code: 'zh', label: 'ZH' },
  { code: 'en', label: 'EN' },
  { code: 'ja', label: 'JA' },
] as const
type LocaleCode = (typeof languages)[number]['code']
function changeLocale(code: string) {
  if (languages.some((language) => language.code === code)) setLocale(code as LocaleCode)
}
const languageOpen = ref(false)
const langSwitch = ref<HTMLElement | null>(null)
const paletteTrigger = ref<HTMLElement | null>(null)
const palettePanel = ref<HTMLElement | null>(null)
function selectLanguage(code: LocaleCode) {
  if (!languageOpen.value) {
    languageOpen.value = true
    return
  }
  changeLocale(code)
  languageOpen.value = false
}
// 点击语言切换或调色板以外的区域时收起对应的小菜单
function closePopovers(event: MouseEvent) {
  const node = event.target as Node | null
  if (!node) return
  if (languageOpen.value && langSwitch.value && !langSwitch.value.contains(node)) languageOpen.value = false
  if (paletteOpen.value && !paletteTrigger.value?.contains(node) && !palettePanel.value?.contains(node))
    paletteOpen.value = false
}
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => {
    now.value = new Date()
  }, 1000)
  document.addEventListener('click', closePopovers)
  const saved = localStorage.getItem('custom-theme')
  if (saved) {
    try {
      customColors.value = JSON.parse(saved)
    } catch {}
  }
  for (const field of colorFields)
    document.documentElement.style.setProperty(`--${field.variable}`, customColors.value[field.key])
  document.documentElement.style.setProperty('--brand', customColors.value.textPrimary)
})
function saveToLocalStorage() {
  localStorage.setItem('custom-theme', JSON.stringify(customColors.value))
}
function applyCustomColor(variable: string, key: keyof typeof customColors.value, value: string) {
  customColors.value[key] = value
  document.documentElement.style.setProperty(`--${variable}`, value)
  if (key === 'textPrimary') document.documentElement.style.setProperty('--brand', value)
  saveToLocalStorage()
}
onUnmounted(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('click', closePopovers)
})

const authTransition = useState('auth-transition', () => 'idle')
const isRouteTransitioning = useState('route-transitioning', () => false)
const seam = useRouteSeam()

async function login() {
  if (loading.value || authTransition.value !== 'idle') return
  loading.value = true
  error.value = ''
  const timeout = setTimeout(() => {
    if (loading.value) {
      loading.value = false
      error.value = '后端连接超时，请确认 27777 服务已启动'
    }
  }, 8000)
  try {
    await request('/api/health', { timeout: 3000 })
    apiOnline.value = true
    await request('/api/login', {
      method: 'POST',
      timeout: 8000,
      body: { username: username.value, password: password.value },
    })
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    authTransition.value = reducedMotion ? 'navigating' : 'expanding'
    await nextTick()
    await new Promise((resolve) => setTimeout(resolve, reducedMotion ? 0 : 750))
    authTransition.value = 'navigating'
    await navigateTo('/dashboard')
    await nextTick()
    isRouteTransitioning.value = false
    authTransition.value = 'idle'
    document.getElementById('route-card-handoff')?.replaceChildren()
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    const reducedMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches
    if (!reducedMotion && apiOnline.value) {
      // 复用扫描激光 卡一半暂停
      authTransition.value = 'failed'
      await nextTick()
      await new Promise((resolve) => setTimeout(resolve, 400))
      authTransition.value = 'failed-stuck'
      await new Promise((resolve) => setTimeout(resolve, 800))
      authTransition.value = 'failed-return'
      await new Promise((resolve) => setTimeout(resolve, 480))
      authTransition.value = 'idle'
      await new Promise((resolve) => setTimeout(resolve, 60))
    }
    error.value = apiOnline.value ? getErrorMessage(cause, '密码错误，请检查账号和密码') : '后端未连接，请启动后端服务'
    authTransition.value = 'idle'
    isRouteTransitioning.value = false
    document.getElementById('route-card-handoff')?.replaceChildren()
  } finally {
    clearTimeout(timeout)
    loading.value = false
  }
}
</script>

<template>
  <div class="starfield-container pointer-events-none fixed inset-0 z-0 overflow-hidden">
    <div class="nebula nebula-1" />
    <div class="nebula nebula-2" />
    <DotField />
    <div class="cross-star cross-1" />
    <div class="cross-star cross-2" />
    <div class="cross-star cross-3" />
    <div class="orbit-line line-1" />
    <div class="orbit-line line-2" />
  </div>

  <div class="fixed top-0 right-0 left-0 z-10 border-t border-white/10">
    <span class="absolute top-3 left-8 font-mono text-[9px] tracking-widest text-text-secondary"
      >/ CONTROL ROOM / AUTH</span
    >
    <span class="absolute top-3 right-8 font-mono text-[9px] tracking-widest text-text-secondary"
      >SYS.V2.0 / NODE_01</span
    >
  </div>
  <div class="fixed right-0 bottom-0 left-0 z-10 border-b border-white/10">
    <span class="absolute bottom-3 left-8 font-mono text-[9px] tracking-widest text-text-secondary"
      >[ {{ now.toLocaleDateString('en-GB').replaceAll('/', '.') }} / PANEL
      {{ apiOnline ? 'CONNECTED' : 'OFFLINE' }} ]</span
    >
    <span class="absolute right-8 bottom-3 font-mono text-[9px] tracking-widest text-text-secondary"
      >SECURE CONNECTION / OK</span
    >
  </div>

  <div class="fixed top-8 right-8 z-50 flex items-center gap-2">
    <div ref="langSwitch" class="lang-switch flex items-center" :class="{ 'lang-open': languageOpen }">
      <button
        v-for="language in languages"
        :key="language.code"
        type="button"
        class="lang-btn border bg-background/50 px-3 py-2 font-mono text-[9px] tracking-widest backdrop-blur hover:border-brand hover:text-brand"
        :class="locale === language.code ? 'is-active border-brand text-brand' : 'border-border text-text-secondary'"
        :tabindex="languageOpen || locale === language.code ? 0 : -1"
        :aria-pressed="locale === language.code"
        @click="selectLanguage(language.code)"
      >
        {{ language.label }}
      </button>
    </div>
    <button
      ref="paletteTrigger"
      class="palette-trigger border border-border px-3 py-2 font-mono text-[9px] tracking-widest text-text-secondary hover:border-brand hover:text-brand"
      @click="paletteOpen = !paletteOpen"
    >
      ◒ PALETTE
    </button>
    <Transition name="palette-fade">
      <div v-if="paletteOpen" ref="palettePanel" class="palette-menu absolute top-12 right-0 w-64 p-5 shadow-2xl">
        <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">APPEARANCE</p>
        <div class="mb-4 space-y-1 border-b border-border pb-4">
          <button
            v-for="theme in themeOptions"
            :key="theme.value"
            type="button"
            class="flex w-full items-center gap-2 border border-transparent px-3 py-2 text-left font-mono text-[10px] text-text-secondary hover:bg-background hover:text-text-primary"
            :class="colorMode.preference === theme.value ? 'border-brand text-text-primary' : ''"
            @click="selectTheme(theme.value)"
          >
            ◌ {{ theme.label }}
          </button>
        </div>
        <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">CUSTOM COLORS</p>
        <div class="grid grid-cols-4 gap-3">
          <label
            v-for="field in colorFields"
            :key="field.variable"
            class="relative h-8 w-8 cursor-pointer overflow-hidden rounded-full border border-white/20 shadow-lg transition-transform hover:scale-110"
            ><input
              type="color"
              :value="customColors[field.key]"
              class="absolute inset-[-10px] h-12 w-12 cursor-pointer opacity-0"
              @input="applyCustomColor(field.variable, field.key, ($event.target as HTMLInputElement).value)" /><span
              class="pointer-events-none block h-full w-full rounded-full"
              :style="{ backgroundColor: customColors[field.key] }"
          /></label>
        </div>
      </div>
    </Transition>
  </div>

  <main
    class="relative z-10 flex min-h-screen items-center overflow-hidden bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-brand/10 via-transparent to-transparent px-8 py-16 text-text-primary"
  >
    <div class="mx-auto grid w-full max-w-7xl items-center gap-20 lg:grid-cols-[1fr_430px]">
      <section class="intro">
        <span class="font-mono text-xs tracking-[.2em] text-text-secondary">{{ t('authRequired') }}</span>
        <h1 class="mt-8 font-serif text-6xl leading-[.88] font-light tracking-tight text-text-primary md:text-8xl">
          <span class="hand-title text-text-primary">{{ t('titleEnter') }}</span
          ><br /><em class="sf-title text-text-primary">{{ t('titleAtmosphere') }}</em>
        </h1>
        <p class="mt-10 max-w-md text-sm leading-8 text-text-secondary">{{ t('desc1') }}<br />{{ t('desc2') }}</p>
      </section>
      <div class="login-transition-stage relative w-full max-w-md">
        <div
          class="login-ghost-frame"
          :class="{
            'is-splitting':
              authTransition === 'expanding' || authTransition === 'failed' || authTransition === 'failed-stuck',
          }"
          aria-hidden="true"
        />
        <div
          class="login-transition-outer"
          :class="{
            'is-expanding': authTransition === 'expanding',
            'is-failing': authTransition === 'failed' || authTransition === 'failed-stuck',
            'is-stuck': authTransition === 'failed-stuck',
            'is-returning': authTransition === 'failed-return',
          }"
        >
          <div class="login-scan-laser" aria-hidden="true" />
        </div>
        <div
          class="login-transition-inner"
          :class="{
            'is-dissolving':
              authTransition === 'expanding' || authTransition === 'failed' || authTransition === 'failed-stuck',
            'is-stuck': authTransition === 'failed-stuck',
            'is-returning': authTransition === 'failed-return',
          }"
        >
          <div class="login-glass-card">
            <form class="relative p-8 md:p-10" @submit.prevent="login">
              <div
                class="flex justify-between border-b border-border pb-5 font-mono text-xs tracking-[.16em] text-brand"
              >
                <span>ACCESS / LOGIN</span><span>01</span>
              </div>
              <label class="mt-9 block text-text-secondary"
                >{{ t('labelUsername')
                }}<input
                  v-model="username"
                  class="mt-3 w-full border-0 border-b border-border bg-transparent px-0 py-3 font-mono text-text-primary outline-none focus:border-brand"
                  placeholder="Atmo7"
              /></label>
              <label class="mt-7 block text-text-secondary"
                >{{ t('labelPassword') }}
                <div class="relative">
                  <input
                    v-model="password"
                    :type="showPassword ? 'text' : 'password'"
                    class="password-input mt-3 w-full border-0 border-b border-border bg-transparent px-0 py-3 pr-8 font-mono text-text-primary outline-none placeholder:text-text-secondary placeholder:opacity-40 focus:border-brand"
                    :placeholder="t('placeholderCredentials')"
                  /><button
                    type="button"
                    class="absolute top-[26px] right-1 text-text-secondary hover:text-brand"
                    @click="showPassword = !showPassword"
                  >
                    <Icon :icon="showPassword ? 'line-md:sunny-filled-loop' : 'line-md:moon-filled-loop'" width="18" />
                  </button></div
              ></label>
              <p
                class="mt-5 flex items-center gap-2 font-mono text-xs"
                :class="apiOnline ? 'api-online' : 'api-offline'"
              >
                <i class="status-hologram" />API {{ apiOnline ? t('apiConnected') : t('apiOffline') }}
              </p>
              <div class="login-error-slot" :class="{ 'is-open': Boolean(error) }">
                <div class="login-error-clip">
                  <p class="login-error-text mt-3 text-sm text-red-400">! {{ error }}</p>
                </div>
              </div>
              <button
                class="mt-6 inline-flex w-full items-center justify-between border border-brand/30 bg-transparent px-5 py-4 text-brand transition hover:border-brand hover:bg-brand/10 active:scale-[.99] disabled:opacity-50"
                :disabled="loading"
              >
                {{ loading ? t('btnLoading') : t('btnLogin') }}<span v-if="!loading">→</span
                ><span v-else class="h-4 w-4 animate-spin rounded-full border border-brand border-t-transparent" />
              </button>
              <p class="mt-6 font-mono text-[9px] leading-5 text-text-secondary">
                SESSION / HTTPONLY · SAME-SITE LAX<br />默认会话有效期 24 小时
              </p>
            </form>
          </div>
        </div>
        <p class="login-scan-error" :class="{ 'is-visible': authTransition === 'failed-stuck' }" aria-hidden="true">
          [ERROR]
        </p>
      </div>
    </div>
  </main>
</template>

<style scoped>
.login-glass-card {
  position: relative;
  isolation: isolate;
  padding: 2rem;
  background: rgba(0, 0, 0, 0.3);
  border-top: 1px solid rgba(255, 255, 255, 0.2);
  border-left: 1px solid rgba(255, 255, 255, 0.2);
  backdrop-filter: blur(16px);
  transition:
    transform 300ms ease,
    opacity 300ms ease;
}
.login-transition-stage {
  position: relative;
  min-height: 540px;
}
.login-transition-outer {
  position: absolute;
  inset: 0;
  z-index: 2;
  pointer-events: none;
  border: 1px solid rgba(255, 255, 255, 0.2);
  background: transparent;
  transition:
    clip-path 320ms ease,
    opacity 320ms ease;
}
.login-transition-inner {
  position: relative;
  z-index: 3;
  transition:
    opacity 320ms ease,
    transform 320ms ease,
    filter 320ms ease;
}
.login-transition-inner.is-dissolving {
  animation: login-inner-dissolve 120ms steps(1, end) forwards;
}
.login-transition-outer.is-expanding {
  animation: login-outer-erase 220ms linear forwards;
}
.login-transition-outer.is-expanding .login-scan-laser {
  animation: login-laser 220ms linear forwards;
}
.login-transition-stage {
  isolation: isolate;
}
.login-scan-laser {
  position: absolute;
  inset: 0 0 auto;
  height: 1px;
  background: rgba(255, 255, 255, 0.85);
  box-shadow: 0 0 15px 2px rgba(255, 255, 255, 0.7);
  opacity: 0;
  transition:
    opacity 240ms ease,
    transform 360ms cubic-bezier(0.22, 1, 0.36, 1);
}
.login-transition-outer.is-expanding {
  animation: login-outer-erase 800ms linear forwards;
}
.login-transition-outer.is-expanding .login-scan-laser {
  animation: login-laser 800ms linear forwards;
}
.login-transition-inner.is-dissolving {
  animation: login-inner-dissolve 400ms ease-out forwards;
}
/* 登录失败 复用 */
.login-transition-outer.is-failing {
  animation: login-outer-erase 800ms linear forwards;
}
.login-transition-outer.is-failing .login-scan-laser {
  animation: login-laser 800ms linear forwards;
}
.login-transition-outer.is-stuck,
.login-transition-inner.is-stuck {
  animation-play-state: paused;
}
.login-transition-outer.is-stuck .login-scan-laser {
  /* 钉在 270px */
  transform: translateY(270px) !important;
  opacity: 1 !important;
}
/* ERROR */
/* 与扫描线对齐 */
.login-scan-error {
  position: absolute;
  top: 271px;
  right: 0;
  left: 0;
  z-index: 5;
  pointer-events: none;
  text-align: center;
  font-family: var(--font-mono);
  font-size: 1.15rem;
  font-weight: 700;
  letter-spacing: 0.42em;
  transform: translateY(-50%);
  color: #f87171;
  text-shadow: 0 0 18px rgba(248, 113, 113, 0.45);
  opacity: 0;
  transition: opacity 220ms ease;
}
.login-scan-error.is-visible {
  opacity: 1;
  transition-delay: 120ms;
}
/* 平滑撑开 */
.login-error-slot {
  display: grid;
  grid-template-rows: 0fr;
  transition: grid-template-rows 340ms cubic-bezier(0.22, 1, 0.36, 1);
}
.login-error-slot.is-open {
  grid-template-rows: 1fr;
}
.login-error-clip {
  min-height: 0;
  overflow: hidden;
}
.login-error-text {
  opacity: 0;
  transform: translateY(-4px);
  transition:
    opacity 200ms ease,
    transform 240ms ease;
}
.login-error-slot.is-open .login-error-text {
  opacity: 1;
  transform: none;
  transition-delay: 90ms;
}
/* 自然归位 半溶解恢复成原样 */
.login-transition-outer.is-returning {
  animation: login-outer-return 480ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
.login-transition-inner.is-returning {
  animation: login-inner-return 480ms cubic-bezier(0.22, 1, 0.36, 1) forwards;
}
@keyframes login-outer-return {
  from {
    clip-path: inset(0 0 50% 0);
    opacity: 1;
  }
  to {
    clip-path: inset(0 0 0 0);
    opacity: 1;
  }
}
@keyframes login-inner-return {
  from {
    opacity: 0.15;
    transform: translateY(-22px);
    filter: blur(3px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
}
@keyframes login-outer-erase {
  0% {
    clip-path: inset(0 0 0 0);
    opacity: 1;
  }
  100% {
    clip-path: inset(0 0 100% 0);
    opacity: 0;
  }
}
@keyframes login-laser {
  0% {
    transform: translateY(0);
    opacity: 1;
  }
  100% {
    transform: translateY(540px);
    opacity: 0;
  }
}
@keyframes login-inner-dissolve {
  0% {
    opacity: 1;
    transform: translateY(0);
    filter: blur(0);
  }
  100% {
    opacity: 0.15;
    transform: translateY(-22px);
    filter: blur(3px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .login-transition-outer.is-expanding,
  .login-transition-inner.is-dissolving,
  .login-transition-outer.is-expanding .login-scan-laser {
    animation: none;
  }
}
/* 左上、右下拼成完整矩形 */
/* 扫描开始 拆开 向左上 / 右下悬浮 */
/* 这真帅吧 */
.login-ghost-frame {
  position: absolute;
  inset: 0;
  z-index: 4;
  pointer-events: none;
}
.login-ghost-frame::before,
.login-ghost-frame::after {
  content: '';
  position: absolute;
  inset: 0;
  border: 0 solid rgba(255, 255, 255, 0.05);
  transform: translate(10px, 10px);
  transition: transform 520ms cubic-bezier(0.22, 1, 0.36, 1);
}
.login-ghost-frame::before {
  border-top-width: 1px;
  border-left-width: 1px;
}
.login-ghost-frame::after {
  border-right-width: 1px;
  border-bottom-width: 1px;
}
.login-ghost-frame.is-splitting::before {
  /* 与右下角保持一致的 34px 距离 */
  /* 左上角的额外距离 */
  transform: translate(-34px, -34px);
}
.login-ghost-frame.is-splitting::after {
  transform: translate(34px, 34px);
}
.starfield-container {
  background: var(--background);
}
.nebula {
  position: absolute;
  width: 48vw;
  height: 48vw;
  border-radius: 50%;
  filter: blur(80px);
  opacity: 0.08;
  animation: nebula-pulse 18s ease-in-out infinite;
}
.nebula-1 {
  left: 5%;
  top: 8%;
  background: var(--brand);
}
.nebula-2 {
  right: 2%;
  bottom: -15%;
  background: var(--surface);
  animation-delay: -8s;
}
.cross-star {
  position: absolute;
  width: 22px;
  height: 22px;
  color: var(--brand);
  opacity: 0.45;
  animation: float-cross 9s ease-in-out infinite;
}
.cross-star::before,
.cross-star::after {
  content: '';
  position: absolute;
  background: currentColor;
}
.cross-star::before {
  width: 100%;
  height: 1px;
  top: 50%;
  left: 0;
}
.cross-star::after {
  height: 100%;
  width: 1px;
  left: 50%;
  top: 0;
}
.cross-1 {
  left: 12%;
  top: 22%;
}
.cross-2 {
  right: 21%;
  top: 30%;
  animation-delay: -3s;
}
.cross-3 {
  left: 46%;
  bottom: 17%;
  animation-delay: -6s;
}
.orbit-line {
  position: absolute;
  height: 1px;
  width: 70%;
  background: linear-gradient(90deg, transparent, var(--brand), transparent);
  opacity: 0.12;
  mask-image: linear-gradient(90deg, transparent, #000 20%, #000 80%, transparent);
  animation: line-drift 24s ease-in-out infinite;
}
.line-1 {
  left: -8%;
  top: 38%;
  transform: rotate(-17deg);
}
.line-2 {
  right: -10%;
  bottom: 27%;
  transform: rotate(13deg);
  animation-delay: -10s;
}
.hand-title {
  font-style: italic;
  letter-spacing: -0.04em;
  display: inline-block;
  clip-path: inset(0 100% 0 0);
  animation: hand-write 1.2s cubic-bezier(0.65, 0, 0.35, 1) forwards;
}
.sf-title {
  font-family:
    'SF Pro Display',
    'SF Pro Text',
    -apple-system,
    BlinkMacSystemFont,
    'Segoe UI',
    sans-serif;
  font-style: italic;
  letter-spacing: -0.05em;
  display: inline-block;
  clip-path: inset(0 100% 0 0);
  animation: hand-write 1.4s 0.2s cubic-bezier(0.65, 0, 0.35, 1) forwards;
}
@keyframes hand-write {
  99% {
    clip-path: inset(0 0 0 0);
  }
  to {
    clip-path: none;
  }
}
@keyframes nebula-pulse {
  50% {
    opacity: 0.13;
    transform: scale(1.04);
  }
}
@keyframes float-cross {
  50% {
    transform: translate(5px, -4px) scale(1.08);
  }
}
@keyframes line-drift {
  50% {
    transform: translate(8px, -5px) rotate(-17deg);
    opacity: 0.3;
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
.lang-switch {
  gap: 0;
}
.lang-switch.lang-open {
  gap: 0.5rem;
}
.lang-btn {
  max-width: 8em;
  white-space: nowrap;
  overflow: hidden;
  transition:
    max-width 220ms ease,
    opacity 220ms ease,
    padding-left 220ms ease,
    padding-right 220ms ease,
    border-color 220ms ease,
    color 220ms ease;
}
.lang-switch:not(.lang-open) .lang-btn:not(.is-active) {
  max-width: 0;
  opacity: 0;
  padding-left: 0;
  padding-right: 0;
  border-color: transparent;
  pointer-events: none;
}
/* 隐藏 Edge / IE 自带的密码显示按钮，只保留自定义的太阳 / 月亮切换 */
.password-input::-ms-reveal,
.password-input::-ms-clear {
  display: none;
}
</style>
<style scoped>
.status-hologram {
  display: inline-block;
  width: 6px;
  height: 6px;
  border-radius: 50%;
  background: currentColor;
  box-shadow: 0 0 8px currentColor;
  animation: hologram-pulse 1.4s ease-in-out infinite;
}
.api-online {
  color: var(--data-live);
}
.api-offline {
  color: #f87171;
}
@keyframes hologram-pulse {
  50% {
    opacity: 0.35;
    transform: scale(0.72);
    box-shadow: 0 0 2px currentColor;
  }
}
</style>
