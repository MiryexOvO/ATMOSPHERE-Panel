<script setup lang="ts">
import { onMounted, ref } from 'vue'
const props = defineProps<{ instanceId: string }>()
type Backup = { name: string; size: number; created_at: number }
const items = ref<Backup[]>([])
const loading = ref(false)
const message = ref('')
async function load() { const result = await $fetch<{ backups: Backup[] }>("/api/instances/" + encodeURIComponent(props.instanceId) + "/backups", { credentials: 'include' }); items.value = result.backups }
async function create() { loading.value = true; message.value = ''; try { const result = await $fetch<{ name: string }>("/api/instances/" + encodeURIComponent(props.instanceId) + "/backups", { method: 'POST', credentials: 'include' }); message.value = '已创建：' + result.name; await load() } catch (error: any) { message.value = error?.data?.message || '备份失败' } finally { loading.value = false } }
onMounted(load)
</script>
<template>
  <section class="border border-border bg-surface/30 p-6">
    <header class="flex items-center justify-between border-b border-border pb-5"><div><p class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">BACKUP ARCHIVE</p><h2 class="mt-2 font-serif text-2xl text-text-primary">备份与恢复</h2></div><button type="button" class="border border-brand px-4 py-2 font-mono text-[10px] text-brand hover:bg-brand/10 disabled:opacity-50" :disabled="loading" @click="create">{{ loading ? '处理中…' : '一键备份' }}</button></header>
    <p v-if="message" class="mt-4 font-mono text-xs text-data-live">{{ message }}</p>
    <div v-if="!items.length" class="py-16 text-center font-mono text-xs text-text-secondary">暂无备份记录</div>
    <div v-else class="mt-5 divide-y divide-border"> <div v-for="item in items" :key="item.name" class="flex items-center justify-between py-4 font-mono text-xs"><span class="text-text-primary">{{ item.name }}</span><span class="text-text-secondary">{{ Math.ceil(item.size / 1024) }} KB · {{ new Date(item.created_at * 1000).toLocaleString() }}</span></div></div>
  </section>
</template>