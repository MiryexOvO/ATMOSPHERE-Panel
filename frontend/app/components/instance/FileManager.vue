<script setup lang="ts">

const props = defineProps<{ instanceId: string }>()
type Entry = { name: string; path: string; type: 'file' | 'directory'; size?: number }
const entries = ref<Entry[]>([])
const currentPath = ref('/')
const selectedPath = ref('')
const content = ref('')
const message = ref('')
const loading = ref(false)
async function list(path = '/') { loading.value = true; try { const result = await $fetch<{ entries: Entry[] }>("/api/instances/" + encodeURIComponent(props.instanceId) + "/files", { credentials: 'include', query: { path } }); entries.value = result.entries; currentPath.value = path } finally { loading.value = false } }
async function open(entry: Entry) { if (entry.type === 'directory') return list(entry.path); selectedPath.value = entry.path; const result = await $fetch<{ content: string }>("/api/instances/" + encodeURIComponent(props.instanceId) + "/files/content", { credentials: 'include', query: { path: entry.path } }); content.value = result.content; message.value = '' }
async function save() { await $fetch("/api/instances/" + encodeURIComponent(props.instanceId) + "/files/save", { method: 'POST', credentials: 'include', body: { path: selectedPath.value, content: content.value } }); message.value = '已保存 · ' + selectedPath.value }
onMounted(() => list())
</script>
<template>
  <section class="grid min-h-[480px] border border-border bg-surface/30 md:grid-cols-[240px_1fr]">
    <aside class="border-b border-border p-4 md:border-b-0 md:border-r">
      <div class="mb-4 flex items-center justify-between"><span class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">FILES / {{ currentPath }}</span><button type="button" class="text-brand" @click="list(currentPath)">↻</button></div>
      <button v-if="currentPath !== '/'" type="button" class="mb-2 block font-mono text-xs text-text-secondary hover:text-brand" @click="list(currentPath.split('/').slice(0, -1).join('/') || '/')">../</button>
      <button v-for="entry in entries" :key="entry.path" type="button" class="flex w-full items-center justify-between border-b border-border/50 px-2 py-2 text-left font-mono text-xs hover:bg-background" @click="open(entry)"><span :class="entry.type === 'directory' ? 'text-brand' : 'text-text-primary'">{{ entry.type === 'directory' ? '▸ ' : '· ' }}{{ entry.name }}</span><span v-if="entry.type === 'file'" class="text-[9px] text-text-secondary">{{ entry.size }}B</span></button>
    </aside>
    <div class="flex min-h-[480px] flex-col"><header class="flex items-center justify-between border-b border-border px-4 py-3"><span class="font-mono text-xs text-text-secondary">{{ selectedPath || '选择文件' }}</span><button type="button" class="border border-brand px-3 py-1 font-mono text-[10px] text-brand hover:bg-brand/10 disabled:opacity-40" :disabled="!selectedPath" @click="save">保存</button></header><textarea v-model="content" :disabled="!selectedPath" class="min-h-0 flex-1 resize-none bg-black/20 p-5 font-mono text-xs leading-6 text-text-primary outline-none placeholder:text-text-secondary" placeholder="选择一个文本文件开始编辑" spellcheck="false" /><p class="px-4 py-2 font-mono text-[10px] text-data-live">{{ message }}</p></div>
  </section>
</template>