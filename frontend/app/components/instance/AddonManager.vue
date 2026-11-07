<script setup lang="ts">
import MechanicalSwitch from '~/components/ui/MechanicalSwitch.vue'
const { t } = useI18n()
const props = defineProps<{ instanceId: string; kind: 'mods' | 'plugins' }>()
const { instanceRequest, getErrorMessage } = useInstanceApi(() => props.instanceId)
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
const addonPath = computed(() => `/addons/${props.kind}`)
let loadVersion = 0
// 加载时保留卡片占位；只接收当前分类的最新响应。
async function load() {
  const version = ++loadVersion
  loading.value = true
  try {
    const data = await instanceRequest<{ items: Addon[]; running: boolean; supported: boolean }>(addonPath.value)
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
    const data = await instanceRequest<{ changed: string[] }>(addonPath.value, {
      method: 'POST',
      body: item ? { file: item.file, enabled: !item.enabled } : { auto_client: true },
    })
    message.value = t('msg_updated') + data.changed.length
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
        <p class="font-mono text-xs tracking-widest text-brand">/ {{ kind.toUpperCase() }} REGISTRY</p>
        <h2 class="mt-3 font-serif text-2xl">
          {{ kind === 'mods' ? t('msg_mod_list') : t('msg_plugin_list') }}
        </h2>
      </div>
      <div class="flex gap-4 text-xs text-brand">
        <button v-if="kind === 'mods'" :disabled="loading || running || busy" @click="toggle()">
          {{ t('msg_disable_client_mods') }}</button
        ><button @click="load">{{ t('msg_refresh') }}</button>
      </div>
    </header>
    <p class="mt-5 text-xs leading-6 text-text-secondary">
      {{ t('msg_stop_the_server_before_changing_add_ons_auto') }}
    </p>
    <p v-if="message" role="status" class="mt-4 text-sm text-brand">{{ message }}</p>
    <input
      v-model="search"
      :placeholder="t('msg_search_name_or_file')"
      class="mt-6 w-full border border-border bg-transparent p-3 text-sm outline-none focus:border-brand"
    />
    <div ref="listStart" class="scroll-mt-24" />
    <div v-if="loading" class="addon-loading mt-5 space-y-4" role="status">
      <p class="text-xs text-text-secondary">{{ t('msg_loading_add_ons') }}</p>
      <div v-for="row in 5" :key="row" class="border-b border-border py-5">
        <span class="addon-skeleton block h-3 w-2/5" /><span class="addon-skeleton mt-4 block h-2 w-3/5" />
      </div>
    </div>
    <p v-else-if="kind === 'plugins' && !supported && !items.length" class="py-8 text-sm text-text-secondary">
      {{ t('msg_this_core_does_not_support_plugins_or_no_plu') }}
    </p>
    <p v-else-if="!filtered.length" class="py-8 text-sm text-text-secondary">
      {{ t('msg_no_files_detected') }}
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
      :aria-label="t('msg_add_on_pages')"
      class="mt-5 flex flex-wrap items-center justify-between gap-4 border-t border-border pt-5 text-xs"
    >
      <span class="font-mono text-text-secondary"
        >{{ (page - 1) * pageSize + 1 }}–{{ Math.min(page * pageSize, filtered.length) }} / {{ filtered.length }} ·
        {{ t('msg_20_per_page') }}</span
      >
      <div class="flex items-center gap-4">
        <button
          type="button"
          :disabled="page <= 1"
          class="text-brand disabled:opacity-30"
          @click="changePage(page - 1)"
        >
          {{ t('msg_prev') }}</button
        ><span class="font-mono">{{ page }} / {{ pageCount }}</span
        ><button
          type="button"
          :disabled="page >= pageCount"
          class="text-brand disabled:opacity-30"
          @click="changePage(page + 1)"
        >
          {{ t('msg_next') }}
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
