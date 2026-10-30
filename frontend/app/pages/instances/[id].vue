<script setup lang="ts">

import Console from '~/components/instance/Console.vue'
import Monitor from '~/components/instance/Monitor.vue'
import FileManager from '~/components/instance/FileManager.vue'
import Backups from '~/components/instance/Backups.vue'
definePageMeta({ middleware: 'auth' })
const route = useRoute(); const instanceId = String(route.params.id); const instance = ref<import("~/types").InstanceData | null>(null); const activeTab = ref('console'); let timer: ReturnType<typeof setInterval> | undefined
const { request, getErrorMessage } = useApi()
async function load() { instance.value = await request<import("~/types").InstanceData>('/api/instances/' + encodeURIComponent(instanceId)) }
async function power(action: 'start' | 'stop' | 'restart') { try { await request('/api/instances/' + encodeURIComponent(instanceId) + '/power', { method: 'POST', body: { action } }); await load() } catch (error: unknown) { console.error(getErrorMessage(error, '电源操作失败')) } }
onMounted(() => { load(); timer = setInterval(load, 10000) }); onUnmounted(() => { if (timer) clearInterval(timer) })
</script>
<template>
  <main class="relative z-10 mx-auto max-w-7xl px-8 py-12"><NuxtLink to="/dashboard" class="font-mono text-[10px] tracking-[0.18em] text-text-secondary hover:text-brand">← BACK TO CONTROL ROOM</NuxtLink>
    <header class="mt-8 flex flex-wrap items-end justify-between gap-6 border-b border-border pb-7"><div><p class="font-mono text-[10px] tracking-[0.22em] text-text-secondary">/ INSTANCE CONTROL TERMINAL</p><h1 class="mt-3 font-serif text-4xl text-text-primary">{{ instance?.name || instanceId }}</h1><p class="mt-2 font-mono text-xs text-text-secondary">PORT {{ instance?.port || '—' }} · {{ instance?.status || 'LOADING' }}</p></div><div class="flex gap-2"><button v-for="action in ['start', 'restart', 'stop']" :key="action" type="button" class="border border-border px-4 py-2 font-mono text-[10px] uppercase text-text-secondary hover:border-brand hover:text-brand" @click="power(action as 'start' | 'stop' | 'restart')">{{ action }}</button></div></header>
    <nav class="mt-8 flex flex-wrap gap-6 border-b border-border font-mono text-xs"><button v-for="tab in ['console', 'monitor', 'files', 'backups', 'settings']" :key="tab" type="button" class="border-b-2 pb-3" :class="activeTab === tab ? 'border-brand text-text-primary' : 'border-transparent text-text-secondary hover:text-text-primary'" @click="activeTab = tab">{{ tab }}</button></nav>
    <section class="mt-8"><Console v-if="activeTab === 'console'" :instance-id="instanceId" :status="instance?.status" /><Monitor v-else-if="activeTab === 'monitor'" :instance-id="instanceId" /><FileManager v-else-if="activeTab === 'files'" :instance-id="instanceId" /><Backups v-else-if="activeTab === 'backups'" :instance-id="instanceId" /><section v-else class="border border-border bg-surface/50 p-7 shadow-2xl"><p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ INSTANCE SETTINGS</p><h2 class="mt-3 font-serif text-2xl text-text-primary">实例设置</h2><p class="mt-3 text-sm text-text-secondary">电源、RCON 和启动策略设置将在后续接入；当前控制台、电源、监控、文件和备份功能已可使用。</p></section></section>
  </main>
</template>