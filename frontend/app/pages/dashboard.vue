<script setup lang="ts">
import PanelPreferences from '~/components/admin/PanelPreferences.vue'
import UserManagement from '~/components/admin/UserManagement.vue'
import AboutPanel from '~/components/admin/AboutPanel.vue'
import ScheduleManager from '~/components/admin/ScheduleManager.vue'
import BatchOperations from '~/components/admin/BatchOperations.vue'
import LoginAlert from '~/components/admin/LoginAlert.vue'
import DashboardBackground from '~/components/ui/DashboardBackground.vue'

definePageMeta({ middleware: 'auth' })

const { t } = useI18n()
const seam = useRouteSeam()
// 仅在从登录页成功进入时播放入场淡入
const enteringFromLogin = seam.value.phase === 'away' || seam.value.phase === 'clearing'

const mainTabs = [
  { key: 'dashboard', icon: '◈', labelKey: 'tabDashboard' },
  { key: 'instances', icon: '✦', labelKey: 'tabInstances' },
  { key: 'users', icon: '◉', labelKey: 'tabUsers' },
  { key: 'settings', icon: '◐', labelKey: 'tabSettings' },
  { key: 'about', icon: '◇', labelKey: 'tabAbout' },
] as const
type Tab = (typeof mainTabs)[number]['key']

const activeTab = ref<Tab>('dashboard')
const preferences = useState<Record<string, unknown>>('panel-preferences', () => ({}))

// 主标签高亮：每个标签用左右内边距占住自己的「格」（pl/pr 各 16px，
// 总间距与原 gap-8 的 32px 一致），高亮线就是标签实际占据的空间，相邻格首尾相接
const navEl = ref<HTMLElement | null>(null)
const indicatorStyle = ref({ left: '0px', width: '0px' })
let navObserver: ResizeObserver | undefined

function updateIndicator() {
  const nav = navEl.value
  if (!nav) return
  const buttons = Array.from(nav.querySelectorAll<HTMLElement>('[data-tab]'))
  const index = buttons.findIndex((button) => button.dataset.tab === activeTab.value)
  const button = buttons[index]
  if (!button) return
  // 高亮线基于标签实际占据的空间绘制
  indicatorStyle.value = { left: `${button.offsetLeft}px`, width: `${button.offsetWidth}px` }
}

watch(activeTab, () => nextTick(updateIndicator))

const settingsTabs = [
  { key: 'system', labelKey: 'settingsSystem', code: 'SYSTEM' },
  { key: 'basic', labelKey: 'settingsBasic', code: 'BASIC' },
  { key: 'schedule', labelKey: 'settingsCron', code: 'CRON' },
] as const
type SettingsTab = (typeof settingsTabs)[number]['key']

const activeSettings = ref<SettingsTab>('system')
const activeSettingsTab = computed(
  () => settingsTabs.find((item) => item.key === activeSettings.value) ?? settingsTabs[0],
)

const placeholder = computed(() => {
  const tab = activeTab.value
  if (tab === 'settings') return { title: t(activeSettingsTab.value.labelKey), code: activeSettingsTab.value.code }
  if (tab === 'users') return { title: t('tabUsers'), code: 'USERS' }
  if (tab === 'about') return { title: t('tabAbout'), code: 'ABOUT' }
  return null
})
const instances = ref<import('~/types').InstanceData[]>([])
const { request } = useApi()
const host = ref({
  cpu: 0,
  memory: 0,
  cores: [] as number[],
  platform: t('msg_loading'),
  hostname: t('msg_loading'),
  release: t('msg_loading'),
  panel: 'ATMOSPHERE / 02',
})
let timer: ReturnType<typeof setInterval> | undefined

async function loadInstances() {
  try {
    const response = await request<{ instances?: import('~/types').InstanceData[] }>('/api/instances')
    instances.value = response.instances ?? []
  } catch {
    instances.value = []
  }
}

async function loadHostMetrics() {
  try {
    host.value = await request('/api/instances/system/metrics')
  } catch {
    host.value = { ...host.value, platform: 'UNAVAILABLE', hostname: 'UNAVAILABLE', release: 'UNAVAILABLE' }
  }
}

