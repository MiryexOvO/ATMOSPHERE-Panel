<script setup lang="ts">
import VersionWizardModal from './VersionWizardModal.vue'
const { t } = useI18n()
type Core = { id: string; name: string; desc: string; category: string }
type Selection = { core: string; version: string; build: string; source?: string }
// 分类使用稳定的 ASCII 键，展示文案来自 i18n。
const categories = ['plugin', 'modded', 'proxy', 'bedrock', 'vanilla', 'hybrid'] as const
const categoryKeys: Record<string, string> = {
  plugin: 'deploy_category_plugin',
  modded: 'deploy_category_modded',
  proxy: 'deploy_category_proxy',
  bedrock: 'deploy_category_bedrock',
  vanilla: 'deploy_category_vanilla',
  hybrid: 'deploy_category_hybrid',
}
const categoryLabel = (category: string) => (categoryKeys[category] ? t(categoryKeys[category]) : category)
const cores = computed<Core[]>(() => [
  {
    id: 'arclight',
    name: 'Arclight',
    desc: t('deploy_hybrid_recommended'),
    category: 'hybrid',
  },
  { id: 'catserver', name: 'CatServer', desc: t('deploy_hybrid'), category: 'hybrid' },
  {
    id: 'fabric',
    name: 'Fabric',
    desc: t('deploy_lightweight_mod_loader'),
    category: 'modded',
  },
  {
    id: 'forge',
    name: 'Forge',
    desc: t('deploy_classic_mod_platform'),
    category: 'modded',
  },
  {
    id: 'neoforge',
    name: 'NeoForge',
    desc: t('deploy_next_gen_mod_ecosystem'),
    category: 'modded',
  },
  {
    id: 'quilt',
    name: 'Quilt',
    desc: t('deploy_fabric_derived_loader'),
    category: 'modded',
  },
  {
    id: 'bungeecord',
    name: 'BungeeCord',
    desc: t('deploy_proxy_server'),
    category: 'proxy',
  },
  {
    id: 'velocity',
    name: 'Velocity',
    desc: t('deploy_modern_proxy_server'),
    category: 'proxy',
  },
  {
    id: 'folia',
    name: 'Folia',
    desc: t('deploy_multi_threaded_region_parallelism'),
    category: 'plugin',
  },
  {
    id: 'leaves',
    name: 'Leaves',
    desc: t('deploy_paper_derived_server'),
    category: 'plugin',
  },
  {
    id: 'paper',
    name: 'Paper',
    desc: t('deploy_high_performance_plugin_server_recommended'),
    category: 'plugin',
  },
  {
    id: 'purpur',
    name: 'Purpur',
    desc: t('deploy_highly_customizable_server'),
    category: 'plugin',
  },
  {
    id: 'spigot',
    name: 'Spigot',
    desc: t('deploy_classic_plugin_server'),
    category: 'plugin',
  },
  {
    id: 'spongevanilla',
    name: 'SpongeVanilla',
    desc: t('deploy_sponge_plugin_server'),
    category: 'plugin',
  },
  {
    id: 'nukkit',
    name: 'Nukkit',
    desc: t('deploy_bedrock_server'),
    category: 'bedrock',
  },
  {
    id: 'pocketmine',
    name: 'PocketMine',
    desc: t('deploy_bedrock_server'),
    category: 'bedrock',
  },
  {
    id: 'vanilla',
    name: 'Vanilla',
    desc: t('deploy_official_vanilla_server'),
    category: 'vanilla',
  },
  {
    id: 'spongeforge',
    name: 'SpongeForge',
    desc: t('deploy_forge_hybrid_ecosystem'),
    category: 'hybrid',
  },
  {
    id: 'spongeneo',
    name: 'SpongeNeo',
    desc: t('deploy_neoforge_hybrid_ecosystem'),
    category: 'hybrid',
  },
])
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
    loadError.value = getErrorMessage(error, t('deploy_failed_to_load_versions'))
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
    loadError.value = getErrorMessage(error, t('deploy_failed_to_load_builds'))
    builds.value = { ...builds.value, [version]: [] }
  }
}
const activeCategory = ref(categories[0])
const selectedCore = ref<Core | null>(null)
const selected = ref<Selection | null>(null)
const isModalOpen = ref(false)
const filteredCores = computed(() => cores.value.filter((core) => core.category === activeCategory.value))
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
          {{ categoryLabel(category) }}
        </button>
      </nav>
    </aside>
    <main class="min-w-0 flex-1">
      <header class="mb-6 flex items-end justify-between gap-4 border-b border-border pb-5">
        <div>
          <p class="mb-2 font-mono text-[10px] tracking-[0.24em] text-text-secondary">/ CORE LIBRARY</p>
          <h2 class="font-serif text-2xl text-text-primary">
            {{ t('deploy_choose_a_server_core') }}
          </h2>
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
        {{ t('deploy_selected') }}{{ selected.core }} {{ selected.version }} ({{ selected.build }})
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
