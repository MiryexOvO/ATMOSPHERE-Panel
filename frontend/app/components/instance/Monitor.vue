<script setup lang="ts">
import ResourceChart from './ResourceChart.vue'
const props = defineProps<{ instanceId: string }>()
const { t } = useI18n()
const tr = usePanelText()
const { request, getErrorMessage } = useApi()
type Reading = {
  running: boolean
  pid: number | null
  cpu_percent: number
  host_cpu_percent: number
  memory_mb: number
  memory_percent: number
  allocated_mb: number
  threads: number
  uptime_seconds: number
  read_bytes_per_second: number
  write_bytes_per_second: number
  total_read_bytes: number
  total_write_bytes: number
  io_available: boolean
}
type Point = { time: string; cpu: number; memory: number }
const points = ref<Point[]>([])
const reading = ref<Reading | null>(null)
const loading = ref(true)
const error = ref('')
let disposed = false,
  sampling = false
let timer: ReturnType<typeof setInterval> | undefined
const uptime = computed(() => {
  const n = reading.value?.uptime_seconds || 0
  return `${Math.floor(n / 3600)}h ${Math.floor((n % 3600) / 60)}m ${n % 60}s`
})
const tiles = computed(() => [
  { label: t('monitorThreads'), value: String(reading.value?.threads || 0) },
  { label: t('monitorUptime'), value: uptime.value },
  { label: t('monitorRead'), value: ((reading.value?.read_bytes_per_second || 0) / 1024).toFixed(1) + ' KB/s' },
  { label: t('monitorWrite'), value: ((reading.value?.write_bytes_per_second || 0) / 1024).toFixed(1) + ' KB/s' },
])
// 采集实例进程资源，失败时保留最近读数并显示错误。
async function sample() {
  if (sampling || disposed) return
  sampling = true
  try {
    reading.value = await request<Reading>(`/api/instances/${encodeURIComponent(props.instanceId)}/monitor`)
    points.value.push({
      time: new Date().toLocaleTimeString(),
      cpu: reading.value.host_cpu_percent,
      memory: reading.value.memory_mb,
    })
    if (points.value.length > 60) points.value.shift()
    error.value = ''
  } catch (cause) {
    error.value = getErrorMessage(cause)
  } finally {
    loading.value = false
    sampling = false
  }
}
onMounted(async () => {
  await sample()
  let seconds = 5
  try {
    const result = await request<{ settings: { metrics_interval_seconds: number } }>('/api/panel/settings')
    seconds = result.settings.metrics_interval_seconds
  } catch {}
  if (!disposed) timer = setInterval(sample, seconds * 1000)
})
onUnmounted(() => {
  disposed = true
  if (timer) clearInterval(timer)
})
</script>
<template>
  <section class="space-y-6">
    <header class="flex flex-wrap items-end justify-between gap-3">
      <div>
        <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ LIVE SAMPLING</p>
        <h2 class="mt-2 font-serif text-2xl">{{ t('monitorTitle') }}</h2>
      </div>
      <span class="font-mono text-xs text-text-secondary"
        >PID {{ reading?.pid || '—' }} · {{ reading?.running ? 'LIVE' : t('monitorOffline') }}</span
      >
    </header>
    <p class="text-xs leading-6 text-text-secondary">
      {{
        tr(
          'CPU 按主机逻辑核心数归一化，只统计此实例的进程树；内存相对于实例分配上限。',
          'CPU is normalized by host logical cores and measures only this instance process tree. Memory is relative to the instance allocation.',
          'CPU はホストの論理コア数で正規化し、このインスタンスのプロセス群のみ計測。メモリは割当上限に対する割合です。',
        )
      }}
    </p>
    <p v-if="error" role="alert" class="text-sm text-red-400">{{ error }}</p>
    <div class="grid gap-4 md:grid-cols-2">
      <AtmosphereCard :interactive="false">
        <p class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">{{ t('monitorCpu') }}</p>
        <strong class="mt-3 block font-mono text-3xl text-text-primary"
          >{{ (points.at(-1)?.cpu ?? 0).toFixed(1) }}%</strong
        >
        <ResourceChart class="mt-5" :values="points.map((p) => p.cpu)" :label="t('monitorCpu')" />
        <p class="mt-3 font-mono text-[10px] text-text-secondary">
          {{ tr('单核等效', 'SINGLE-CORE EQUIVALENT', '単一コア換算') }} {{ (reading?.cpu_percent || 0).toFixed(2) }}%
        </p>
      </AtmosphereCard>
      <AtmosphereCard :interactive="false">
        <p class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">{{ t('monitorMemory') }}</p>
        <strong class="mt-3 block font-mono text-3xl text-text-primary"
          >{{ (reading?.memory_mb ?? 0).toFixed(0) }}
          <span class="text-sm text-text-secondary">MB / {{ reading?.allocated_mb || '—' }} MB</span></strong
        >
        <ResourceChart
          class="mt-5"
          :values="points.map((p) => p.memory)"
          :limit="reading?.allocated_mb || 4096"
          :label="t('monitorMemory')"
          color="var(--data-live)"
        />
        <p class="mt-3 font-mono text-[10px] text-text-secondary">
          {{ (reading?.memory_percent || 0).toFixed(1) }}% / ALLOCATED MEMORY
        </p>
      </AtmosphereCard>
    </div>
    <div class="grid grid-cols-2 gap-4 lg:grid-cols-4">
      <AtmosphereCard v-for="tile in tiles" :key="tile.label" :interactive="false"
        ><p class="text-xs text-text-secondary">{{ tile.label }}</p>
        <strong class="mt-4 block font-mono text-xl text-brand">{{ tile.value }}</strong></AtmosphereCard
      >
    </div>
    <p class="font-mono text-xs leading-6 text-text-secondary">
      {{ tr('累计读取 / 写入', 'TOTAL READ / WRITE', '累積読み取り / 書き込み') }} ·
      {{ ((reading?.total_read_bytes || 0) / 1048576).toFixed(1) }} MB /
      {{ ((reading?.total_write_bytes || 0) / 1048576).toFixed(1) }} MB
      <span v-if="reading?.io_available === false"
        >·
        {{
          tr(
            '此平台不提供进程磁盘统计',
            'PROCESS DISK STATS UNAVAILABLE ON THIS PLATFORM',
            'この環境ではプロセスのディスク統計を取得できません',
          )
        }}</span
      >
    </p>
    <p class="font-mono text-[10px] text-text-secondary">
      {{ loading ? '读取监控数据……' : t('monitorSample') + ' · ' + points.length }}
    </p>
  </section>
</template>
