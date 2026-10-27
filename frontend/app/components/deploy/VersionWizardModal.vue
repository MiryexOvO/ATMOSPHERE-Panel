<script setup lang="ts">
import { ref, watch } from 'vue'
const props = defineProps<{ open: boolean; core: any; versions: string[]; loading?: boolean; error?: string }>()
const emit = defineEmits<{ close: []; deploy: [version: string, build: string] }>()
const wizardStep = ref(1)
const selectedMcVersion = ref<string | null>(null)
const builds = ref<string[]>([])
const loadingBuilds = ref(false)
watch(() => props.open, (open) => { if (open) { wizardStep.value = 1; selectedMcVersion.value = null; builds.value = [] } })
async function chooseVersion(version: string) {
  selectedMcVersion.value = version
  wizardStep.value = 2
  loadingBuilds.value = true
  try {
    const result: any = await $fetch(`/api/resources/cores/${props.core.id}/versions/${encodeURIComponent(version)}/builds`, { credentials: 'include' })
    builds.value = result.builds || []
  } catch { builds.value = [] }
  finally { loadingBuilds.value = false }
}
</script>
<template>
  <Teleport to="body">
    <div v-if="open" class="wizard-backdrop" @click.self="emit('close')">
      <section class="wizard-modal">
        <header class="wizard-header"><div><span>/ CORE LIBRARY / {{ core?.name }}</span><h2>{{ core?.name }} 选择构建版本</h2></div><button class="wizard-close" @click="emit('close')">×</button></header>
        <div class="wizard-progress"><b :class="{active:wizardStep===1,done:wizardStep>1}">01 <span>游戏版本</span></b><i></i><b :class="{active:wizardStep===2}">02 <span>构建版本</span></b></div>
        <div v-if="wizardStep===1" class="wizard-pane"><h3>选择 Minecraft 游戏版本</h3><p>选择版本后，将只加载该核心对应的构建分支。</p><div class="wizard-version-grid"><button v-for="version in versions" :key="version" @click="chooseVersion(version)">{{ version }}</button></div></div>
        <div v-else class="wizard-pane"><button class="wizard-back" @click="wizardStep=1">← 返回游戏版本</button><h3>选择 {{ selectedMcVersion }} 的构建版本</h3><p v-if="loadingBuilds">正在读取官方构建列表...</p><p v-else-if="!builds.length" class="wizard-error">! 当前版本暂未获取到构建列表</p><div class="wizard-build-grid"><button v-for="build in builds" :key="build" @click="emit('deploy', selectedMcVersion!, build)"><span>{{ build }}</span><em v-if="build===builds[0]">推荐 / 最新</em></button></div></div>
      </section>
    </div>
  </Teleport>
</template>