// 面板与实例监测共用采样间隔设置。
function startPolling() {
  if (timer) clearInterval(timer)
  timer = setInterval(
    () => {
      loadInstances()
      loadHostMetrics()
    },
    Number(preferences.value.metrics_interval_seconds || 5) * 1000,
  )
}
watch(() => preferences.value.metrics_interval_seconds, startPolling)
onMounted(() => {
  loadInstances()
  loadHostMetrics()
  startPolling()
  updateIndicator()
  navObserver = new ResizeObserver(updateIndicator)
  if (navEl.value) navObserver.observe(navEl.value)
  document.fonts.ready.then(updateIndicator)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  navObserver?.disconnect()
})

const summary = computed(() => [
  {
    label: 'ACTIVE INSTANCES',
    value: String(instances.value.filter((item) => item.status === 'running').length).padStart(2, '0'),
    note: t('summaryNoteInstances'),
  },
  { label: 'DEPLOYMENT MODE', value: 'JAR', note: t('summaryNoteDeploy') },
  { label: 'SESSION', value: String(preferences.value.session_hours || 24), note: t('summaryNoteSession') },
])
</script>

<template>
  <div class="min-h-screen">
    <DashboardBackground />
    <main class="relative z-10 mx-auto max-w-7xl px-8 py-14" :class="{ 'dashboard-enter': enteringFromLogin }">
      <header class="border-b border-border pb-8">
        <div class="flex items-end justify-between gap-8">
          <div>
            <p class="mb-6 font-mono text-xs tracking-[0.2em] text-text-secondary">/ CONTROL ROOM / AUTHORIZED</p>
            <h1 class="font-serif text-6xl leading-none font-light tracking-tight md:text-8xl">
              <span class="block text-text-primary">Server</span>
              <span class="mt-2 block text-brand italic">instances.</span>
            </h1>
          </div>
          <button
            type="button"
            class="mb-2 border border-brand px-4 py-3 font-mono text-xs text-text-primary hover:bg-brand hover:text-background"
            @click="navigateTo('/deploy')"
          >
            [ + NEW INSTANCE ]
          </button>
        </div>
      </header>

      <nav ref="navEl" class="relative mt-8 flex border-b border-border font-mono text-sm">
        <button
          v-for="tab in mainTabs"
          :key="tab.key"
          type="button"
          :data-tab="tab.key"
          class="pr-[18px] pb-3 pl-[14px]"
          :class="activeTab === tab.key ? 'text-text-primary' : 'text-text-secondary hover:text-text-primary'"
          @click="activeTab = tab.key"
        >
          {{ tab.icon }} {{ t(tab.labelKey) }}
        </button>
        <span class="tab-highlight" :style="indicatorStyle" aria-hidden="true" />
      </nav>

      <!-- 设置子项：主标签切到「设置」时展开一行；横线与子项都从左侧生长出来，下方面板随之平滑下移 -->
      <div
        class="grid transition-[grid-template-rows] duration-[320ms] ease-out"
        :class="activeTab === 'settings' ? 'grid-rows-[1fr]' : 'grid-rows-[0fr]'"
      >
        <div class="overflow-hidden">
          <div
            class="settings-subnav flex gap-6 border-b border-border pt-3 pb-4 pl-[10px] font-mono text-xs"
            :class="{ 'is-visible': activeTab === 'settings' }"
            :aria-hidden="activeTab !== 'settings'"
          >
            <button
              v-for="item in settingsTabs"
              :key="item.key"
              type="button"
              :class="activeSettings === item.key ? 'text-brand' : 'text-text-secondary hover:text-text-primary'"
              :tabindex="activeTab === 'settings' ? 0 : -1"
              @click="activeSettings = item.key"
            >
              {{ t(item.labelKey) }}
            </button>
          </div>
        </div>
      </div>

      <LoginAlert />
      <Transition name="dashboard-panel" mode="out-in">
        <section v-if="activeTab === 'dashboard'" key="dashboard" class="mt-10 space-y-6">
          <div class="grid gap-8 md:grid-cols-3">
            <AtmosphereCard v-for="item in summary" :key="item.label" class="p-8">
              <div>
                <p class="font-mono text-[10px] tracking-[0.2em] text-text-secondary">{{ item.label }}</p>
                <strong class="mt-5 block font-mono text-3xl text-text-primary">{{ item.value }}</strong
                ><small class="mt-2 block text-xs text-text-secondary">{{ item.note }}</small>
              </div>
            </AtmosphereCard>
          </div>

          <div class="grid gap-8 lg:grid-cols-[1.2fr_0.8fr]">
            <AtmosphereCard class="p-8">
              <div>
                <header class="flex items-center justify-between pb-4">
                  <div>
                    <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ LIVE READOUT</p>
                    <h2 class="mt-2 font-serif text-2xl text-text-primary">{{ t('hostTelemetryTitle') }}</h2>
                  </div>
                  <span class="font-mono text-[10px] text-data-live">● LIVE / 5S</span>
                </header>
                <div class="mt-7 grid gap-8 md:grid-cols-2">
                  <div>
                    <div class="flex items-end justify-between">
                      <span class="font-mono text-[10px] tracking-[0.16em] text-text-secondary">CPU LOAD</span
                      ><strong class="font-mono text-2xl text-text-primary">{{ host.cpu.toFixed(1) }}%</strong>
                    </div>
                    <div class="mt-4 h-2 overflow-hidden bg-background">
                      <div class="metric-line h-full bg-brand" :style="{ width: host.cpu + '%' }" />
                    </div>
                    <div class="mt-5 grid grid-cols-4 gap-2">
                      <i v-for="(core, index) in host.cores" :key="index" class="block h-16 p-1"
                        ><span
                          class="block h-full bg-brand/70 transition-all duration-700"
                          :style="{
                            transform: 'scaleY(' + Math.max(0.08, core / 100) + ')',
                            transformOrigin: 'bottom',
                          }"
                        /><small class="mt-1 block font-mono text-[8px] text-text-secondary">C{{ index + 1 }}</small></i
                      >
                    </div>
                  </div>
                  <div>
                    <div class="flex items-end justify-between">
                      <span class="font-mono text-[10px] tracking-[0.16em] text-text-secondary">MEMORY LOAD</span
                      ><strong class="font-mono text-2xl text-text-primary">{{ host.memory.toFixed(1) }}%</strong>
                    </div>
                    <div class="mt-4 h-2 overflow-hidden bg-background">
                      <div class="metric-line h-full bg-data-live" :style="{ width: host.memory + '%' }" />
                    </div>
                    <p class="mt-6 font-mono text-xs text-text-secondary">{{ t('samplingNote') }}</p>
                  </div>
                </div>
              </div>
            </AtmosphereCard>

            <AtmosphereCard class="p-8">
              <div>
                <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ NODE PROFILE</p>
                <h2 class="mt-2 font-serif text-2xl text-text-primary">{{ t('hostIdentityTitle') }}</h2>
                <dl class="mt-7 font-mono text-xs">
                  <div class="flex justify-between border-b border-white/10 py-4 last:border-b-0">
                    <dt class="text-text-secondary">PANEL VERSION</dt>
                    <dd class="text-text-primary">{{ host.panel }}</dd>
                  </div>
                  <div class="flex justify-between border-b border-white/10 py-4 last:border-b-0">
                    <dt class="text-text-secondary">PLATFORM</dt>
                    <dd class="text-text-primary">{{ host.platform }}</dd>
                  </div>
                  <div class="flex justify-between border-b border-white/10 py-4 last:border-b-0">
                    <dt class="text-text-secondary">HOSTNAME</dt>
                    <dd class="text-text-primary">{{ host.hostname }}</dd>
                  </div>
                  <div class="flex justify-between border-b border-white/10 py-4 last:border-b-0">
                    <dt class="text-text-secondary">RELEASE</dt>
                    <dd class="max-w-[12rem] truncate text-right text-text-primary">{{ host.release }}</dd>
                  </div>
                </dl>
              </div>
            </AtmosphereCard>
          </div>
        </section>

        <section v-else-if="activeTab === 'instances'" key="instances" class="mt-10">
          <AtmosphereCard v-if="!instances.length" class="dashboard-card py-32 text-center">
            <span class="font-mono text-xs tracking-[0.3em] text-brand">[ 00 / 00 ]</span>
            <h2 class="mt-6 font-mono text-lg tracking-[0.35em] text-text-primary">{{ t('emptyInstancesTitle') }}</h2>
            <p class="mt-4 text-xs text-text-secondary">{{ t('emptyInstancesDesc') }}</p>
          </AtmosphereCard>
          <div v-else class="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3">
            <NuxtLink v-for="item in instances" :key="item.id" :to="`/instances/${item.id}`"
              ><AtmosphereCard
                ><div class="flex items-start justify-between">
                  <h2 class="font-mono text-lg font-bold text-text-primary">{{ item.name }}</h2>
                  <span
                    class="h-2 w-2 rounded-full"
                    :class="
                      item.status === 'running'
                        ? 'animate-pulse bg-data-live shadow-[0_0_12px_var(--data-live)]'
                        : 'bg-red-400 shadow-[0_0_10px_rgba(248,113,113,.45)]'
                    "
                  />
                </div>
                <p class="mt-8 font-mono text-xs text-text-secondary">
                  {{ item.selected_core || 'Minecraft Server' }} · PORT {{ item.port }}
                </p>
                <span class="mt-5 block font-mono text-[10px] tracking-[0.16em] text-brand"
                  >[ ACCESS ]</span
                ></AtmosphereCard
              ></NuxtLink
            >
          </div>
        </section>

        <section
          v-else-if="activeTab === 'settings' && (activeSettings === 'system' || activeSettings === 'basic')"
          :key="'settings-' + activeSettings"
          class="mt-10"
        >
          <PanelPreferences :section="activeSettings" />
          <BatchOperations v-if="activeSettings === 'system'" class="mt-6" />
        </section>
        <section v-else-if="activeTab === 'users'" key="users" class="mt-10"><UserManagement /></section>
        <section v-else-if="activeTab === 'settings' && activeSettings === 'schedule'" key="schedule" class="mt-10">
          <ScheduleManager />
        </section>

        <section v-else-if="activeTab === 'about'" key="about" class="mt-10">
          <AboutPanel :version="host.panel" />
        </section>

        <section v-else-if="placeholder" :key="activeTab" class="mt-10">
          <AtmosphereCard class="dashboard-card py-32 text-center">
            <span class="font-mono text-xs tracking-[0.3em] text-brand">[ {{ placeholder.code }} / PENDING ]</span>
            <h2 class="mt-6 font-mono text-lg tracking-[0.35em] text-text-primary">{{ placeholder.title }}</h2>
            <p class="mt-4 text-xs text-text-secondary">{{ t('pending') }}</p>
          </AtmosphereCard>
        </section>
      </Transition>
    </main>
  </div>
