<script setup lang="ts">
import Console from '~/components/instance/Console.vue'
import Monitor from '~/components/instance/Monitor.vue'
import FileManager from '~/components/instance/FileManager.vue'
import Backups from '~/components/instance/Backups.vue'
definePageMeta({ middleware: 'auth' })
const route = useRoute()
const instanceId = String(route.params.id)
const instance = ref<import('~/types').InstanceData | null>(null)
const activeTab = ref('console')
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
const settings = reactive({ name: '', instance_path: '', java_version: '21', jar_name: 'server.jar', jvm_args: '', port: 0, memory_mb: 4096, memory_unit: 'MB', rcon_enabled: true, rcon_port: 25575, rcon_password: '', auto_restart: false, ignore_eula: false, server_properties: '' })
const settingsNav = ref('instance')
const settingsLoaded = ref(false)

function showToast(type: 'success' | 'error', message: string) {
  toast.value = { type, message }
  window.setTimeout(() => { toast.value = null }, 3500)
}

async function loadSettings() {
  try {
    const response = await request<{ settings: typeof settings }>('/api/instances/' + encodeURIComponent(instanceId) + '/settings')
    Object.assign(settings, response.settings)
    settingsLoaded.value = true
  } catch (error: unknown) {
    showToast('error', getErrorMessage(error, '设置加载失败'))
  }
}

