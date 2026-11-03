<script setup lang="ts">
import MechanicalSwitch from '~/components/ui/MechanicalSwitch.vue'
const props = defineProps<{ instanceId: string; kind: 'mods' | 'plugins' }>()
const tr = usePanelText(),
  { request, getErrorMessage } = useApi()
type Addon = {
  file: string
  name: string
  version: string
  enabled: boolean
  client_only: boolean
  description: string
}
const items = ref<Addon[]>([]),
  running = ref(false),
  supported = ref(true),
  busy = ref(false),
  message = ref(''),
  search = ref('')
const loading = ref(true),
  page = ref(1)
const listStart = ref<HTMLElement | null>(null)
const pageSize = 20
const filtered = computed(() =>
  items.value.filter((item) => (item.name + ' ' + item.file).toLowerCase().includes(search.value.toLowerCase())),
)
const pageCount = computed(() => Math.max(1, Math.ceil(filtered.value.length / pageSize)))
const pageItems = computed(() => filtered.value.slice((page.value - 1) * pageSize, page.value * pageSize))
// 翻页后回到列表开头，便于继续浏览下一批扩展。
function changePage(next: number) {
  page.value = Math.max(1, Math.min(pageCount.value, next))
  nextTick(() =>
    listStart.value?.scrollIntoView({
      block: 'start',
      behavior: window.matchMedia('(prefers-reduced-motion: reduce)').matches ? 'auto' : 'smooth',
    }),
  )
}
watch(search, () => {
  page.value = 1
})
watch(pageCount, (count) => {
  page.value = Math.min(page.value, count)
})
const base = computed(() => `/api/instances/${encodeURIComponent(props.instanceId)}/addons/${props.kind}`)
let loadVersion = 0
// 加载时保留卡片占位；只接收当前分类的最新响应。
async function load() {
  const version = ++loadVersion
  loading.value = true
  try {
    const data = await request<{ items: Addon[]; running: boolean; supported: boolean }>(base.value)
    if (version !== loadVersion) return
    items.value = data.items
    running.value = data.running
    supported.value = data.supported
  } catch (error) {
    if (version === loadVersion) message.value = getErrorMessage(error)
  } finally {
    if (version === loadVersion) loading.value = false
  }
}
// 停服后重命名文件，保留所有组件数据。
async function toggle(item?: Addon) {
  busy.value = true
  message.value = ''
  try {
    const data = await request<{ changed: string[] }>(base.value, {
      method: 'POST',
      body: item ? { file: item.file, enabled: !item.enabled } : { auto_client: true },
    })
    message.value = tr('已更新 ', 'UPDATED ', '更新済み ') + data.changed.length
    await load()
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
watch(
  () => [props.instanceId, props.kind],
  () => {
    message.value = ''
    page.value = 1
    items.value = []
    load()
  },
)
onUnmounted(() => {
  loadVersion++
})
onMounted(load)
</script>
<template>
  <AtmosphereCard :interactive="false" :aria-busy="loading" data-addon-manager
    ><header class="flex flex-wrap items-center justify-between gap-4">
      <div>
        <p class="font-mono text-xs tracking-widest text-brand">/ {{ kind.toUpperCase() }} INVENTORY</p>
        <h2 class="mt-3 font-serif text-2xl">
          {{
            kind === 'mods' ? tr('模组列表', 'MOD LIST', 'MOD 一覧') : tr('插件列表', 'PLUGIN LIST', 'プラグイン一覧')
          }}
        </h2>
      </div>
      <div class="flex gap-4 text-xs text-brand">
        <button v-if="kind === 'mods'" :disabled="loading || running || busy" @click="toggle()">
          {{ tr('关闭客户端模组', 'DISABLE CLIENT MODS', 'クライアント MOD を無効化') }}</button
        ><button @click="load">{{ tr('刷新', 'REFRESH', '更新') }}</button>
      </div>
    </header>
    <p class="mt-5 text-xs leading-6 text-text-secondary">
      {{
        tr(
          '启停需先停止实例。自动检测仅关闭元数据明确标记为客户端专用的模组，未知项目保持原样。',
          'Stop the server before changing add-ons. Auto-detection only disables explicitly marked client-only mods.',
          '変更前に停止してください。自動検出は明示的にクライアント専用とされた MOD のみ無効化します。',
        )
      }}
    </p>
    <p v-if="message" role="status" class="mt-4 text-sm text-brand">{{ message }}</p>
    <input
      v-model="search"
      :placeholder="tr('搜索名称或文件', 'SEARCH NAME OR FILE', '名前・ファイルを検索')"
      class="mt-6 w-full border border-border bg-transparent p-3 text-sm outline-none focus:border-brand"
    />
    <div ref="listStart" class="scroll-mt-24" />
    <div v-if="loading" class="addon-loading mt-5 space-y-4" role="status">
      <p class="text-xs text-text-secondary">{{ tr('正在读取扩展列表…', 'LOADING ADD-ONS…', '一覧を読み込み中…') }}</p>
      <div v-for="row in 5" :key="row" class="border-b border-border py-5">
        <span class="addon-skeleton block h-3 w-2/5" /><span class="addon-skeleton mt-4 block h-2 w-3/5" />
      </div>
    </div>
    <p v-else-if="kind === 'plugins' && !supported && !items.length" class="py-8 text-sm text-text-secondary">
      {{
        tr(
          '该核心不支持插件或未检测到插件列表。',
          'This core does not support plugins, or no plugins were detected.',
          'プラグイン非対応、または一覧が検出されませんでした。',
        )
      }}
    </p>
    <p v-else-if="!filtered.length" class="py-8 text-sm text-text-secondary">
      {{ tr('未检测到文件', 'NO FILES DETECTED', 'ファイルがありません') }}
    </p>
    <div
      v-for="item in loading ? [] : pageItems"
      data-addon-row
      :key="item.file"
      class="flex items-center justify-between gap-5 border-b border-border py-5"
    >
      <div class="min-w-0">
        <h3 class="text-sm">
          {{ item.name }} <span class="ml-3 font-mono text-xs text-brand">{{ item.version }}</span>
        </h3>
        <p class="mt-2 font-mono text-xs break-all text-text-secondary">{{ item.file }}</p>
        <p v-if="item.client_only" class="mt-2 text-xs text-brand">CLIENT ONLY</p>
        <p v-if="item.description" class="mt-2 text-xs text-amber-300">{{ item.description }}</p>
      </div>
      <MechanicalSwitch
        :model-value="item.enabled"
        :label="item.name"
        :disabled="loading || running || busy"
        @update:model-value="toggle(item)"
      />
    </div>
    <nav
      v-if="!loading && filtered.length"
      :aria-label="tr('扩展分页', 'ADD-ON PAGES', 'ページ切替')"
      class="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-5 text-xs"
    >
      <span class="font-mono text-text-secondary"
        >{{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, filtered.length) }} / {{ filtered.length }} ·
        {{ tr('每页20项', '20 PER PAGE', '20 件/ページ') }}</span
      >
      <div class="flex items-center gap-4">
        <button
          type="button"
          :disabled="page <= 1"
          class="text-brand disabled:opacity-30"
          @click="changePage(page - 1)"
        >
          {{ tr('上一页', 'PREV', '前へ') }}</button
        ><span class="font-mono">{{ page }} / {{ pageCount }}</span
        ><button
          type="button"
          :disabled="page >= pageCount"
          class="text-brand disabled:opacity-30"
          @click="changePage(page + 1)"
        >
          {{ tr('下一页', 'NEXT', '次へ') }}
        </button>
      </div>
    </nav></AtmosphereCard
  >
</template>

<style scoped>
/* 低对比占位避免异步加载时出现空卡片。 */
.addon-loading {
  min-height: 380px;
}
.addon-skeleton {
  background: color-mix(in srgb, var(--text-secondary) 12%, transparent);
  animation: addon-pulse 1.8s ease-in-out infinite;
}
@keyframes addon-pulse {
  50% {
    opacity: 0.35;
  }
}
@media (prefers-reduced-motion: reduce) {
  .addon-skeleton {
    animation: none;
  }
}
</style>
