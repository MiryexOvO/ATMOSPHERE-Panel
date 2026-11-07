<script setup lang="ts">
import VersionWizardModal from './VersionWizardModal.vue'
const { t } = useI18n()
// 分类使用稳定的 ASCII 键，展示文案来自 i18n。
const categories = ['plugin', 'modded', 'vanilla', 'proxy']
const categoryKeys: Record<string, string> = {
  plugin: 'deploy_category_plugin',
  modded: 'deploy_category_modded',
  vanilla: 'deploy_category_vanilla',
  proxy: 'deploy_category_proxy',
}
const categoryLabel = (category: string) => (categoryKeys[category] ? t(categoryKeys[category]) : category)

type Core = {
  id: string
  name: string
  desc: string
  category: string
}

type Selection = {
  core: string
  version: string
  build: string
}

const cores = computed<Core[]>(() => [
  {
    id: 'paper',
    name: 'Paper',
    desc: t('deploy_high_performance_spigot_fork'),
    category: 'plugin',
  },
  {
    id: 'purpur',
    name: 'Purpur',
    desc: t('deploy_highly_customizable_paper_fork'),
    category: 'plugin',
  },
  {
    id: 'folia',
    name: 'Folia',
    desc: t('deploy_region_parallel_server'),
    category: 'plugin',
  },
  {
    id: 'fabric',
    name: 'Fabric',
    desc: t('deploy_lightweight_flexible_mod_loader'),
    category: 'modded',
  },
  {
    id: 'forge',
    name: 'Forge',
    desc: t('deploy_classic_minecraft_mod_platform'),
    category: 'modded',
  },
  {
    id: 'vanilla',
    name: 'Vanilla',
    desc: t('deploy_official_vanilla_minecraft_server'),
    category: 'vanilla',
  },
  {
    id: 'velocity',
    name: 'Velocity',
    desc: t('deploy_modern_high_performance_proxy'),
    category: 'proxy',
  },
])

const versions: Record<string, string[]> = {
  paper: ['1.21.1', '1.21', '1.20.6', '1.20.4', '1.20.2', '1.20.1'],
  purpur: ['1.21.1', '1.21', '1.20.6', '1.20.4'],
  folia: ['1.21', '1.20.6', '1.20.4'],
  fabric: ['1.21.1', '1.21', '1.20.6', '1.20.4'],
  forge: ['1.21.1', '1.20.6', '1.20.4', '1.20.1'],
  vanilla: ['1.21.1', '1.21', '1.20.6', '1.20.4'],
  velocity: ['3.4.0', '3.3.0', '3.2.0'],
}

const builds: Record<string, Record<string, string[]>> = {
  paper: {
    '1.21.1': ['Build ಪ್ರ', 'Build 131'],
    '1.21': ['Build 130', 'Build 129'],
    '1.20.4': ['Build 496', 'Build 495', 'Build 494'],
    '1.20.2': ['Build 318', 'Build 317'],
    '1.20.1': ['Build 196', 'Build 195'],
  },
  purpur: { '1.21.1': ['Build 2327', 'Build 2326'], '1.20.4': ['Build 2176', 'Build 2175'] },
  folia: { '1.21': ['Build 30', 'Build 29'], '1.20.4': ['Build 120', 'Build 119'] },
  fabric: { '1.21.1': ['Loader 0.16.5', 'Loader 0.16.4'], '1.20.4': ['Loader 0.15.11', 'Loader 0.15.10'] },
  forge: { '1.21.1': ['Build 52.0.30', 'Build 52.0.29'], '1.20.1': ['Build 47.3.0', 'Build 47.2.0'] },
  vanilla: { '1.21.1': ['Release', 'Server Jar'], '1.20.4': ['Release', 'Server Jar'] },
  velocity: { '3.4.0': ['Build 459', 'Build 458'], '3.3.0': ['Build ಷ್ಟ', 'Build 437'] },
}

const activeCategory = ref(categories[0])
const selectedCore = ref<Core | null>(null)
const isModalOpen = ref(false)
const selected = ref<Selection | null>(null)

const filteredCores = computed(() => cores.value.filter((core) => core.category === activeCategory.value))

function openWizard(core: Core) {
  selectedCore.value = core
  isModalOpen.value = true
}

function closeWizard() {
  isModalOpen.value = false
}

function handleSelection(selection: Selection) {
  selected.value = selection
  isModalOpen.value = false
}
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
        <span class="font-mono text-[10px] tracking-[0.18em] text-text-secondary uppercase">
          {{ filteredCores.length.toString().padStart(2, '0') }} AVAILABLE
        </span>
      </header>

      <div class="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
        <button
          v-for="core in filteredCores"
          :key="core.id"
          type="button"
          class="group cursor-pointer border border-border bg-surface/50 p-5 text-left transition-colors hover:border-brand/50"
          @click="openWizard(core)"
        >
          <div class="mb-8 flex items-start justify-between">
            <span class="font-mono text-lg font-bold text-text-primary">{{ core.name }}</span>
          </div>
          <p class="text-xs text-text-secondary">{{ core.desc }}</p>
        </button>
      </div>

      <p v-if="selected" class="mt-6 border-l-2 border-brand bg-surface px-4 py-3 font-mono text-xs text-text-primary">
        {{ t('deploy_selected') }}{{ selected.core }} {{ selected.version }} ({{ selected.build }})
      </p>
    </main>

    <VersionWizardModal
      :open="isModalOpen"
      :core="selectedCore"
      :versions="selectedCore ? versions[selectedCore.id] || [] : []"
      :builds="selectedCore ? builds[selectedCore.id] || {} : {}"
      @close="closeWizard"
      @select="handleSelection"
    />
  </section>
</template>
