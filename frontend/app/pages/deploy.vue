<script setup lang="ts">
const formData = useState('wizard-form', () => ({ name: '', port: 25565, coreType: '', mcVersion: '', buildVersion: '', javaVersion: '17', memory: 4096, useAikar: true }))
const step = ref(1)
const modalOpen = ref(false)
const cores = ref<any[]>([])
const categories = ref<any[]>([])
const category = ref('plugin')
const versions = ref<string[]>([])
const chosenCore = ref<any>(null)
const error = ref('')
const deploying = ref(false)
const percent = ref(0)
const deployMessage = ref('')
const steps = ['基本信息','核心文件','Java / JVM','确认信息','执行部署']
const validBasic = computed(() => /^[A-Za-z0-9-]{2,48}$/.test(formData.value.name) && formData.value.port >= 1 && formData.value.port <= 65535)
const canNext = computed(() => step.value === 1 ? validBasic.value : step.value === 2 ? !!formData.value.coreType && !!formData.value.mcVersion && !!formData.value.buildVersion : step.value === 3 ? !!formData.value.javaVersion && formData.value.memory > 0 : true)
const visibleCores = computed(() => cores.value.filter(item => item.category === category.value))
async function loadCores() { const result: any = await $fetch('/api/resources/cores', { credentials: 'include' }); cores.value = result.cores || []; categories.value = result.categories || [] }
async function openCore(core: any) { chosenCore.value = core; versions.value = (await $fetch(`/api/resources/cores/${core.id}/versions`, { credentials: 'include' }) as any).versions || core.versions || []; modalOpen.value = true }
function selectBuild(version: string, build: string) { formData.value.coreType = chosenCore.value.name; formData.value.mcVersion = version; formData.value.buildVersion = build; formData.value.javaVersion = version.startsWith('1.16') ? '8' : version.startsWith('1.17') ? '16' : version <= '1.20.4' ? '17' : '21'; modalOpen.value = false }
function next() { if (canNext.value && step.value < 4) step.value++ ; else if (canNext.value && step.value === 4) { step.value = 5; deploy() } }
function back() { if (!deploying.value && step.value > 1) step.value-- }
async function deploy() { deploying.value = true; error.value = ''; try { const fd = new FormData(); fd.set('instance_id', formData.value.name.toLowerCase()); fd.set('resource', formData.value.coreType.toLowerCase()); fd.set('version', formData.value.mcVersion); fd.set('build', formData.value.buildVersion); fd.set('java_version', formData.value.javaVersion); const result: any = await $fetch('/api/deploy/tasks', { method: 'POST', credentials: 'include', body: fd }); const source = new EventSource(`/api/deploy/stream?task_id=${encodeURIComponent(result.task_id)}`); source.onmessage = event => { const data = JSON.parse(event.data); percent.value = data.percent || 0; deployMessage.value = data.stage || data.status || ''; if (data.status === 'completed' || data.status === 'failed') { deploying.value = false; source.close() } } } catch (e: any) { deploying.value = false; error.value = e?.data?.message || '部署失败' } }
onMounted(loadCores)
</script>
<template>
  <main class="new-wizard-page">
    <header class="wizard-page-header"><button class="ghost" :disabled="deploying" @click="navigateTo('/');">← 返回</button><div><span>ATMOSPHERE / INSTANCE PROVISIONING</span><h1>新建实例</h1></div></header>
    <nav class="wizard-stepper"><div v-for="(item,index) in steps" :key="item" :class="{active: step===index+1,done: step>index+1}">{{ step>index+1 ? '✓' : `0${index+1}` }} <span>{{ item }}</span></div></nav>
    <Transition name="wizard-slide" mode="out-in">
      <section v-if="step===1" key="basic" class="wizard-step-panel"><h2>基本信息</h2><p>填写实例名称和端口。</p><label>实例名称<input class="atmo-input" v-model="formData.name" placeholder="Survival-Server"></label><label>服务端口<input class="atmo-input" type="number" v-model.number="formData.port"></label><p v-if="formData.name&&!validBasic" class="wizard-error">名称只能包含英文、数字和连字符。</p></section>
      <section v-else-if="step===2" key="core" class="wizard-step-panel core-step"><h2>核心文件</h2><div class="deploy-layout-new"><aside class="deploy-sidebar-new"><h3>服务端分类</h3><p>选择核心类型</p><button v-for="item in categories" :key="item.id" :class="{active:category===item.id}" @click="category=item.id">{{item.name}}</button></aside><div class="deploy-content-new"><span>/ CORE LIBRARY</span><h3>选择服务端核心</h3><div class="deploy-core-grid"><button v-for="core in visibleCores" :key="core.id" class="core-card-new" @click="openCore(core)"><strong>{{core.name}}</strong><small>{{core.description}}</small></button></div></div></div><div v-if="formData.coreType" class="selection-summary">已选择：<strong>{{formData.coreType}}</strong> {{formData.mcVersion}} · Build {{formData.buildVersion}}</div></section>
      <section v-else-if="step===3" key="java" class="wizard-step-panel"><h2>Java 环境与 JVM 设置</h2><p>系统已自动匹配 Java {{formData.javaVersion}} 环境。</p><label>Java 版本<select class="atmo-input" v-model="formData.javaVersion"><option>8</option><option>16</option><option>17</option><option>21</option></select></label><label>内存（MB）<input class="atmo-input" type="number" min="512" v-model.number="formData.memory"></label><label class="switch-line"><input type="checkbox" v-model="formData.useAikar"> 使用 Aikar's flags</label></section>
      <section v-else-if="step===4" key="confirm" class="wizard-step-panel"><h2>确认信息</h2><div class="confirm-grid"><div><span>实例名称</span><strong>{{formData.name}}</strong></div><div><span>端口</span><strong>{{formData.port}}</strong></div><div><span>核心</span><strong>{{formData.coreType}}</strong></div><div><span>版本</span><strong>{{formData.mcVersion}} / {{formData.buildVersion}}</strong></div><div><span>Java</span><strong>{{formData.javaVersion}}</strong></div><div><span>内存</span><strong>{{formData.memory}} MB</strong></div></div></section>
      <section v-else key="deploy" class="wizard-step-panel deploy-progress-panel"><h2>{{percent===100?'创建成功！':'正在执行部署'}}</h2><p>{{deployMessage}}</p><div class="deploy-progress-bar"><i :style="{width:`${percent}%`}"></i></div><strong>{{percent}}%</strong><p v-if="error" class="wizard-error">! {{error}}</p></section>
    </Transition>
    <footer class="wizard-footer"><button class="ghost" :disabled="step===1||deploying" @click="back">上一步</button><button v-if="step<5" class="primary" :disabled="!canNext" @click="next">{{step===4?'确认并创建':'下一步'}} →</button><button v-else-if="percent===100" class="primary" @click="navigateTo('/')">返回实例列表 →</button></footer>
    <VersionWizardModal :open="modalOpen" :core="chosenCore" :versions="versions" @close="modalOpen=false" @deploy="selectBuild" />
  </main>
</template>
