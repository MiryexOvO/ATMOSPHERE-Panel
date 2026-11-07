<script setup lang="ts">
import LocalScrollRuler from '~/components/ui/LocalScrollRuler.vue'
const { t } = useI18n()
type Level = 'normal' | 'error' | 'warn' | 'system'
type LogLine = { id: number; text: string; level: Level; time: string; animate: boolean }

const props = defineProps<{ instanceId: string; status?: string }>()
const { instanceRequest, path, getErrorMessage } = useInstanceApi(() => props.instanceId)
const logs = ref<LogLine[]>([])
const command = ref('')
const connected = ref(false)
const serverRunning = ref<boolean | null>(null)
// 优先采用实时心跳，避免旧状态误禁用发送。
const isOffline = computed(() =>
  serverRunning.value === null ? ['stopped', 'failed', 'error'].includes(props.status || '') : !serverRunning.value,
)
const history = ref<string[]>([])
let historyPosition = 0
const paused = ref(false)
const autoScroll = ref(true)
const sending = ref(false)
const sent = ref(false)
let sentTimer: ReturnType<typeof setTimeout> | undefined
const viewport = ref<HTMLElement | null>(null)
const filter = ref<'all' | 'error' | 'warn'>('all')
const playerCount = ref(0)
const sequence = ref(0)
let source: EventSource | null = null
let playerTimer: ReturnType<typeof setInterval> | undefined
const MAX_LOGS = 800
const logClock = new Intl.DateTimeFormat('en-GB', { hour: '2-digit', minute: '2-digit', second: '2-digit' })
let pendingLogs: LogLine[] = []
let flushFrame = 0,
  scrollFrame = 0,
  lastFlush = 0

const visibleLogs = computed(() => logs.value.filter((line) => filter.value === 'all' || line.level === filter.value))
const streamOnline = computed(() => connected.value && serverRunning.value && !isOffline.value)
const statusLabel = computed(() => (streamOnline.value ? 'STREAM ONLINE' : 'STREAM OFFLINE'))

function classify(text: string): Level {
  if (/error|exception|failed|fatal|crash/i.test(text)) return 'error'
  if (/warn|warning/i.test(text)) return 'warn'
  if (/journal|connected|starting|stopping/i.test(text)) return 'system'
  return 'normal'
}

// 日志先缓冲，批量刷新，避免每条消息触发渲染和布局。
function flushLogs(now: number) {
  flushFrame = 0
  if (now - lastFlush < 80) {
    flushFrame = requestAnimationFrame(flushLogs)
    return
  }
  lastFlush = now
  const batch = pendingLogs
  pendingLogs = []
  if (!batch.length) return
  const animate = batch.length <= 12
  logs.value = [...logs.value, ...batch.map((line) => ({ ...line, animate }))].slice(-MAX_LOGS)
  if (autoScroll.value)
    nextTick(() => {
      if (scrollFrame) cancelAnimationFrame(scrollFrame)
      scrollFrame = requestAnimationFrame(() => {
        scrollFrame = 0
        if (autoScroll.value && viewport.value) viewport.value.scrollTop = viewport.value.scrollHeight
      })
    })
}

function append(text: string) {
  if (paused.value) return
  const now = logClock.format(Date.now())
  const lines = text.split(/\r?\n/).filter(Boolean).slice(-MAX_LOGS)
  pendingLogs.push(
    ...lines.map((line) => ({ id: sequence.value++, text: line, level: classify(line), time: now, animate: false })),
  )
  if (pendingLogs.length > MAX_LOGS) pendingLogs.splice(0, pendingLogs.length - MAX_LOGS)
  if (!flushFrame) flushFrame = requestAnimationFrame(flushLogs)
}

function connect() {
  source?.close()
  connected.value = false
  serverRunning.value = null
  source = new EventSource(path('/logs/stream'))
  source.onopen = () => {
    connected.value = true
  }
  source.addEventListener('state', (event) => {
    try {
      serverRunning.value = JSON.parse((event as MessageEvent).data).running
    } catch {
      serverRunning.value = false
    }
  })
  source.onmessage = (event) => {
    try {
      const payload = JSON.parse(event.data)
      if (payload.logs) append(payload.logs)
      if (payload.line) append(payload.line)
    } catch {
      append(event.data)
    }
  }
  source.onerror = () => {
    connected.value = false
  }
}

