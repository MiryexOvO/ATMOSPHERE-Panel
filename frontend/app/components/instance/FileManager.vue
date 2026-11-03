<script setup lang="ts">
const props = defineProps<{ instanceId: string }>()
const { t } = useI18n()
const { request, getErrorMessage } = useApi()
const original = ref('')
const activeEntry = ref<Entry | null>(null)
const pending = ref<{ action: string; path: string } | null>(null)
const destination = ref('')
const uploadInput = ref<HTMLInputElement | null>(null)
const working = ref(false)

type Entry = { name: string; path: string; type: 'file' | 'directory'; size?: number }
const entries = ref<Entry[]>([])
const currentPath = ref('/')
const selectedPath = ref('')
const content = ref('')
const message = ref('')
const loading = ref(false)
async function list(path = '/') {
  loading.value = true
  try {
    const result = await $fetch<{ entries: Entry[] }>(
      '/api/instances/' + encodeURIComponent(props.instanceId) + '/files',
      { credentials: 'include', query: { path } },
    )
    entries.value = result.entries
    currentPath.value = path
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    loading.value = false
  }
}
async function open(entry: Entry) {
  if (content.value !== original.value && !window.confirm(t('fileUnsaved'))) return
  activeEntry.value = entry
  if (entry.type === 'directory') return list(entry.path)
  selectedPath.value = entry.path
  try {
    const result = await $fetch<{ content: string }>(
      '/api/instances/' + encodeURIComponent(props.instanceId) + '/files/content',
      { credentials: 'include', query: { path: entry.path } },
    )
    content.value = result.content
    original.value = result.content
    message.value = ''
  } catch (error) {
    message.value = getErrorMessage(error)
    selectedPath.value = ''
  }
}
async function save() {
  working.value = true
  try {
    await $fetch('/api/instances/' + encodeURIComponent(props.instanceId) + '/files/save', {
      method: 'POST',
      credentials: 'include',
      body: { path: selectedPath.value, content: content.value },
    })
    original.value = content.value
    message.value = t('fileDone') + ' · ' + selectedPath.value
    await list(currentPath.value)
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    working.value = false
  }
}
// 文件操作先展示明确目标，再提交变更。
function prepare(action: string, entry?: Entry) {
  const path = entry?.path || currentPath.value
  pending.value = { action, path }
  destination.value =
    action === 'mkdir' || action === 'create'
      ? currentPath.value.replace(/\/$/, '') + '/'
      : action === 'copy'
        ? path + '.copy'
        : action === 'compress'
          ? path + '.zip'
          : action === 'extract'
            ? path.replace(/\.(zip|tar\.gz|tgz)$/i, '') + '-unpacked'
            : path
}
async function commit() {
  if (!pending.value) return
  working.value = true
  try {
    const value = pending.value
    await request(`/api/instances/${encodeURIComponent(props.instanceId)}/files/action`, {
      method: 'POST',
      body: {
        action: value.action,
        path: ['mkdir', 'create'].includes(value.action) ? destination.value : value.path,
        destination: destination.value,
      },
    })
    pending.value = null
    if (value.path === selectedPath.value) {
      selectedPath.value = ''
      content.value = ''
      original.value = ''
    }
    activeEntry.value = null
    if (
      value.action === 'delete' &&
      (currentPath.value === value.path || currentPath.value.startsWith(value.path + '/'))
    )
      currentPath.value = value.path.split('/').slice(0, -1).join('/') || '/'
    await list(currentPath.value)
    message.value = t('fileDone')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    working.value = false
  }
}
// 点击和拖放共用上传入口，不覆盖已有文件。
async function upload(files: FileList | null | undefined) {
  if (!files?.length || working.value) return
  working.value = true
  try {
    for (const file of Array.from(files)) {
      const form = new FormData()
      form.set('path', currentPath.value)
      form.set('file', file)
      await request(`/api/instances/${encodeURIComponent(props.instanceId)}/files/upload`, {
        method: 'POST',
        body: form,
      })
    }
    await list(currentPath.value)
    message.value = t('fileDone')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    working.value = false
    if (uploadInput.value) uploadInput.value.value = ''
  }
}
function download() {
  if (activeEntry.value?.type === 'file')
    window.location.href = `/api/instances/${encodeURIComponent(props.instanceId)}/files/download?path=${encodeURIComponent(activeEntry.value.path)}`
}
onMounted(() => list())
</script>
<template>
  <AtmosphereCard :interactive="false">
    <div class="mb-5 flex flex-wrap gap-2" @dragover.prevent @drop.prevent="upload($event.dataTransfer?.files)">
      <button
        v-for="item in [
          { action: 'create', label: 'fileNew' },
          { action: 'mkdir', label: 'fileFolder' },
        ]"
        :key="item.action"
        type="button"
        class="file-tool"
        :disabled="working"
        @click="prepare(item.action)"
      >
        {{ t(item.label) }}
      </button>
      <button type="button" class="file-tool" :disabled="working" @click="uploadInput?.click()">
        {{ t('fileUpload') }}
      </button>
      <input
        ref="uploadInput"
        type="file"
        multiple
        class="hidden"
        @change="upload(($event.target as HTMLInputElement).files)"
      />
      <span class="ml-auto font-mono text-xs break-all text-text-secondary">{{ currentPath }}</span>
    </div>
    <p v-if="message" role="status" class="mb-4 text-sm text-brand">{{ message }}</p>
    <div v-if="activeEntry" class="mb-4 flex flex-wrap items-center gap-2 border-y border-border py-3">
      <span class="mr-2 text-xs break-all text-text-secondary">{{ activeEntry.name }}</span>
      <button
        v-for="item in [
          { action: 'rename', label: 'fileRename' },
          { action: 'copy', label: 'fileCopy' },
          { action: 'compress', label: 'fileCompress' },
          { action: 'delete', label: 'fileDelete' },
        ]"
        :key="item.action"
        type="button"
        class="file-tool"
        :disabled="working"
        @click="prepare(item.action, activeEntry)"
      >
        {{ t(item.label) }}
      </button>
      <button
        v-if="activeEntry.type === 'file' && /\.(zip|tgz|tar\.gz)$/i.test(activeEntry.name)"
        type="button"
        class="file-tool"
        @click="prepare('extract', activeEntry)"
      >
        {{ t('fileExtract') }}
      </button>
      <button v-if="activeEntry.type === 'file'" type="button" class="file-tool" @click="download">
        {{ t('fileDownload') }}
      </button>
    </div>
    <section
      class="grid min-h-[480px] border border-border md:grid-cols-[300px_1fr]"
      @dragover.prevent
      @drop.prevent="upload($event.dataTransfer?.files)"
    >
      <aside class="max-h-[650px] overflow-y-auto border-b border-border p-4 md:border-r md:border-b-0">
        <div class="mb-4 flex items-center justify-between">
          <span class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">FILES / {{ currentPath }}</span
          ><button type="button" class="text-brand" @click="list(currentPath)">↻</button>
        </div>
        <button
          v-if="currentPath !== '/'"
          type="button"
          class="mb-2 block font-mono text-xs text-text-secondary hover:text-brand"
          @click="list(currentPath.split('/').slice(0, -1).join('/') || '/')"
        >
          ../
        </button>
        <p v-if="!loading && !entries.length" class="py-8 text-center text-xs text-text-secondary">
          {{ t('fileEmpty') }}
        </p>
        <div
          v-for="entry in entries"
          :key="entry.path"
          class="flex border-b border-border/50"
          :class="activeEntry?.path === entry.path ? 'bg-brand/10' : ''"
        >
          <button
            type="button"
            class="min-w-0 flex-1 truncate px-2 py-3 text-left font-mono text-xs text-text-primary hover:text-brand"
            @click="open(entry)"
          >
            {{ entry.type === 'directory' ? '▸ ' : '· ' }}{{ entry.name }}
          </button>
          <button
            type="button"
            class="px-3 text-text-secondary hover:text-brand"
            :aria-label="entry.name"
            @click="activeEntry = entry"
          >
            ⋯
          </button>
        </div>
      </aside>
      <div class="flex min-h-[480px] flex-col">
        <header class="flex items-center justify-between border-b border-border px-4 py-3">
          <span class="font-mono text-xs text-text-secondary">{{ selectedPath || t('fileSelect') }}</span
          ><button
            type="button"
            class="border border-brand px-3 py-1 font-mono text-[10px] text-brand hover:bg-brand/10 disabled:opacity-40"
            :disabled="!selectedPath || working"
            @click="save"
          >
            {{ t('fileSave') }}
          </button>
        </header>
        <textarea
          v-model="content"
          :disabled="!selectedPath || working"
          class="min-h-0 flex-1 resize-none bg-black/20 p-5 font-mono text-xs leading-6 text-text-primary outline-none placeholder:text-text-secondary"
          :placeholder="t('fileSelect')"
          spellcheck="false"
        />
        <p class="px-4 py-2 font-mono text-[10px] text-data-live">{{ message }}</p>
      </div>
    </section>
    <Teleport to="body"
      ><div v-if="pending" class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-5">
        <AtmosphereCard :interactive="false" class="w-full max-w-xl">
          <h3 class="font-serif text-xl">{{ pending.action.toUpperCase() }}</h3>
          <p class="mt-4 text-sm break-all text-text-secondary">
            {{ pending.action === 'delete' ? t('fileDeleteHint') : t('fileTarget') }} {{ pending.path }}
          </p>
          <input
            v-if="pending.action !== 'delete'"
            v-model="destination"
            class="mt-5 w-full border border-border bg-background px-3 py-3 font-mono text-sm"
            :aria-label="t('fileTarget')"
          />
          <div class="mt-6 flex justify-end gap-3">
            <button type="button" class="file-tool" :disabled="working" @click="pending = null">
              {{ t('fileCancel') }}</button
            ><button type="button" class="file-tool" :disabled="working" @click="commit">{{ t('fileConfirm') }}</button>
          </div>
        </AtmosphereCard>
      </div></Teleport
    >
  </AtmosphereCard>
</template>
<style scoped>
/* 文件工具栏统一紧凑反馈。 */
.file-tool {
  border: 1px solid var(--border);
  padding: 7px 10px;
  color: var(--brand);
  font-size: 11px;
  transition:
    border-color 180ms ease,
    background 180ms ease;
}
.file-tool:hover {
  border-color: var(--brand);
  background: color-mix(in srgb, var(--brand) 7%, transparent);
}
.file-tool:disabled {
  opacity: 0.4;
  cursor: wait;
}
</style>
