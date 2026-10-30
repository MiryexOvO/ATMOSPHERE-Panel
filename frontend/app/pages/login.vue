<script setup lang="ts">
import { Icon } from '@iconify/vue'


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
const customColors = ref({ textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' })
const colorFields = [{ label: 'TEXT1', variable: 'text-primary', key: 'textPrimary' }, { label: 'TEXT2', variable: 'text-secondary', key: 'textSecondary' }, { label: 'UI COLOR', variable: 'surface', key: 'surface' }, { label: 'BACKGROUND', variable: 'background', key: 'background' }] as const
const themeOptions = [{ label: 'SYSTEM', value: 'system' }, { label: 'DARK', value: 'dark' }, { label: 'LIGHT', value: 'light' }] as const
function selectTheme(value: 'system' | 'dark' | 'light') {
  colorMode.preference = value
  localStorage.removeItem('custom-theme')
  const colors = value === 'light' ? { textPrimary: '#17233a', textSecondary: '#59636b', surface: '#fffdf7', background: '#e9e4d8' } : { textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' }
  customColors.value = colors
  for (const field of colorFields) document.documentElement.style.setProperty('--' + field.variable, colors[field.key])
  document.documentElement.style.setProperty('--brand', colors.textPrimary)
}
const { t, locale, setLocale } = useI18n()
const languages = [{ code: 'zh', label: 'ZH' }, { code: 'en', label: 'EN' }, { code: 'ja', label: 'JA' }] as const
type LocaleCode = typeof languages[number]['code']
function changeLocale(code: string) {
  if (languages.some((language) => language.code === code)) setLocale(code as LocaleCode)
}
const languageOpen = ref(false)
const langSwitch = ref<HTMLElement | null>(null)
function selectLanguage(code: LocaleCode) {
  if (!languageOpen.value) {
    languageOpen.value = true
    return
  }
  changeLocale(code)
  languageOpen.value = false
}
function closeLanguage(event: MouseEvent) {
  if (!languageOpen.value) return
  const node = event.target as Node | null
  if (node && langSwitch.value && !langSwitch.value.contains(node)) languageOpen.value = false
}
let timer: ReturnType<typeof setInterval> | undefined

onMounted(() => {
  timer = setInterval(() => { now.value = new Date() }, 1000)
  document.addEventListener('click', closeLanguage)
  const saved = localStorage.getItem('custom-theme')
  if (saved) { try { customColors.value = JSON.parse(saved) } catch {} }
  for (const field of colorFields) document.documentElement.style.setProperty(`--${field.variable}`, customColors.value[field.key])
  document.documentElement.style.setProperty('--brand', customColors.value.textPrimary)
})
function saveToLocalStorage() { localStorage.setItem('custom-theme', JSON.stringify(customColors.value)) }
function applyCustomColor(variable: string, key: keyof typeof customColors.value, value: string) { customColors.value[key] = value; document.documentElement.style.setProperty(`--${variable}`, value); if (key === 'textPrimary') document.documentElement.style.setProperty('--brand', value); saveToLocalStorage() }
onUnmounted(() => {
  if (timer) clearInterval(timer)
  document.removeEventListener('click', closeLanguage)
})

async function login() {
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
    await request('/api/login', { method: 'POST', timeout: 8000, body: { username: username.value, password: password.value } })
    await navigateTo('/dashboard')
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = apiOnline.value ? (getErrorMessage(cause, '密码错误，请检查账号和密码')) : '后端未连接，请启动后端服务'
  } finally {
    clearTimeout(timeout)
    loading.value = false
  }
}
</script>

<template>
  <div class="starfield-container fixed inset-0 z-0 pointer-events-none overflow-hidden">
    <div class="nebula nebula-1" />
    <div class="nebula nebula-2" />
    <div class="stars-layer stars-sm" />
    <div class="stars-layer stars-lg" />
    <div class="cross-star cross-1" />
    <div class="cross-star cross-2" />
    <div class="cross-star cross-3" />
    <div class="orbit-line line-1" />
    <div class="orbit-line line-2" />
  </div>

  <div class="fixed top-0 left-0 right-0 z-10 border-t border-white/10">
    <span class="absolute left-8 top-3 font-mono text-[9px] tracking-widest text-text-secondary">/ CONTROL ROOM / AUTH</span>
    <span class="absolute right-8 top-3 font-mono text-[9px] tracking-widest text-text-secondary">SYS.V2.0 / NODE_01</span>
  </div>
  <div class="fixed bottom-0 left-0 right-0 z-10 border-b border-white/10">
    <span class="absolute bottom-3 left-8 font-mono text-[9px] tracking-widest text-text-secondary">[ {{ now.toLocaleDateString('en-GB').replaceAll('/', '.') }} / PANEL {{ apiOnline ? 'CONNECTED' : 'OFFLINE' }} ]</span>
    <span class="absolute bottom-3 right-8 font-mono text-[9px] tracking-widest text-text-secondary">SECURE CONNECTION / OK</span>
  </div>

  <div class="fixed right-8 top-8 z-50 flex items-center gap-2">
    <div ref="langSwitch" class="lang-switch flex items-center" :class="{ 'lang-open': languageOpen }">
      <button v-for="language in languages" :key="language.code" type="button" class="lang-btn border bg-background/50 px-3 py-2 font-mono text-[9px] tracking-widest backdrop-blur hover:border-brand hover:text-brand" :class="locale === language.code ? 'is-active border-brand text-brand' : 'border-border text-text-secondary'" :tabindex="languageOpen || locale === language.code ? 0 : -1" :aria-pressed="locale === language.code" @click="selectLanguage(language.code)">{{ language.label }}</button>
    </div>
    <button class="palette-trigger border border-border px-3 py-2 font-mono text-[9px] tracking-widest text-text-secondary hover:border-brand hover:text-brand" @click="paletteOpen = !paletteOpen">◒ PALETTE</button>
    <Transition name="palette-fade">
      <div v-if="paletteOpen" class="palette-menu absolute right-0 top-12 w-64 border border-border bg-surface p-5 shadow-2xl">
        <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">APPEARANCE</p>
        <div class="mb-4 space-y-1 border-b border-border pb-4">
          <button v-for="theme in themeOptions" :key="theme.value" type="button" class="flex w-full items-center gap-2 border border-transparent px-3 py-2 text-left font-mono text-[10px] text-text-secondary hover:bg-background hover:text-text-primary" :class="colorMode.preference === theme.value ? 'border-brand text-text-primary' : ''" @click="selectTheme(theme.value)">◌ {{ theme.label }}</button>
        </div>
        <p class="mb-3 font-mono text-[9px] tracking-[0.2em] text-text-secondary">CUSTOM COLORS</p>
        <div class="grid grid-cols-4 gap-3">
          <label v-for="field in colorFields" :key="field.variable" class="relative h-8 w-8 cursor-pointer overflow-hidden rounded-full border border-white/20 shadow-lg transition-transform hover:scale-110"><input type="color" :value="customColors[field.key]" class="absolute inset-[-10px] h-12 w-12 cursor-pointer opacity-0" @input="applyCustomColor(field.variable, field.key, ($event.target as HTMLInputElement).value)"><span class="pointer-events-none block h-full w-full rounded-full" :style="{backgroundColor: customColors[field.key]}" /></label>
        </div>
      </div>
    </Transition>
  </div>

  <main class="relative z-10 flex min-h-screen items-center overflow-hidden bg-[radial-gradient(ellipse_at_center,_var(--tw-gradient-stops))] from-brand/10 via-transparent to-transparent px-8 py-16 text-text-primary">
    <div class="mx-auto grid w-full max-w-7xl items-center gap-20 lg:grid-cols-[1fr_430px]">
      <section class="intro">
        <span class="font-mono text-xs tracking-[.2em] text-text-secondary">{{ t('authRequired') }}</span>
        <h1 class="mt-8 font-serif text-6xl font-light leading-[.88] tracking-tight text-text-primary md:text-8xl"><span class="hand-title text-text-primary">{{ t('titleEnter') }}</span><br><em class="sf-title text-text-primary">{{ t('titleAtmosphere') }}</em></h1>
        <p class="mt-10 max-w-md text-sm leading-8 text-text-secondary">{{ t('desc1') }}<br>{{ t('desc2') }}</p>
      </section>
      <div class="relative w-full max-w-md">
        <div class="pointer-events-none absolute inset-0 translate-x-3 translate-y-3 border border-border bg-black/20 dark:bg-black/40" />
        <form class="auth-card relative border-l border-t border-border bg-surface/80 p-9 shadow-2xl" @submit.prevent="login">
          <div class="flex justify-between border-b border-border pb-5 font-mono text-xs tracking-[.16em] text-brand"><span>ACCESS / LOGIN</span><span>01</span></div>
          <label class="mt-9 block text-text-secondary">{{ t('labelUsername') }}<input v-model="username" class="mt-3 w-full border-0 border-b border-border bg-transparent px-0 py-3 font-mono text-text-primary outline-none focus:border-brand" placeholder="Atmo7"></label>
          <label class="mt-7 block text-text-secondary">{{ t('labelPassword') }}<div class="relative"><input v-model="password" :type="showPassword ? 'text' : 'password'" class="mt-3 w-full border-0 border-b border-border bg-transparent px-0 py-3 pr-8 font-mono text-text-primary outline-none placeholder:text-text-secondary placeholder:opacity-40 focus:border-brand" :placeholder="t('placeholderCredentials')"><button type="button" class="absolute right-1 top-[26px] text-text-secondary hover:text-brand" @click="showPassword=!showPassword"><Icon :icon="showPassword ? 'line-md:sunny-filled-loop' : 'line-md:moon-filled-loop'" width="18" /></button></div></label>
          <p class="mt-5 flex items-center gap-2 font-mono text-xs" :class="apiOnline ? 'api-online' : 'api-offline'"><i class="status-hologram" />API {{ apiOnline ? t('apiConnected') : t('apiOffline') }}</p>
          <p v-if="error" class="mt-3 text-sm text-red-400">! {{ error }}</p>
          <button class="mt-6 inline-flex w-full items-center justify-between border border-brand/30 bg-transparent px-5 py-4 text-brand transition hover:border-brand hover:bg-brand/10 active:scale-[.99] disabled:opacity-50" :disabled="loading">{{ loading ? t('btnLoading') : t('btnLogin') }}<span v-if="!loading">→</span><span v-else class="h-4 w-4 animate-spin rounded-full border border-brand border-t-transparent" /></button>
          <p class="mt-6 font-mono text-[9px] leading-5 text-text-secondary">SESSION / HTTPONLY · SAME-SITE LAX<br>默认会话有效期 24 小时</p>
        </form>
      </div>
    </div>
  </main>
</template>

<style scoped>
.starfield-container{background:var(--background)}
.nebula{position:absolute;width:48vw;height:48vw;border-radius:50%;filter:blur(80px);opacity:.08;animation:nebula-pulse 18s ease-in-out infinite}.nebula-1{left:5%;top:8%;background:var(--brand)}.nebula-2{right:2%;bottom:-15%;background:var(--surface);animation-delay:-8s}
.stars-layer{position:absolute;inset:0}.stars-sm{opacity:.5;background:radial-gradient(circle,var(--text-primary) 0 1px,transparent 1.5px);background-size:83px 71px;animation:twinkle 9s ease-in-out infinite}.stars-lg{opacity:.55;background:radial-gradient(circle,var(--brand) 0 1.5px,transparent 2px);background-size:211px 193px;animation:twinkle 13s ease-in-out infinite reverse}
.cross-star{position:absolute;width:22px;height:22px;color:var(--brand);opacity:.45;animation:float-cross 9s ease-in-out infinite}.cross-star::before,.cross-star::after{content:'';position:absolute;background:currentColor}.cross-star::before{width:100%;height:1px;top:50%;left:0}.cross-star::after{height:100%;width:1px;left:50%;top:0}.cross-1{left:12%;top:22%}.cross-2{right:21%;top:30%;animation-delay:-3s}.cross-3{left:46%;bottom:17%;animation-delay:-6s}
.orbit-line{position:absolute;height:1px;width:70%;background:linear-gradient(90deg,transparent,var(--brand),transparent);opacity:.12;mask-image:linear-gradient(90deg,transparent,#000 20%,#000 80%,transparent);animation:line-drift 24s ease-in-out infinite}.line-1{left:-8%;top:38%;transform:rotate(-17deg)}.line-2{right:-10%;bottom:27%;transform:rotate(13deg);animation-delay:-10s}
.hand-title{font-style:italic;letter-spacing:-.04em;display:inline-block;clip-path:inset(0 100% 0 0);animation:hand-write 1.2s cubic-bezier(.65,0,.35,1) forwards}.sf-title{font-family:'SF Pro Display','SF Pro Text',-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif;font-style:italic;letter-spacing:-.05em;display:inline-block;clip-path:inset(0 100% 0 0);animation:hand-write 1.4s .2s cubic-bezier(.65,0,.35,1) forwards}
@keyframes hand-write{99%{clip-path:inset(0 0 0 0)}to{clip-path:none}}@keyframes nebula-pulse{50%{opacity:.13;transform:scale(1.04)}}@keyframes twinkle{50%{opacity:.22}}@keyframes float-cross{50%{transform:translate(5px,-4px) scale(1.08)}}@keyframes line-drift{50%{transform:translate(8px,-5px) rotate(-17deg);opacity:.3}}
.palette-fade-enter-active,.palette-fade-leave-active{transition:opacity 180ms ease,transform 180ms ease}.palette-fade-enter-from,.palette-fade-leave-to{opacity:0;transform:translateY(-8px) scale(.98)}
.lang-switch{gap:0}.lang-switch.lang-open{gap:.5rem}
.lang-btn{max-width:8em;white-space:nowrap;overflow:hidden;transition:max-width 220ms ease,opacity 220ms ease,padding-left 220ms ease,padding-right 220ms ease,border-color 220ms ease,color 220ms ease}
.lang-switch:not(.lang-open) .lang-btn:not(.is-active){max-width:0;opacity:0;padding-left:0;padding-right:0;border-color:transparent;pointer-events:none}
</style>
<style scoped>
.status-hologram{display:inline-block;width:6px;height:6px;border-radius:50%;background:currentColor;box-shadow:0 0 8px currentColor;animation:hologram-pulse 1.4s ease-in-out infinite}.api-online{color:var(--data-live)}.api-offline{color:#f87171}@keyframes hologram-pulse{50%{opacity:.35;transform:scale(.72);box-shadow:0 0 2px currentColor}}
</style>