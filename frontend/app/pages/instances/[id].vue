<script setup lang="ts">
import WorkspaceBackground from '~/components/ui/WorkspaceBackground.vue'
import Console from '~/components/instance/Console.vue'
import Monitor from '~/components/instance/Monitor.vue'
import FileManager from '~/components/instance/FileManager.vue'
import Backups from '~/components/instance/Backups.vue'
import InstanceSettings from '~/components/instance/InstanceSettings.vue'
import PlayerManager from '~/components/instance/PlayerManager.vue'
definePageMeta({ middleware: 'auth' })
const { t, locale } = useI18n()
const tr = usePanelText()
const route = useRoute()
const instanceId = String(route.params.id)
const instance = ref<import('~/types').InstanceData | null>(null)
const activeTab = ref('console')
const tabKeys: Record<string, string> = {
  console: 'tabConsole',
  monitor: 'tabMonitor',
  files: 'tabFiles',
  backups: 'tabBackups',
  settings: 'tabInstanceSettings',
}
const tabNav = ref<HTMLElement | null>(null)
const tabIndicator = ref({ left: '0px', width: '0px' })
let tabObserver: ResizeObserver | undefined
// 高亮线跟随真实文字宽度与语言变化。
function updateTabIndicator() {
  const button = tabNav.value?.querySelector<HTMLElement>(`[data-instance-tab="${activeTab.value}"]`)
  if (button) tabIndicator.value = { left: button.offsetLeft + 'px', width: button.offsetWidth + 'px' }
}
watch([activeTab, locale], () => nextTick(updateTabIndicator))
let timer: ReturnType<typeof setInterval> | undefined
const { request, getErrorMessage } = useApi()
const toast = ref<{ type: 'success' | 'error'; message: string } | null>(null)
const showDeleteModal = ref(false)
async function deleteInstance() {
  try {
    await request('/api/instances/' + encodeURIComponent(instanceId), { method: 'DELETE' })
    await navigateTo('/dashboard')
  } catch (error: unknown) {
    showDeleteModal.value = false
    showToast('error', getErrorMessage(error, '实例删除失败'))
  }
}
function showToast(type: 'success' | 'error', message: string) {
  toast.value = { type, message }
  window.setTimeout(() => {
    toast.value = null
  }, 3500)
}

