<script setup lang="ts">


type Level = 'normal' | 'error' | 'warn' | 'system'
type LogLine = { id: number; text: string; level: Level; time: string }

const props = defineProps<{ instanceId: string; status?: string }>()
const { request, getErrorMessage } = useApi()
const isOffline = computed(() => props.status === 'stopped' || props.status === 'failed')
const logs = ref<LogLine[]>([])
const command = ref('')
const connected = ref(false)
const paused = ref(false)
const autoScroll = ref(true)
const sending = ref(false)
const viewport = ref<HTMLElement | null>(null)
const filter = ref<'all' | 'error' | 'warn'>('all')
const playerCount = ref(0)
const sequence = ref(0)
let source: EventSource | null = null
let playerTimer: ReturnType<typeof setInterval> | undefined

const visibleLogs = computed(() => logs.value.filter((line) => filter.value === 'all' || line.level === filter.value))
const statusLabel = computed(() => connected.value ? 'STREAM ONLINE' : 'STREAM OFFLINE')

function classify(text: string): Level {
  if (/error|exception|failed|fatal|crash/i.test(text)) return 'error'
  if (/warn|warning/i.test(text)) return 'warn'
  if (/journal|connected|starting|stopping/i.test(text)) return 'system'
  return 'normal'
}

function append(text: string) {
  if (paused.value) return
  const now = new Date().toLocaleTimeString('en-GB')
  logs.value.push(...text.split(/\r?\n/).filter(Boolean).map((line) => ({ id: sequence.value++, text: line, level: classify(line), time: now })))
  if (logs.value.length > 800) logs.value.splice(0, logs.value.length - 800)
  if (autoScroll.value) nextTick(() => { if (viewport.value) viewport.value.scrollTop = viewport.value.scrollHeight })
}

function connect() {
  source?.close()
  if (isOffline.value) return
  source = new EventSource('/api/instances/' + encodeURIComponent(props.instanceId) + '/logs/stream')
  source.onopen = () => { connected.value = true }
  source.onmessage = (event) => {
    try { const payload = JSON.parse(event.data); if (payload.logs) append(payload.logs); if (payload.line) append(payload.line) } catch { append(event.data) }
  }
  source.onerror = () => { connected.value = false }
}

async function refreshPlayers() {
  try { const result = await request<{ players?: string[] }>('/api/instances/' + encodeURIComponent(props.instanceId) + '/players'); playerCount.value = result.players?.length || 0 } catch { playerCount.value = 0 }
}

async function sendCommand() {
  const value = command.value.trim()
  if (!value || sending.value) return
  sending.value = true
  try { await request('/api/instances/' + encodeURIComponent(props.instanceId) + '/command', { method: 'POST', body: { command: value } }); append('> ' + value); command.value = '' } catch (error: unknown) { append('[command error] ' + getErrorMessage(error, '指令发送失败')) } finally { sending.value = false }
}

function clearLogs() { logs.value = [] }
function onScroll() { if (!viewport.value) return; autoScroll.value = viewport.value.scrollHeight - viewport.value.scrollTop - viewport.value.clientHeight < 40 }

onMounted(() => { connect(); refreshPlayers(); playerTimer = setInterval(refreshPlayers, 10000) })
onUnmounted(() => { source?.close(); if (playerTimer) clearInterval(playerTimer) })
</script>

<template>
  <section class="console-shell border border-border bg-black/80 shadow-2xl">
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
      <div class="flex items-center gap-4 font-mono text-[10px] tracking-[0.18em]"><span class="text-text-primary">LIVE CONSOLE</span><span class="text-text-secondary">/ {{ instanceId }}</span><span :class="connected ? 'text-data-live' : 'text-red-400'">● {{ statusLabel }}</span></div>
      <div class="flex items-center gap-3 font-mono text-[10px] text-text-secondary"><span>PLAYERS {{ playerCount }}</span><button type="button" class="hover:text-brand" @click="paused = !paused">{{ paused ? 'RESUME' : 'PAUSE' }}</button><button type="button" class="hover:text-brand" @click="clearLogs">CLEAR</button></div>
    </header>
    <div class="flex items-center justify-between border-b border-border/70 px-4 py-2 font-mono text-[10px]">
      <div class="flex gap-3"><button v-for="item in [{ key: 'all', label: 'ALL' }, { key: 'error', label: 'ERROR' }, { key: 'warn', label: 'WARN' }]" :key="item.key" type="button" :class="filter === item.key ? 'text-brand' : 'text-text-secondary hover:text-text-primary'" @click="filter = item.key as typeof filter">{{ item.label }}</button></div>
      <span class="text-text-secondary">{{ visibleLogs.length.toString().padStart(3, '0') }} LINES</span>
    </div>
    <div ref="viewport" class="h-[460px] overflow-y-auto p-4 font-mono text-[11px] leading-6" @scroll="onScroll">
      <p v-if="isOffline" class="py-12 text-center text-text-secondary">SERVER IS OFFLINE</p><p v-else-if="!visibleLogs.length" class="py-12 text-center text-text-secondary">等待服务端日志……</p>
      <div v-for="line in visibleLogs" :key="line.id" class="grid grid-cols-[70px_42px_1fr] gap-3 hover:bg-white/[0.03]">
        <span class="text-text-secondary/60">{{ line.time }}</span><span class="text-text-secondary/50">{{ line.level === 'error' ? 'ERR' : line.level === 'warn' ? 'WRN' : line.level === 'system' ? 'SYS' : 'LOG' }}</span><span :class="line.level === 'error' ? 'text-red-400' : line.level === 'warn' ? 'text-amber-300' : line.level === 'system' ? 'text-brand' : 'text-text-secondary'">{{ line.text }}</span>
      </div>
    </div>
    <div class="flex items-center justify-between border-t border-border px-4 py-2 font-mono text-[9px] text-text-secondary"><span>{{ paused ? 'OUTPUT PAUSED' : autoScroll ? 'AUTO-SCROLL ACTIVE' : 'SCROLL PAUSED' }}</span><button type="button" class="hover:text-brand" @click="autoScroll = !autoScroll">{{ autoScroll ? 'DISABLE AUTO-SCROLL' : 'ENABLE AUTO-SCROLL' }}</button></div>
    <form class="flex border-t border-border" @submit.prevent="sendCommand"><span class="px-4 py-4 font-mono text-brand">&gt;</span><input v-model="command" :disabled="isOffline" class="min-w-0 flex-1 bg-transparent px-1 py-4 font-mono text-xs text-text-primary outline-none placeholder:text-text-secondary" placeholder="输入服务器指令，例如 say hello" autocomplete="off"><button type="submit" class="border-l border-border px-5 font-mono text-[10px] tracking-[0.15em] text-brand hover:bg-surface disabled:opacity-50" :disabled="sending || isOffline">{{ sending ? 'WAIT' : 'SEND' }}</button></form>
  </section>
</template>