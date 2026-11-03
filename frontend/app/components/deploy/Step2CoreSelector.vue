<script setup lang="ts">
import VersionWizardModal from './VersionWizardModal.vue'
type Core = { id: string; name: string; desc: string; category: string }
type Selection = { core: string; version: string; build: string; source?: string }
const categories = ['插件服务端', '模组服务端', '代理服务端', '基岩服务端', '原版服务端', '混合服务端']
const cores: Core[] = [
  { id: 'arclight', name: 'Arclight', desc: '混合端（推荐）', category: '混合服务端' },
  { id: 'catserver', name: 'CatServer', desc: '混合端', category: '混合服务端' },
  { id: 'fabric', name: 'Fabric', desc: '轻量模组加载器', category: '模组服务端' },
  { id: 'forge', name: 'Forge', desc: '经典模组平台', category: '模组服务端' },
  { id: 'neoforge', name: 'NeoForge', desc: '新一代模组生态', category: '模组服务端' },
  { id: 'quilt', name: 'Quilt', desc: 'Fabric 衍生加载器', category: '模组服务端' },
  { id: 'bungeecord', name: 'BungeeCord', desc: '代理服务端', category: '代理服务端' },
  { id: 'velocity', name: 'Velocity', desc: '现代代理服务端', category: '代理服务端' },
  { id: 'folia', name: 'Folia', desc: '多线程区域并行', category: '插件服务端' },
  { id: 'leaves', name: 'Leaves', desc: 'Paper 衍生服务端', category: '插件服务端' },
  { id: 'paper', name: 'Paper', desc: '高性能插件服务端（推荐）', category: '插件服务端' },
  { id: 'purpur', name: 'Purpur', desc: '高可定制服务端', category: '插件服务端' },
  { id: 'spigot', name: 'Spigot', desc: '经典插件服务端', category: '插件服务端' },
  { id: 'spongevanilla', name: 'SpongeVanilla', desc: 'Sponge 插件服务端', category: '插件服务端' },
  { id: 'nukkit', name: 'Nukkit', desc: '基岩版服务端', category: '基岩服务端' },
  { id: 'pocketmine', name: 'PocketMine', desc: '基岩版服务端', category: '基岩服务端' },
  { id: 'vanilla', name: 'Vanilla', desc: '官方原版服务端', category: '原版服务端' },
  { id: 'spongeforge', name: 'SpongeForge', desc: 'Forge 混合生态', category: '混合服务端' },
  { id: 'spongeneo', name: 'SpongeNeo', desc: 'NeoForge 混合生态', category: '混合服务端' },
]
const versions = ref<string[]>([])
const builds = ref<Record<string, string[]>>({})
const buildSources = ref<Record<string, string>>({})
const loadError = ref('')
const isLoading = ref(false)
const { request, getErrorMessage } = useApi()
async function loadVersions(core: Core) {
  loadError.value = ''
  versions.value = []
  isLoading.value = true
  try {
    const response = await request<{ versions?: ({ id?: string } | string)[] } | ({ id?: string } | string)[]>(
      `/api/resources/cores/${core.id}/versions`,
    )
    const rawVersions = Array.isArray(response) ? response : (response.versions ?? [])
    versions.value = rawVersions.map((item) => (typeof item === 'string' ? item : (item.id ?? ''))).filter(Boolean)
  } catch (error: unknown) {
    loadError.value = getErrorMessage(error, '版本加载失败')
    versions.value = []
  } finally {
    isLoading.value = false
  }
}
async function loadBuilds(core: Core, version: string) {
  loadError.value = ''
  try {
    const response = await request<
      { builds?: ({ id?: string; source?: string } | string)[] } | ({ id?: string; source?: string } | string)[]
    >(`/api/resources/cores/${core.id}/versions/${encodeURIComponent(version)}/builds`)
    const rawBuilds = Array.isArray(response) ? response : (response.builds ?? [])
    for (const item of rawBuilds) {
      if (typeof item !== 'string' && item.id)
        buildSources.value[`${core.id}:${version}:${item.id}`] = item.source || 'fastmirror'
    }
    builds.value = {
      ...builds.value,
      [version]: rawBuilds.map((item) => (typeof item === 'string' ? item : (item.id ?? ''))).filter(Boolean),
    }
  } catch (error: unknown) {
    loadError.value = getErrorMessage(error, '构建加载失败')
    builds.value = { ...builds.value, [version]: [] }
  }
}
const activeCategory = ref(categories[0])
const selectedCore = ref<Core | null>(null)
const selected = ref<Selection | null>(null)
const isModalOpen = ref(false)
const filteredCores = computed(() => cores.filter((core) => core.category === activeCategory.value))
async function openWizard(core: Core) {
  builds.value = {}
  buildSources.value = {}
  selectedCore.value = core
  isModalOpen.value = true
  await loadVersions(core)
}
function handleSelection(value: Selection) {
  selected.value = value
  isModalOpen.value = false
  emit('select', {
    ...value,
    source: buildSources.value[`${value.core.toLowerCase()}:${value.version}:${value.build}`] || 'fastmirror',
  })
}
const emit = defineEmits<{ select: [value: Selection] }>()
</script>
<template>
  <section class="flex min-h-[600px] gap-8">
    <aside class="w-48 shrink-0">
      <p class="mb-4 font-mono text-[10px] tracking-[0.24em] text-text-secondary">/ DEPLOYMENT TYPES</p>
      <nav class="flex flex-col">
        <button
          v-for="category in categories"
          :key="category"
          type="button"
          class="relative border-l-2 border-transparent px-4 py-3 text-left text-sm text-text-secondary transition-colors hover:bg-surface/60 hover:text-text-primary"
          :class="activeCategory === category ? 'border-brand bg-surface text-text-primary' : ''"
          @click="activeCategory = category"
        >
          {{ category }}
        </button>
      </nav>
    </aside>
    <main class="min-w-0 flex-1">
      <header class="mb-6 flex items-end justify-between gap-4 border-b border-border pb-5">
        <div>
          <p class="mb-2 font-mono text-[10px] tracking-[0.24em] text-text-secondary">/ CORE LIBRARY</p>
          <h2 class="font-serif text-2xl text-text-primary">选择服务端核心</h2>
        </div>
        <span class="font-mono text-[10px] tracking-[0.18em] text-text-secondary"
          >{{ filteredCores.length.toString().padStart(2, '0') }} AVAILABLE</span
        >
      </header>
      <p v-if="loadError" class="mb-4 border border-red-400/40 px-4 py-3 text-xs text-red-300">! {{ loadError }}</p>
      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <button
          v-for="core in filteredCores"
          :key="core.id"
          type="button"
          class="group cursor-pointer border border-border bg-surface/50 p-5 text-left transition-all duration-300 hover:-translate-y-1 hover:border-brand/60 hover:bg-surface"
          @click="openWizard(core)"
        >
          <div class="mb-8 flex items-start justify-between">
            <span class="font-mono text-lg font-bold text-text-primary">{{ core.name }}</span
            ><span
              aria-hidden="true"
              class="mt-1 h-2 w-2 border border-text-secondary/60 transition-colors group-hover:border-brand group-hover:bg-brand"
            />
          </div>
          <p class="text-xs text-text-secondary">{{ core.desc }}</p>
        </button>
      </div>
      <p v-if="selected" class="mt-6 border-l-2 border-brand bg-brand/15 px-4 py-3 font-mono text-xs text-text-primary">
        已选择：{{ selected.core }} {{ selected.version }} ({{ selected.build }})
      </p>
    </main>
    <VersionWizardModal
      :open="isModalOpen"
      :core="selectedCore"
      :versions="versions"
      :builds="builds"
      :loading="isLoading"
      :error="loadError"
      @close="isModalOpen = false"
      @select="handleSelection"
      @version-select="selectedCore && loadBuilds(selectedCore, $event)"
    />
  </section>
</template>