async function refreshPlayers() {
  try {
    const result = await instanceRequest<{ players?: string[] }>('/players')
    playerCount.value = result.players?.length || 0
  } catch {
    playerCount.value = 0
  }
}

async function sendCommand() {
  const value = command.value.trim()
  if (!value || sending.value) return
  if (isOffline.value) {
    append(t('msg_system_start_the_server_before_sending_your_'))
    return
  }
  sending.value = true
  try {
    await instanceRequest('/command', {
      method: 'POST',
      body: { command: value },
    })
    append('> ' + value)
    history.value.push(value)
    historyPosition = history.value.length
    command.value = ''
    sent.value = true
    if (sentTimer) clearTimeout(sentTimer)
    sentTimer = setTimeout(() => {
      sent.value = false
    }, 900)
  } catch (error: unknown) {
    append('[command error] ' + getErrorMessage(error, t('msg_failed_to_send_command')))
  } finally {
    sending.value = false
  }
}

// 上下键回溯已成功发送的指令。
function recall(direction: number) {
  historyPosition = Math.max(0, Math.min(history.value.length, historyPosition + direction))
  command.value = history.value[historyPosition] || ''
}

function clearLogs() {
  logs.value = []
  pendingLogs = []
  if (flushFrame) cancelAnimationFrame(flushFrame)
  flushFrame = 0
}
function onScroll() {
  if (!viewport.value) return
  autoScroll.value = viewport.value.scrollHeight - viewport.value.scrollTop - viewport.value.clientHeight < 40
}

// 状态由心跳更新，只有切换实例才重建日志连接。
watch(
  () => props.instanceId,
  () => {
    clearLogs()
    connect()
    refreshPlayers()
  },
)

onMounted(() => {
  connect()
  refreshPlayers()
  playerTimer = setInterval(refreshPlayers, 10000)
})
onUnmounted(() => {
  source?.close()
  if (playerTimer) clearInterval(playerTimer)
  if (sentTimer) clearTimeout(sentTimer)
  if (flushFrame) cancelAnimationFrame(flushFrame)
  if (scrollFrame) cancelAnimationFrame(scrollFrame)
  pendingLogs = []
})
</script>