</template>

<style scoped>
.dashboard-enter {
  /* 完全透明后入场 */
  animation: dashboard-enter 700ms cubic-bezier(0.22, 1, 0.36, 1) 320ms both;
}
@keyframes dashboard-enter {
  from {
    opacity: 0;
    transform: translateY(14px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
.dashboard-panel-enter-active,
.dashboard-panel-leave-active {
  transition:
    opacity 260ms ease,
    transform 260ms ease;
}
.dashboard-panel-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.dashboard-panel-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
.dashboard-card {
  transition:
    transform 320ms cubic-bezier(0.22, 1, 0.36, 1),
    border-color 260ms ease,
    background-color 260ms ease;
}
.dashboard-card:hover {
  transform: translateY(-3px);
  border-color: color-mix(in srgb, var(--brand) 55%, transparent);
}
.metric-line {
  transition: width 900ms cubic-bezier(0.22, 1, 0.36, 1);
}
/* 主标签高亮：高亮线 = 标签实际占据的格，切换时左右滑动 */
.tab-highlight {
  position: absolute;
  bottom: -1px;
  height: 2px;
  background: var(--brand);
  pointer-events: none;
  transition:
    left 380ms cubic-bezier(0.22, 1, 0.36, 1),
    width 380ms cubic-bezier(0.22, 1, 0.36, 1);
}
/* 设置子项：横线与文字一起从左往右生长 */
.settings-subnav {
  clip-path: inset(0 100% 0 0);
  transition: clip-path 480ms cubic-bezier(0.22, 1, 0.36, 1);
}
.settings-subnav.is-visible {
  clip-path: inset(0 0 0 0);
}
</style>