async function load() {
  instance.value = await request<import('~/types').InstanceData>('/api/instances/' + encodeURIComponent(instanceId))
}
const powerBusy = ref(false)
async function power(action: 'start' | 'stop' | 'restart') {
  if (powerBusy.value) return
  powerBusy.value = true
  try {
    await request('/api/instances/' + encodeURIComponent(instanceId) + '/power', { method: 'POST', body: { action } })
    await load()
  } catch (error: unknown) {
    showToast('error', getErrorMessage(error, t('instancePowerError')))
  } finally {
    powerBusy.value = false
  }
}
onMounted(() => {
  load()
  nextTick(updateTabIndicator)
  tabObserver = new ResizeObserver(updateTabIndicator)
  if (tabNav.value) tabObserver.observe(tabNav.value)
  timer = setInterval(load, 10000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
  tabObserver?.disconnect()
})
</script>
<template>
  <div class="min-h-screen">
    <WorkspaceBackground />
    <main class="relative z-10 mx-auto max-w-7xl px-8 py-12">
      <header class="flex flex-wrap items-end justify-between gap-6 border-b border-border pb-7">
        <div>
          <p class="font-mono text-[10px] tracking-[0.22em] text-text-secondary">/ INSTANCE CONTROL TERMINAL</p>
          <h1 class="mt-3 font-serif text-4xl text-text-primary">{{ instance?.name || instanceId }}</h1>
          <p class="mt-2 font-mono text-xs text-text-secondary">
            PORT {{ instance?.port || '—' }} · {{ instance?.status || 'LOADING' }}
          </p>
        </div>
        <div class="flex gap-2">
          <button
            v-for="action in ['start', 'restart', 'stop']"
            :key="action"
            type="button"
            class="border border-border px-4 py-2 font-mono text-[10px] text-text-secondary uppercase hover:border-brand hover:text-brand"
            :disabled="powerBusy || instance?.status === 'deploying'"
            :aria-busy="powerBusy"
            @click="power(action as 'start' | 'stop' | 'restart')"
          >
            {{ t(action === 'start' ? 'instanceStart' : action === 'stop' ? 'instanceStop' : 'instanceRestart') }}
          </button>
          <button
            type="button"
            class="border border-red-500/30 px-4 py-2 font-mono text-[10px] text-red-500 uppercase hover:bg-red-500/10"
            @click="showDeleteModal = true"
          >
            [ DELETE ]
          </button>
        </div>
      </header>
      <div
        v-if="showDeleteModal"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
        role="dialog"
        aria-modal="true"
      >
        <AtmosphereCard>
          <div class="max-w-md space-y-5">
            <p class="font-mono text-[10px] tracking-[0.2em] text-red-500">/ DESTRUCTIVE ACTION</p>
            <h2 class="font-serif text-2xl text-text-primary">确认删除实例 {{ instance?.name || instanceId }}？</h2>
            <p class="text-sm text-text-secondary">此操作将永久删除所有服务端文件，不可恢复！</p>
            <div class="flex justify-end gap-3">
              <button
                type="button"
                class="border border-border px-4 py-2 font-mono text-xs text-text-secondary hover:text-text-primary"
                @click="showDeleteModal = false"
              >
                取消
              </button>
              <button
                type="button"
                class="border border-red-500/30 px-4 py-2 font-mono text-xs text-red-500 hover:bg-red-500/10"
                @click="deleteInstance"
              >
                确认删除
              </button>
            </div>
          </div>
        </AtmosphereCard>
      </div>
      <nav ref="tabNav" class="relative mt-8 flex flex-wrap gap-6 border-b border-border font-mono text-xs">
        <button
          v-for="tab in ['console', 'monitor', 'players', 'files', 'backups', 'settings']"
          :key="tab"
          :data-instance-tab="tab"
          type="button"
          class="pb-3 tracking-wider uppercase transition-colors duration-300"
          :class="activeTab === tab ? 'text-brand' : 'text-text-secondary hover:text-text-primary'"
          @click="activeTab = tab"
        >
          {{ tab === 'players' ? tr('玩家管理', 'PLAYERS', 'プレイヤー') : t(tabKeys[tab]!) }}
        </button>
        <span aria-hidden="true" class="instance-tab-indicator" :style="tabIndicator" />
      </nav>
      <section class="mt-8">
        <Console v-if="activeTab === 'console'" :instance-id="instanceId" :status="instance?.status" /><Monitor
          v-else-if="activeTab === 'monitor'"
          :instance-id="instanceId"
        /><FileManager v-else-if="activeTab === 'files'" :instance-id="instanceId" /><Backups
          v-else-if="activeTab === 'backups'"
          :instance-id="instanceId"
        />
        <PlayerManager v-else-if="activeTab === 'players'" :instance-id="instanceId" />
        <InstanceSettings v-else :instance-id="instanceId" :status="instance?.status" @saved="load" />
        <div
          v-if="toast"
          class="fixed right-6 bottom-6 z-50 border border-border px-5 py-3 font-mono text-xs text-text-primary backdrop-blur-md"
        >
          {{ toast.message }}
        </div>
      </section>
      <div class="mt-10">
        <a href="/dashboard" class="font-mono text-sm tracking-[0.18em] text-text-secondary hover:text-brand">
          ← {{ t('backToControlRoom') }}
        </a>
      </div>
    </main>
  </div>
</template>

<style scoped>
.instance-tab-indicator {
  position: absolute;
  bottom: -1px;
  height: 2px;
  background: var(--brand);
  box-shadow: 0 0 10px color-mix(in srgb, var(--brand) 20%, transparent);
  transition:
    left 320ms cubic-bezier(0.22, 1, 0.36, 1),
    width 320ms cubic-bezier(0.22, 1, 0.36, 1);
  pointer-events: none;
}
/* 保留样式入口，兼容开发环境的旧 HMR 引用。 */
button[aria-busy='true'] {
  cursor: wait;
  opacity: 0.5;
}
</style>
