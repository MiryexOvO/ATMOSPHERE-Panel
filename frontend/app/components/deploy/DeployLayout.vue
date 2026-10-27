<script setup lang="ts">
import CoreCard from './CoreCard.vue'
import VersionWizardModal from './VersionWizardModal.vue'
const categories = [{ id: 'plugin', name: '插件服务端' }, { id: 'mod', name: '模组服务端' }, { id: 'vanilla', name: '原版服务端' }, { id: 'proxy', name: '代理服务端' }]
const cores = ref<any[]>([])
const versions = ref<string[]>([])
const activeCategory = ref('plugin')
const isModalOpen = ref(false)
const selectedCore = ref<string | null>(null)
const wizardStep = ref(1)
const selectedMcVersion = ref<string | null>(null)
const error = ref('')
const filteredCores = computed(() => cores.value.filter(core => core.category === activeCategory.value))
async function load() { const result: any = await $fetch('/api/resources/cores', { credentials: 'include' }); cores.value = result.cores || [] }
async function openCore(core: any) {
  selectedCore.value = core.id
  isModalOpen.value = true
  wizardStep.value = 1
  selectedMcVersion.value = null
  try { const result: any = await $fetch(`/api/resources/cores/${core.id}/versions`, { credentials: 'include' }); versions.value = result.versions || [] } catch { versions.value = core.versions || [] }
}
function closeModal() { isModalOpen.value = false; selectedCore.value = null; selectedMcVersion.value = null; wizardStep.value = 1 }
async function deploy(version: string, build: string) {
  error.value = ''
  try {
    const form = new FormData(); form.set('instance_id', `online-${Date.now().toString().slice(-6)}`); form.set('resource', selectedCore.value || 'paper'); form.set('version', version); form.set('build', build); form.set('java_version', '17')
    await $fetch('/api/deploy/tasks', { method: 'POST', credentials: 'include', body: form }); closeModal()
  } catch (e: any) { error.value = e?.data?.message || '部署任务创建失败' }
}
onMounted(load)
</script>
<template>
  <section class="deploy-layout-new">
    <aside class="deploy-sidebar-new"><h3>服务端分类</h3><p>选择您需要的底层架构类型</p><button v-for="category in categories" :key="category.id" :class="{active: activeCategory===category.id}" @click="activeCategory=category.id">{{ category.name }}</button></aside>
    <main class="deploy-content-new"><header><div><span>/ CORE LIBRARY</span><h2>选择服务端核心</h2></div><input placeholder="搜索核心名称..." /></header><div class="deploy-core-grid"><CoreCard v-for="core in filteredCores" :key="core.id" :name="core.name" :description="core.description" :versions="core.versions?.length" @select="openCore(core)" /></div><p v-if="error" class="wizard-error">! {{ error }}</p></main>
    <VersionWizardModal :open="isModalOpen" :core="cores.find(item => item.id === selectedCore)" :versions="versions" :error="error" @close="closeModal" @deploy="deploy" />
  </section>
</template>