<template>
  <section class="console-shell border border-border bg-black/80 shadow-2xl">
    <header class="flex flex-wrap items-center justify-between gap-3 border-b border-border px-4 py-3">
      <div class="flex items-center gap-4 font-mono text-[10px] tracking-[0.18em]">
        <span class="text-text-primary">LIVE CONSOLE</span><span class="text-text-secondary">/ {{ instanceId }}</span
        ><span :class="streamOnline ? 'text-data-live' : 'text-red-400'">● {{ statusLabel }}</span>
      </div>
      <div class="flex items-center gap-3 font-mono text-[10px] text-text-secondary">
        <span>PLAYERS {{ playerCount }}</span
        ><button type="button" class="hover:text-brand" @click="paused = !paused">
          {{ paused ? 'RESUME' : 'PAUSE' }}</button
        ><button type="button" class="hover:text-brand" @click="clearLogs">CLEAR</button>
      </div>
    </header>
    <div class="flex items-center justify-between border-b border-border/70 px-4 py-2 font-mono text-[10px]">
      <div class="flex gap-3">
        <button
          v-for="item in [
            { key: 'all', label: 'ALL' },
            { key: 'error', label: 'ERROR' },
            { key: 'warn', label: 'WARN' },
          ]"
          :key="item.key"
          type="button"
          :class="filter === item.key ? 'text-brand' : 'text-text-secondary hover:text-text-primary'"
          @click="filter = item.key as typeof filter"
        >
          {{ item.label }}
        </button>
      </div>
      <span class="text-text-secondary">{{ visibleLogs.length.toString().padStart(3, '0') }} LINES</span>
    </div>
    <div class="relative">
      <div ref="viewport" class="h-[460px] overflow-y-auto p-4 font-mono text-[11px] leading-6" @scroll="onScroll">
        <p v-if="isOffline" class="py-12 text-center text-text-secondary">SERVER IS OFFLINE</p>
        <p v-else-if="!visibleLogs.length" class="py-12 text-center text-text-secondary">
          {{ t('msg_waiting_for_server_logs') }}
        </p>
        <div
          v-for="line in visibleLogs"
          :key="line.id"
          class="terminal-line grid grid-cols-[70px_42px_1fr] gap-3 hover:bg-white/[0.03]"
          :class="{ 'is-new': line.animate }"
        >
          <span class="text-text-secondary/60">{{ line.time }}</span
          ><span class="text-text-secondary/50">{{
            line.level === 'error' ? 'ERR' : line.level === 'warn' ? 'WRN' : line.level === 'system' ? 'SYS' : 'LOG'
          }}</span
          ><span
            :class="
              line.level === 'error'
                ? 'text-red-400'
                : line.level === 'warn'
                  ? 'text-amber-300'
                  : line.level === 'system'
                    ? 'text-brand'
                    : 'text-text-secondary'
            "
            >{{ line.text }}</span
          >
        </div>
      </div>
      <LocalScrollRuler :target="viewport" />
    </div>
    <div
      class="flex items-center justify-between border-t border-border px-4 py-2 font-mono text-[9px] text-text-secondary"
    >
      <span>{{ paused ? 'OUTPUT PAUSED' : autoScroll ? 'AUTO-SCROLL ACTIVE' : 'SCROLL PAUSED' }}</span
      ><button type="button" class="hover:text-brand" @click="autoScroll = !autoScroll">
        {{ autoScroll ? 'DISABLE AUTO-SCROLL' : 'ENABLE AUTO-SCROLL' }}
      </button>
    </div>
    <form
      class="terminal-input flex border-t border-border"
      :class="{ 'is-sending': sending }"
      @submit.prevent="sendCommand"
    >
      <span class="px-4 py-4 font-mono text-brand">&gt;</span
      ><input
        v-model="command"
        class="min-w-0 flex-1 bg-transparent px-1 py-4 font-mono text-xs text-text-primary outline-none placeholder:text-text-secondary"
        :placeholder="t('msg_enter_a_server_command_e_g_say_hello')"
        autocomplete="off"
        @keydown.up.prevent="recall(-1)"
        @keydown.down.prevent="recall(1)"
      /><button
        type="submit"
        class="border-l border-border px-5 font-mono text-[10px] tracking-[0.15em] text-brand hover:bg-surface disabled:opacity-50"
        :disabled="sending || isOffline || !command.trim()"
      >
        <span
          class="inline-block transition-transform duration-300"
          :class="sent ? 'translate-x-1 text-data-live' : ''"
          >{{ sending ? t('msg_sending') : sent ? t('msg_sent') : t('msg_send') }}</span
        >
      </button>
    </form>
    <p v-if="isOffline" role="status" class="border-t border-border px-4 py-2 text-xs text-text-secondary">
      {{ t('msg_server_stopped_you_can_prepare_a_command_and') }}
    </p>
  </section>
</template>
<style scoped>
/* 新日志轻移入场，发送时沿输入栏扫光。 */
.terminal-line {
  overflow-wrap: anywhere;
}
.terminal-line.is-new {
  animation: line-arrive 220ms ease-out;
}
.terminal-input {
  position: relative;
  transition: box-shadow 250ms;
}
.terminal-input:focus-within {
  box-shadow: inset 0 -1px var(--brand);
}
.terminal-input.is-sending::after {
  content: '';
  position: absolute;
  top: 0;
  left: 0;
  height: 1px;
  width: 25%;
  background: var(--brand);
  box-shadow: 0 0 12px var(--brand);
  animation: command-scan 800ms ease-in-out infinite;
}
@keyframes line-arrive {
  from {
    opacity: 0.3;
    transform: translateY(4px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes command-scan {
  from {
    left: 0;
    opacity: 0;
  }
  50% {
    opacity: 1;
  }
  to {
    left: 75%;
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .terminal-line,
  .terminal-input.is-sending::after {
    animation: none;
  }
}
</style>
