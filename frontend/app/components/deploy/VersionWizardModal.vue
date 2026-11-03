<script setup lang="ts">
import LocalScrollRuler from '~/components/ui/LocalScrollRuler.vue'
const versionViewport = ref<HTMLElement | null>(null)
const buildViewport = ref<HTMLElement | null>(null)
type Core = { id: string; name: string }
type Selection = { core: string; version: string; build: string }

const props = defineProps<{
  open: boolean
  core: Core | null
  versions: string[]
  builds: Record<string, string[]>
  loading?: boolean
  error?: string
}>()

const emit = defineEmits<{
  close: []
  select: [selection: Selection]
  versionSelect: [version: string]
}>()

const step = ref(1)
const selectedVersion = ref<string | null>(null)

const selectedBuilds = computed(() => (selectedVersion.value ? props.builds[selectedVersion.value] || [] : []))

watch(
  () => props.open,
  (open) => {
    if (open) {
      step.value = 1
      selectedVersion.value = null
    }
  },
)

function chooseVersion(version: string) {
  selectedVersion.value = version
  emit('versionSelect', version)
  step.value = 2
}

function chooseBuild(build: string) {
  if (!props.core || !selectedVersion.value) return
  emit('select', {
    core: props.core.name,
    version: selectedVersion.value,
    build,
  })
}
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-[100] flex items-center justify-center bg-background/80 p-4 backdrop-blur-sm"
      role="dialog"
      aria-modal="true"
      @click.self="emit('close')"
    >
      <section class="w-full max-w-lg border border-border bg-surface p-6 shadow-2xl">
        <header class="mb-6 flex items-start justify-between gap-4 border-b border-border pb-5">
          <div>
            <p class="mb-2 font-mono text-[10px] tracking-[0.22em] text-text-secondary">
              / DEPLOYMENT WIZARD / 0{{ step }}
            </p>
            <h2 class="font-mono text-lg font-bold text-text-primary">
              [ {{ core?.name }} ] {{ step === 1 ? '选择游戏版本' : '选择构建版本' }}
            </h2>
          </div>
          <button
            type="button"
            class="font-mono text-xl text-text-secondary hover:text-text-primary"
            aria-label="关闭"
            @click="emit('close')"
          >
            ×
          </button>
        </header>

        <div v-if="step === 1">
          <p class="mb-4 text-xs text-text-secondary">选择一个 Minecraft 游戏版本以继续。</p>
          <p v-if="loading" class="py-8 text-center text-xs text-text-secondary">正在获取最新版本数据...</p>
          <p v-else-if="error" class="py-4 text-center text-xs text-red-300">! {{ error }}</p>
          <p v-else-if="!versions.length" class="py-8 text-center text-xs text-text-secondary">暂无可用版本</p>
          <!-- 宽列表使用小刻度尺，保留紧凑选择布局。 -->
          <div class="relative">
            <div ref="versionViewport" class="grid max-h-96 grid-cols-3 gap-2 overflow-y-auto pr-6 sm:grid-cols-4">
              <button
                v-for="version in versions"
                :key="version"
                type="button"
                class="border border-border px-3 py-4 text-center font-mono text-xs text-text-secondary transition-colors hover:border-brand hover:text-text-primary"
                :class="selectedVersion === version ? 'border-brand bg-brand/10 text-text-primary' : ''"
                @click="chooseVersion(version)"
              >
                {{ version }}
              </button>
            </div>
            <LocalScrollRuler :target="versionViewport" />
          </div>
        </div>

        <div v-else>
          <button
            type="button"
            class="mb-5 font-mono text-[11px] text-text-secondary hover:text-text-primary"
            @click="step = 1"
          >
            ← 返回游戏版本
          </button>
          <p class="mb-4 text-xs text-text-secondary">{{ selectedVersion }} 的可用构建版本。</p>
          <div class="relative">
            <div ref="buildViewport" class="max-h-96 space-y-2 overflow-y-auto pr-6">
              <button
                v-for="(build, index) in selectedBuilds"
                :key="build"
                type="button"
                class="flex w-full items-center justify-between border border-border px-4 py-3 text-left font-mono text-sm text-text-primary transition-colors hover:border-brand/60 hover:bg-background"
                @click="chooseBuild(build)"
              >
                <span>{{ build }}</span>
                <span
                  v-if="index === 0"
                  class="border border-emerald-500/50 px-2 py-0.5 text-[9px] tracking-[0.16em] text-emerald-400"
                  >NEW</span
                >
              </button>
            </div>
            <LocalScrollRuler :target="buildViewport" />
          </div>
        </div>
      </section>
    </div>
  </Teleport>
</template>
