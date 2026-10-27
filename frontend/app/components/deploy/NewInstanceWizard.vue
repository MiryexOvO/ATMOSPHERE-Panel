<script setup lang="ts">
import DeployLayout from './DeployLayout.vue'
import VersionWizardModal from './VersionWizardModal.vue'

const emit = defineEmits<{ close: []; complete: [] }>()
const step = ref(1)
const formData = reactive({ name: '', port: 25565, coreType: '', mcVersion: '', buildVersion: '', javaVersion: '', memory: '4G', useAikar: true })
const coreModal = ref(false)
const selectedCore = ref<any>(null)
const deployStatus = ref('idle')
const deployPercent = ref(0)
const deployMessage = ref('')
const deploySteps = ref([
  { label: '创建实例目录', state: 'pending' }, { label: '下载 Java 环境', state: 'pending' }, { label: '下载核心文件', state: 'pending' }, { label: '生成配置文件', state: 'pending' }, { label: '启动服务器', state: 'pending' }
])
const validBasic = computed(() => /^[A-Za-z0-9-]{2,48}$/.test(formData.name) && formData.port > 0 && formData.port < 65536)
const canNext = computed(() => step.value === 1 ? validBasic.value : step.value === 2 ? !!formData.coreType && !!formData.mcVersion && !!formData.buildVersion : step.value === 3 ? !!formData.javaVersion && !!formData.memory : true)
function chooseCore(core: any, version: string, build: string) { selectedCore.value = core; formData.coreType = core.name; formData.mcVersion = version; formData.buildVersion = build; coreModal.value = false }
function recommendJava(version: string) { formData.javaVersion = version.startsWith('1.16') ? '8' : version.startsWith('1.17') ? '16' : (version.startsWith('1.18') || version.startsWith('1.19') || version === '1.20.4') ? '17' : '21' }
watch(() => formData.mcVersion, value => { if (value) recommendJava(value) })
function next() { if (!canNext.value) return; if (step.value < 4) step.value++; else if (step.value === 4) { step.value = 5; startDeploy() } }
function back() { if (step.value > 1 && step.value < 5) step.value-- }
async function startDeploy() {
  deployStatus.value = 'running'; deployMessage.value = '准备部署'
  try {
    const fd = new FormData(); fd.set('instance_id', formData.name.toLowerCase()); fd.set('resource', formData.coreType.toLowerCase()); fd.set('version', formData.mcVersion); fd.set('build', formData.buildVersion); fd.set('java_version', formData.javaVersion)
    const result: any = await $fetch('/api/deploy/tasks', { method: 'POST', credentials: 'include', body: fd })
    const source = new EventSource(`/api/deploy/stream?task_id=${encodeURIComponent(result.task_id)}`)
    source.onmessage = event => { const data = JSON.parse(event.data); deployPercent.value = data.percent || 0; deployMessage.value = data.stage || data.status; if (data.status === 'completed') { deploySteps.value.forEach(item => item.state = 'done'); deployStatus.value = 'done'; source.close() } if (data.status === 'failed') { deployStatus.value = 'failed'; source.close() } }
  } catch (error: any) { deployStatus.value = 'failed'; deployMessage.value = error?.data?.message || '部署失败' }
}
</script>
<template>
  <div class="new-wizard-page">
    <header class="wizard-page-header"><button class="ghost" :disabled="step===5" @click="emit('close')">← 返回</button><div><span>ATMOSPHERE / INSTANCE PROVISIONING</span><h1>新建实例</h1></div></header>
    <nav class="wizard-stepper"><div v-for="item in ['基本信息','核心文件','Java / JVM','确认信息','执行部署']" :key="item" :class="{active:step===['基本信息','核心文件','Java / JVM','确认信息','执行部署'].indexOf(item)+1,done:['基本信息','核心文件','Java / JVM','确认信息','执行部署'].indexOf(item)+1<step}">{{ item }}</div></nav>
    <Transition name="wizard-slide" mode="out-in">
      <section v-if="step===1" key="basic" class="wizard-step-panel"><h2>基本信息</h2><p>创建实例名称与网络端口。</p><label>实例名称<input class="atmo-input" v-model="formData.name" placeholder="Survival-Server"></label><label>服务端端口<input class="atmo-input" type="number" v-model.number="formData.port"></label><p v-if="formData.name&&!validBasic" class="wizard-error">名称只能包含英文、数字和连字符。</p></section>
      <section v-else-if="step===2" key="core" class="wizard-step-panel"><h2>核心文件</h2><p>选择核心后不会立即下载，确认后继续下一步。</p><button class="core-selected" @click="coreModal=true">{{formData.coreType?`${formData.coreType} ${formData.mcVersion} · Build ${formData.buildVersion}`:'选择服务端核心'}}</button><div v-if="formData.coreType" class="selection-summary">已选择：<strong>{{formData.coreType}}</strong> / {{formData.mcVersion}} / Build {{formData.buildVersion}}</div></section>
      <section v-else-if="step===3" key="java" class="wizard-step-panel"><h2>Java 环境与 JVM 设置</h2><p>系统已自动匹配 Java {{formData.javaVersion || '17'}} 环境。</p><label>Java 版本<select class="atmo-input" v-model="formData.javaVersion"><option>8</option><option>17</option><option>21</option></select></label><label>内存分配<input class="atmo-input" v-model="formData.memory"></label><label class="switch-line"><input type="checkbox" v-model="formData.useAikar"> 使用 Aikar's flags</label></section>
      <section v-else-if="step===4" key="confirm" class="wizard-step-panel"><h2>确认信息</h2><div class="confirm-grid"><div><span>实例名称</span><strong>{{formData.name}}</strong></div><div><span>端口</span><strong>{{formData.port}}</strong></div><div><span>核心</span><strong>{{formData.coreType}}</strong></div><div><span>版本</span><strong>{{formData.mcVersion}} / {{formData.buildVersion}}</strong></div><div><span>Java</span><strong>{{formData.javaVersion}}</strong></div><div><span>内存</span><strong>{{formData.memory}}</strong></div></div></section>
      <section v-else key="deploy" class="wizard-step-panel deploy-progress-panel"><h2>{{deployStatus==='done'?'创建成功！':'正在执行部署'}}</h2><p>{{deployMessage}}</p><div class="deploy-progress-bar"><i :style="{width:`${deployPercent}%`}"></i></div><strong>{{deployPercent}}%</strong><div class="deploy-timeline"><div v-for="item in deploySteps" :key="item.label" :class="item.state">{{item.state==='done'?'✓':'○'}} {{item.label}}</div></div><button v-if="deployStatus==='done'" class="primary" @click="emit('complete')">进入实例列表 →</button></section>
    </Transition>
    <footer class="wizard-footer"><button class="ghost" :disabled="step===1||step===5" @click="back">上一步</button><button v-if="step<5" class="primary" :disabled="!canNext" @click="next">{{step===4?'确认并创建':'下一步'}} →</button></footer>
    <VersionWizardModal v-if="coreModal" :open="coreModal" :core="selectedCore || {id:'paper',name:'服务端核心'}" :versions="['1.21.4','1.21.1','1.20.4','1.19.4','1.18','1.16.5']" @close="coreModal=false" @deploy="chooseCore(selectedCore || {name:'Paper'}, $event[0], $event[1])" />
  </div>
</template>
