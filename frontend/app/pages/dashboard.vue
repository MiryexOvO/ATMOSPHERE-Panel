<script setup lang="ts">

import DashboardBackground from '~/components/ui/DashboardBackground.vue'

definePageMeta({ middleware: 'auth' })

const activeTab = ref<'dashboard' | 'instances'>('dashboard')
const instances = ref<import("~/types").InstanceData[]>([])
const { request } = useApi()
const host = ref({ cpu: 0, memory: 0, cores: [] as number[], platform: '读取中', hostname: '读取中', release: '读取中', panel: 'ATMOSPHERE / 02' })
let timer: ReturnType<typeof setInterval> | undefined

const instancesRes = await request<{ instances?: import('~/types').InstanceData[] }>('/api/instances')
instances.value = instancesRes.instances || []

async function loadHostMetrics() {
  try {
    host.value = await request('/api/system/metrics')
  } catch {
    host.value = { ...host.value, platform: 'UNAVAILABLE', hostname: 'UNAVAILABLE', release: 'UNAVAILABLE' }
  }
}

onMounted(() => {
  loadHostMetrics()
  timer = setInterval(loadHostMetrics, 5000)
})
onUnmounted(() => { if (timer) clearInterval(timer) })

const summary = computed(() => [
  { label: 'ACTIVE INSTANCES', value: String(instances.value.length).padStart(2, '0'), note: '已登记的 Minecraft 实例' },
  { label: 'DEPLOYMENT MODE', value: 'JAR', note: '安全上传与独立目录' },
  { label: 'SESSION', value: '24', note: '管理员会话已建立' },
])
</script>