async function saveSettings() {
  try {
    const response = await request<{ restart_required?: boolean }>('/api/instances/' + encodeURIComponent(instanceId) + '/settings', { method: 'PUT', body: settings })
    showToast('success', response.restart_required ? '配置已保存，内存修改需重启实例生效' : '配置已保存')
    await load()
  } catch (error: unknown) {
    showToast('error', getErrorMessage(error, '配置保存失败'))
  }
}
async function load() {
  instance.value = await request<import('~/types').InstanceData>('/api/instances/' + encodeURIComponent(instanceId))
}
async function power(action: 'start' | 'stop' | 'restart') {
  try {
    await request('/api/instances/' + encodeURIComponent(instanceId) + '/power', { method: 'POST', body: { action } })
    await load()
  } catch (error: unknown) {
    console.error(getErrorMessage(error, '电源操作失败'))
  }
}
onMounted(() => {
  load()
  loadSettings()
  timer = setInterval(load, 10000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
<template>
  <main class="relative z-10 mx-auto max-w-7xl px-8 py-12">
    <NuxtLink to="/dashboard" class="font-mono text-[10px] tracking-[0.18em] text-text-secondary hover:text-brand"
      >← BACK TO CONTROL ROOM</NuxtLink
    >
    <header class="mt-8 flex flex-wrap items-end justify-between gap-6 border-b border-border pb-7">
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
          class="border border-border px-4 py-2 font-mono text-[10px] uppercase text-text-secondary hover:border-brand hover:text-brand"
          @click="power(action as 'start' | 'stop' | 'restart')"
        >
          {{ action }}
        </button>
        <button type="button" class="border border-red-500/30 px-4 py-2 font-mono text-[10px] uppercase text-red-500 hover:bg-red-500/10" @click="showDeleteModal = true">[ DELETE ]</button>
      </div>
    </header>
    <div v-if="showDeleteModal" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4" role="dialog" aria-modal="true">
      <AtmosphereCard>
        <div class="max-w-md space-y-5">
          <p class="font-mono text-[10px] tracking-[0.2em] text-red-500">/ DESTRUCTIVE ACTION</p>
          <h2 class="font-serif text-2xl text-text-primary">确认删除实例 {{ instance?.name || instanceId }}？</h2>
          <p class="text-sm text-text-secondary">此操作将永久删除所有服务端文件，不可恢复！</p>
          <div class="flex justify-end gap-3">
            <button type="button" class="border border-border px-4 py-2 font-mono text-xs text-text-secondary hover:text-text-primary" @click="showDeleteModal = false">取消</button>
            <button type="button" class="border border-red-500/30 px-4 py-2 font-mono text-xs text-red-500 hover:bg-red-500/10" @click="deleteInstance">确认删除</button>
          </div>
        </div>
      </AtmosphereCard>
    </div>
    <nav class="mt-8 flex flex-wrap gap-6 border-b border-border font-mono text-xs">
      <button
        v-for="tab in ['console', 'monitor', 'files', 'backups', 'settings']"
        :key="tab"
        type="button"
        class="border-b-2 pb-3"
        :class="
          activeTab === tab
            ? 'border-brand text-text-primary'
            : 'border-transparent text-text-secondary hover:text-text-primary'
        "
        @click="activeTab = tab"
      >
        {{ tab }}
      </button>
    </nav>
    <section class="mt-8">
      <Console v-if="activeTab === 'console'" :instance-id="instanceId" :status="instance?.status" /><Monitor
        v-else-if="activeTab === 'monitor'"
        :instance-id="instanceId"
      /><FileManager v-else-if="activeTab === 'files'" :instance-id="instanceId" /><Backups
        v-else-if="activeTab === 'backups'"
        :instance-id="instanceId"
      />
      <div v-else class="grid gap-6 lg:grid-cols-[220px_minmax(0,1fr)]">
        <AtmosphereCard>
          <nav class="space-y-2" aria-label="设置分类">
            <p class="font-mono text-[10px] tracking-[0.2em] text-text-secondary">/ CONFIGURATION</p>
            <button type="button" class="flex w-full items-center justify-between border-l-2 px-4 py-3 text-left font-mono text-xs" :class="settingsNav === 'instance' ? 'border-brand bg-surface text-text-primary' : 'border-transparent text-text-secondary hover:bg-surface hover:text-text-primary'" @click="settingsNav = 'instance'">实例设置 <span>→</span></button>
            <button type="button" class="flex w-full items-center justify-between border-l-2 px-4 py-3 text-left font-mono text-xs" :class="settingsNav === 'properties' ? 'border-brand bg-surface text-text-primary' : 'border-transparent text-text-secondary hover:bg-surface hover:text-text-primary'" @click="settingsNav = 'properties'">服务端属性 <span>→</span></button>
          </nav>
        </AtmosphereCard>
        <AtmosphereCard>
          <form v-if="settingsNav === 'instance'" class="space-y-6" @submit.prevent="saveSettings">
          <div>
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ INSTANCE SETTINGS</p>
            <h2 class="mt-3 font-serif text-2xl text-text-primary">实例设置</h2>
          </div>
          <div class="grid gap-5 md:grid-cols-2">
            <label class="space-y-2"><span class="font-mono text-xs text-text-secondary">实例名称</span><input v-model="settings.name" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /></label>
            <label class="space-y-2"><span class="font-mono text-xs text-text-secondary">服务端端口</span><input v-model.number="settings.port" type="number" min="1" max="65535" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /></label>
            <label class="space-y-2"><span class="font-mono text-xs text-text-secondary">内存分配 (MB)</span><input v-model.number="settings.memory_mb" type="number" min="512" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /><span class="block text-xs text-text-secondary">修改后需重启实例生效</span></label>
            <label class="space-y-2"><span class="font-mono text-xs text-text-secondary">RCON 端口</span><input v-model.number="settings.rcon_port" type="number" min="1" max="65535" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /></label>
            <label class="space-y-2 md:col-span-2"><span class="font-mono text-xs text-text-secondary">RCON 密码</span><input v-model="settings.rcon_password" type="password" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /></label>
          </div>
          <div class="grid gap-4 border-t border-border pt-6 md:grid-cols-3">
            <label class="flex items-center justify-between border border-border bg-background px-4 py-3 text-xs text-text-secondary">RCON 通讯模式 <input v-model="settings.rcon_enabled" type="checkbox" class="accent-brand" /></label>
            <label class="flex items-center justify-between border border-border bg-background px-4 py-3 text-xs text-text-secondary">自动重启 <input v-model="settings.auto_restart" type="checkbox" class="accent-brand" /></label>
            <label class="flex items-center justify-between border border-border bg-background px-4 py-3 text-xs text-text-secondary">忽略 EULA <input v-model="settings.ignore_eula" type="checkbox" class="accent-brand" /></label>
          </div>
          <label v-if="settings.rcon_enabled" class="block space-y-2"><span class="font-mono text-xs text-text-secondary">RCON 密码</span><input v-model="settings.rcon_password" type="password" required class="w-full border border-border bg-background px-3 py-2 text-text-primary outline-none focus:border-brand" /></label>
          <button type="submit" :disabled="!settingsLoaded" class="border border-border px-5 py-3 font-mono text-xs tracking-[0.14em] text-text-primary transition hover:border-brand hover:text-brand disabled:cursor-not-allowed disabled:opacity-50">[ SAVE ]</button>
        </form>
        <form v-else class="space-y-6" @submit.prevent="saveSettings">
          <div class="flex items-start justify-between border-b border-border pb-5"><div><p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ SERVER.PROPERTIES</p><h2 class="mt-3 font-serif text-2xl text-text-primary">服务端属性</h2></div><button type="submit" class="border border-border px-4 py-2 font-mono text-[10px] text-text-primary hover:border-brand hover:text-brand">[ SAVE ]</button></div>
          <textarea v-model="settings.server_properties" rows="22" spellcheck="false" class="w-full resize-y border border-border bg-background p-4 font-mono text-xs leading-6 text-text-primary outline-none focus:border-brand" />
        </form>
        </AtmosphereCard>
      </div>
      <div v-if="toast" class="fixed bottom-6 right-6 z-50 border border-border bg-surface px-5 py-3 font-mono text-xs text-text-primary">{{ toast.message }}</div>
    </section>
  </main>
</template>