<template>
  <DashboardBackground />
  <main class="relative z-10 mx-auto max-w-7xl px-8 py-14">
    <header class="border-b border-border pb-8">
      <div class="flex items-end justify-between gap-8">
        <div>
          <p class="mb-6 font-mono text-xs tracking-[0.2em] text-text-secondary">/ CONTROL ROOM / AUTHORIZED</p>
          <h1 class="font-serif text-6xl font-light leading-none tracking-tight md:text-8xl">
            <span class="block text-text-primary">Server</span>
            <span class="mt-2 block text-brand italic">instances.</span>
          </h1>
        </div>
        <button type="button" class="mb-2 border border-brand px-4 py-3 font-mono text-xs text-text-primary hover:bg-brand hover:text-background" @click="navigateTo('/deploy')">[ + NEW INSTANCE ]</button>
      </div>
    </header>

    <nav class="mt-8 flex gap-8 border-b border-border font-mono text-sm">
      <button type="button" :class="activeTab === 'dashboard' ? 'border-b-2 border-brand pb-3 text-text-primary' : 'border-b-2 border-transparent pb-3 text-text-secondary hover:text-text-primary'" @click="activeTab = 'dashboard'">◈ 仪表盘</button>
      <button type="button" :class="activeTab === 'instances' ? 'border-b-2 border-brand pb-3 text-text-primary' : 'border-b-2 border-transparent pb-3 text-text-secondary hover:text-text-primary'" @click="activeTab = 'instances'">✦ 实例概览</button>
    </nav>

    <Transition name="dashboard-panel" mode="out-in">
      <section v-if="activeTab === 'dashboard'" key="dashboard" class="mt-10 space-y-6">
        <div class="grid gap-5 md:grid-cols-3">
          <article v-for="item in summary" :key="item.label" class="dashboard-card relative border-l border-t border-border bg-surface/75 p-6 shadow-2xl">
            <div class="pointer-events-none absolute inset-0 translate-x-2 translate-y-2 border border-border bg-background/40" />
            <div class="relative"><p class="font-mono text-[10px] tracking-[0.2em] text-text-secondary">{{ item.label }}</p><strong class="mt-5 block font-mono text-3xl text-text-primary">{{ item.value }}</strong><small class="mt-2 block text-xs text-text-secondary">{{ item.note }}</small></div>
          </article>
        </div>

        <div class="grid gap-5 lg:grid-cols-[1.2fr_0.8fr]">
          <article class="dashboard-card relative border-l border-t border-border bg-surface/75 p-7 shadow-2xl">
            <div class="pointer-events-none absolute inset-0 translate-x-2 translate-y-2 border border-border bg-background/40" />
            <div class="relative"><header class="flex items-center justify-between border-b border-border pb-4"><div><p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ HOST TELEMETRY</p><h2 class="mt-2 font-serif text-2xl text-text-primary">资源监控</h2></div><span class="font-mono text-[10px] text-data-live">● LIVE / 5S</span></header>
              <div class="mt-7 grid gap-8 md:grid-cols-2">
                <div><div class="flex items-end justify-between"><span class="font-mono text-[10px] tracking-[0.16em] text-text-secondary">CPU LOAD</span><strong class="font-mono text-2xl text-text-primary">{{ host.cpu.toFixed(1) }}%</strong></div><div class="mt-4 h-2 overflow-hidden bg-background"><div class="metric-line h-full bg-brand" :style="{ width: host.cpu + '%' }" /></div><div class="mt-5 grid grid-cols-4 gap-2"><i v-for="(core, index) in host.cores" :key="index" class="block h-16 border border-border bg-background/50 p-1"><span class="block h-full bg-brand/70 transition-all duration-700" :style="{ transform: 'scaleY(' + Math.max(0.08, core / 100) + ')', transformOrigin: 'bottom' }" /><small class="mt-1 block font-mono text-[8px] text-text-secondary">C{{ index + 1 }}</small></i></div></div>
                <div><div class="flex items-end justify-between"><span class="font-mono text-[10px] tracking-[0.16em] text-text-secondary">MEMORY LOAD</span><strong class="font-mono text-2xl text-text-primary">{{ host.memory.toFixed(1) }}%</strong></div><div class="mt-4 h-2 overflow-hidden bg-background"><div class="metric-line h-full bg-data-live" :style="{ width: host.memory + '%' }" /></div><p class="mt-6 font-mono text-xs text-text-secondary">实时采样 · 系统资源状态</p></div>
              </div>
            </div>
          </article>

          <article class="dashboard-card relative border-l border-t border-border bg-surface/75 p-7 shadow-2xl">
            <div class="pointer-events-none absolute inset-0 translate-x-2 translate-y-2 border border-border bg-background/40" />
            <div class="relative"><p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ SYSTEM IDENTITY</p><h2 class="mt-2 font-serif text-2xl text-text-primary">主机信息</h2><dl class="mt-7 divide-y divide-border font-mono text-xs"><div class="flex justify-between py-4"><dt class="text-text-secondary">PANEL VERSION</dt><dd class="text-text-primary">{{ host.panel }}</dd></div><div class="flex justify-between py-4"><dt class="text-text-secondary">PLATFORM</dt><dd class="text-text-primary">{{ host.platform }}</dd></div><div class="flex justify-between py-4"><dt class="text-text-secondary">HOSTNAME</dt><dd class="text-text-primary">{{ host.hostname }}</dd></div><div class="flex justify-between py-4"><dt class="text-text-secondary">RELEASE</dt><dd class="max-w-[12rem] truncate text-right text-text-primary">{{ host.release }}</dd></div></dl></div>
          </article>
        </div>
      </section>

      <section v-else key="instances" class="mt-10">
        <div v-if="!instances.length" class="dashboard-card relative border-l border-t border-border bg-surface/75 py-32 text-center shadow-2xl"><span class="font-mono text-xs tracking-[0.3em] text-brand">[ 00 / 00 ]</span><h2 class="mt-6 font-mono text-lg tracking-[0.35em] text-text-primary">NO SERVER INSTANCES</h2><p class="mt-4 text-xs text-text-secondary">创建第一个实例，上传服务端核心并确认 EULA。</p></div>
        <div v-else class="divide-y divide-border border-y border-border"> <NuxtLink v-for="(item, index) in instances" :key="item.id" :to="`/instances/${item.id}`" class="group flex items-center justify-between py-7 transition hover:bg-surface/60"><div class="flex items-center gap-8"><span class="font-mono text-xs text-brand">&gt; {{ String(index + 1).padStart(2, '0') }}</span><div><h2 class="font-mono text-lg font-bold text-text-primary">{{ item.name }}</h2><small class="font-mono text-xs text-text-secondary">PORT {{ item.port }} · STATUS {{ item.status }}</small></div></div><span class="font-mono text-xs text-text-secondary group-hover:text-brand">[ DETAILS + ]</span></NuxtLink></div>
      </section>
    </Transition>
  </main>
</template>

<style scoped>
.dashboard-panel-enter-active, .dashboard-panel-leave-active { transition: opacity 260ms ease, transform 260ms ease; }
.dashboard-panel-enter-from { opacity: 0; transform: translateY(12px); }
.dashboard-panel-leave-to { opacity: 0; transform: translateY(-8px); }
.dashboard-card { transition: transform 320ms cubic-bezier(.22,1,.36,1), border-color 260ms ease, background-color 260ms ease; }
.dashboard-card:hover { transform: translateY(-3px); border-color: color-mix(in srgb, var(--brand) 55%, transparent); }
.metric-line { transition: width 900ms cubic-bezier(.22,1,.36,1); }
</style>