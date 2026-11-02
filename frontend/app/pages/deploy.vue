<script setup lang="ts">
import WorkspaceBackground from '~/components/ui/WorkspaceBackground.vue'
import Step2CoreSelector from '~/components/deploy/Step2CoreSelector.vue'

definePageMeta({ middleware: 'auth' })

const { t } = useI18n()

type DeployResult = {
  ok: boolean
  message?: string
  instance?: { id: string }
  core_candidates?: import('~/types').PackageCandidate[]
}
type WizardData = import('~/types').DeployWizardData
type PackageInfo = import('~/types').PackageInfo
type Mode = WizardData['mode']

const data = useState<WizardData>('wizard-data', () => ({
  mode: '',
  name: '',
  port: 25565,
  coreType: '',
  mcVersion: '',
  buildVersion: '',
  javaVersion: '21',
  memory: 4096,
  useAikar: true,
  packageFile: null,
  packageInfo: null,
}))

const step = ref(0)
const bedrockVersions=ref<{id:string;label:string}[]>([])
const modeLoading=ref(false),acceptEula=ref(false)
const ipv6Port=ref(19133)
const busy = ref(false)
const dragging = ref(false)
const packageLimitMb=ref(500)
const packageInput = ref<HTMLInputElement | null>(null)
const error = ref('')
const result = ref<DeployResult | null>(null)
const isDeploying = ref(false)
const progress = ref<number | null>(0)
const deployStatus = ref('准备部署...')
const deployInstanceId = ref('')
const deploySource = useState('wizard-source', () => 'fastmirror')
let deployStream: EventSource | null = null
// 新向导使用面板默认环境；不改动已进行的步骤。
onMounted(async()=>{try{const result=await useApi().request<{settings:{upload_limit_mb:number}}>('/api/panel/settings');packageLimitMb.value=result.settings.upload_limit_mb}catch{}})
onUnmounted(()=>deployStream?.close())
const { request,getErrorMessage } = useApi()

function openInstanceConsole() {
  isDeploying.value = false
  navigateTo('/instances/' + deployInstanceId.value)
}

const modes = [
  { id: 'quick', title: '快速部署', desc: '在线选择核心、版本与构建', icon: '' },
  { id: 'bedrock', title: '基岩版', desc: '部署 Bedrock Dedicated Server', icon: '◇' },
  { id: 'package', title: '上传整合包', desc: '上传、解压并自动检测服务端核心', icon: '↑' },
  { id: 'mcdr', title: 'MCDR', desc: '使用 Python 管理 Minecraft 服务端', icon: '⌘' },
] as const

const steps = computed(() =>
  data.value.mode === 'quick'
    ? ['基本信息', '核心文件', '环境与设置', '确认信息', '执行部署', '完成结果']
    : data.value.mode === 'bedrock'
      ? ['基本信息', '服务端版本', '环境与设置', '确认信息', '执行部署', '完成结果']
      : data.value.mode === 'package'
        ? ['上传整合包', '基本信息', '核心配置', '环境与设置', '确认信息', '执行部署', '完成结果']
        : ['基本信息', '核心文件', '环境与设置', '确认信息', '执行部署', '完成结果'],
)

// 整合包多一步上传，环境与确认步骤随模式偏移。
const environmentStep = computed(() => data.value.mode === 'package' ? 4 : 3)
const confirmStep = computed(() => data.value.mode === 'package' ? 5 : 4)
const isComplete = computed(() => step.value === steps.value.length)
const validBasic = computed(
  () => /^[A-Za-z0-9-]{2,48}$/.test(data.value.name) && data.value.port > 0 && data.value.port <= 65535,
)

const canContinue = computed(() => {
  if (data.value.mode === 'package' && step.value === 1) return Boolean(data.value.packageFile)
  if (
    (data.value.mode === 'quick' && step.value === 1) ||
    (data.value.mode === 'bedrock' && step.value === 1) ||
    (data.value.mode === 'mcdr' && step.value === 1)
  )
    return validBasic.value
  if ((data.value.mode === 'quick'||data.value.mode==='mcdr') && step.value === 2)
    return Boolean(data.value.coreType && data.value.mcVersion && data.value.buildVersion)
  if (data.value.mode === 'package' && step.value === 2) return validBasic.value
  if(data.value.mode==='bedrock'&&step.value===2)return Boolean(data.value.mcVersion)&&!modeLoading.value
  if (step.value === environmentStep.value) return data.value.memory >= 512 && data.value.memory <= 131072&&(data.value.mode!=='bedrock'||(acceptEula.value&&ipv6Port.value!==data.value.port))
  if (data.value.mode === 'package' && step.value === 3) return Boolean(data.value.coreType)
  if (step.value === confirmStep.value) return true
  return true
})

function selectMode(mode: Mode) {
  data.value.mode = mode
  data.value.port=mode==='bedrock'?19132:25565
  acceptEula.value=false
  if(mode==='bedrock')loadBedrockVersions()
  data.value.coreType = ''
  data.value.mcVersion = ''
  data.value.buildVersion = ''
  data.value.packageInfo = null
  data.value.packageFile = null
  step.value = 1
  error.value = ''
  result.value = null
}
// 版本直接来自官方适用于本机的正式发布目录。
async function loadBedrockVersions(){modeLoading.value=true;try{const result=await request<{supported:boolean;message?:string;versions:typeof bedrockVersions.value}>('/api/deploy/bedrock/versions');if(!result.supported)throw Error(result.message);bedrockVersions.value=result.versions;data.value.coreType='bedrock';data.value.mcVersion=result.versions[0]?.id||'';data.value.buildVersion=data.value.mcVersion}catch(cause){error.value=getErrorMessage(cause)}finally{modeLoading.value=false}}
function setCore(value: { core: string; version: string; build: string; source?: string }) {
  deploySource.value = value.source || 'fastmirror'
  data.value.coreType = value.core
  data.value.mcVersion = value.version
  data.value.buildVersion = value.build
  // 低于核心最低要求时才提升默认 Java。
  const match=value.version.match(/^(\d+)(?:\.(\d+))?(?:\.(\d+))?/)
  const minimum=Number(match?.[1])>=26?25:Number(match?.[2])>=21||(Number(match?.[2])===20&&Number(match?.[3])>=5)?21:17
  if(Number(data.value.javaVersion)<minimum)data.value.javaVersion=String(minimum)
}
// 点击和拖放共用校验，换包时清除旧的核心信息。
function choosePackage(file?: File) {
  if (!file) return
  if (!/\.(zip|tar\.gz|tgz)$/i.test(file.name)) { error.value = '仅支持 .zip、.tar.gz 或 .tgz 整合包。'; return }
  if (file.size > packageLimitMb.value * 1024 * 1024) { error.value = `整合包不能超过 ${packageLimitMb.value}MB。`; return }
  data.value.packageFile = file
  data.value.packageInfo = null
  data.value.coreType = ''
  data.value.mcVersion = ''
  data.value.buildVersion = ''
  error.value = ''
}
function onPackage(event: Event) {
  choosePackage((event.target as HTMLInputElement).files?.[0])
}
function onDrop(event: DragEvent) {
  dragging.value = false
  if (busy.value) return
  if (event.dataTransfer?.files.length !== 1) { error.value = '每次请选择一个整合包。'; return }
  choosePackage(event.dataTransfer.files[0])
}

async function analyzePackage() {
  if (!data.value.packageFile) return
  busy.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.set('package', data.value.packageFile)
    const response = await request<PackageInfo>('/api/instances/package/inspect', {
      method: 'POST',
      body: form,
    })
    if (!response.core_candidates?.some(item => item.kind === 'jar' || item.kind === 'args')) throw new Error('整合包中未找到可启动核心。')
    data.value.packageInfo = response
    const candidate = response.core_candidates?.find((item) => item.recommended) || response.core_candidates?.[0]
    if (candidate) data.value.coreType = candidate.path
    step.value++
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = err.data?.message || err.message || '整合包分析失败。'
  } finally {
    busy.value = false
  }
}

async function deploy() {
  busy.value = true
  isDeploying.value = true
  progress.value = 0
  deployStatus.value = '准备部署...'
  deployInstanceId.value = data.value.name.toLowerCase()
  error.value = ''
  try {
    if (data.value.mode === 'package' && data.value.packageFile) {
      const form = new FormData()
      form.set('instance_id', data.value.name.toLowerCase())
      form.set('name', data.value.name)
      form.set('port', String(data.value.port))
      form.set('selected_core', data.value.coreType)
      form.set('memory', String(data.value.memory))
      form.set('java_version', data.value.javaVersion)
      form.set('package', data.value.packageFile)
      deployStatus.value = '正在上传并校验整合包，完成后创建实例...'
      progress.value = null
      result.value = await request<DeployResult>('/api/instances/package', { method: 'POST', body: form })
      progress.value = 100
      deployStatus.value = '整合包已导入，实例已创建，可手动启动'
      step.value = steps.value.length
      return
    } else {
      result.value = await request<DeployResult>('/api/instances/deploy', {
        method: 'POST',
        body: {
          mode:data.value.mode==='mcdr'?'mcdr':data.value.mode==='bedrock'?'bedrock':'java',
          accept_eula:acceptEula.value,ipv6_port:ipv6Port.value,
          instance_id: data.value.name.toLowerCase(),
          core_type: data.value.coreType,
          mc_version: data.value.mcVersion,
          build_version: data.value.buildVersion,
          source: deploySource.value,
          port: data.value.port,
          java_version: data.value.javaVersion,
          memory: data.value.memory,
        },
      })
    }
    busy.value = false
    deployStream?.close()
    deployStream = new EventSource('/api/instances/deploy/stream/' + encodeURIComponent(deployInstanceId.value))
    deployStream.onmessage = (event) => {
      const payload = JSON.parse(event.data) as { progress: number; status: string }
      progress.value = payload.progress ?? null
      deployStatus.value = payload.status
      if (payload.status.startsWith('部署失败')) {
        error.value = payload.status
        deployStream?.close()
        return
      }
      if (progress.value !== null && progress.value >= 100) {
        deployStream?.close()
        deployStatus.value = '部署完成！'
        step.value = steps.value.length
      }
    }
    deployStream.onerror = () => {
      deployStream?.close()
      error.value = '部署进度连接中断，请检查后端及实例状态后再重试。'
      deployStatus.value = error.value
    }
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = err.data?.message || err.message || '部署失败。'
    deployStatus.value = error.value
  } finally {
    busy.value = false
  }
}

function next() {
  if (busy.value || isDeploying.value) return
  error.value = ''
  if (!canContinue.value) {
    error.value = '请先完成当前步骤。'
    return
  }
  if (data.value.mode === 'package' && step.value === 1) {
    analyzePackage()
    return
  }
  if (step.value === confirmStep.value) {
    deploy()
    return
  }
  if (step.value < steps.value.length) step.value++
}
function back() {
  if (step.value > 1) step.value--
  else {
    step.value = 0
    data.value.mode = ''
  }
}
</script>

<template>
  <div class="min-h-screen">
  <WorkspaceBackground/>
  <main class="relative z-10 min-h-screen px-6 py-10 text-text-primary md:px-10">
    <div class="mx-auto w-full max-w-6xl">
      <header class="flex items-end justify-between border-b border-border pb-7">
        <div>
          <p class="font-mono text-[10px] tracking-[0.22em] text-text-secondary">
            / ATMOSPHERE / INSTANCE PROVISIONING
          </p>
          <h1 class="mt-3 font-serif text-4xl md:text-5xl">{{ step === 0 ? '选择开服模式' : '新建实例' }}</h1>
        </div>
        <span v-if="step" class="font-mono text-[10px] tracking-[0.2em] text-text-secondary"
          >STEP {{ String(step).padStart(2, '0') }} / {{ String(steps.length).padStart(2, '0') }}</span
        >
      </header>
      <section v-if="step === 0" class="mt-12 grid gap-4 sm:grid-cols-2">
        <button
          v-for="mode in modes"
          :key="mode.id"
          type="button"
          class="group border border-border bg-surface/50 p-7 text-left transition-all hover:-translate-y-1 hover:border-brand hover:bg-surface"
          @click="selectMode(mode.id)"
        >
          <div class="flex items-start justify-between">
            <span class="font-mono text-lg font-bold text-text-primary">{{ mode.title }}</span
            ><span v-if="mode.icon" class="text-xl text-brand transition-transform group-hover:translate-x-1">{{ mode.icon }}</span>
          </div>
          <p class="mt-8 text-sm text-text-secondary">{{ mode.desc }}</p>
          <span class="mt-5 block font-mono text-[10px] tracking-[0.16em] text-brand">选择模式 →</span>
        </button>
      </section>
      <template v-else>
        <nav class="mt-8 grid border-y border-border py-5" :class="steps.length > 6 ? 'grid-cols-7' : 'grid-cols-6'">
          <div
            v-for="(label, index) in steps"
            :key="label"
            class="flex items-center gap-2 font-mono text-[10px]"
            :class="index + 1 <= step ? 'text-brand' : 'text-text-secondary'"
          >
            <span
              class="flex h-6 w-6 shrink-0 items-center justify-center border"
              :class="
                index + 1 < step
                  ? 'border-brand bg-brand text-background'
                  : index + 1 === step
                    ? 'border-brand'
                    : 'border-border'
              "
              >{{ index + 1 < step ? '✓' : String(index + 1).padStart(2, '0') }}</span
            ><span class="hidden lg:inline">{{ label }}</span>
          </div>
        </nav>
        <Transition name="wizard-slide" mode="out-in">
          <section
            v-if="isComplete"
            key="complete"
            class="mx-auto mt-12 max-w-xl border border-brand/50 bg-surface/60 p-10 text-center"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ DEPLOYMENT COMPLETE</p>
            <h2 class="mt-4 font-serif text-3xl">实例已创建</h2>
            <p class="mt-4 text-sm text-text-secondary">服务端已写入独立实例目录，可以进入控制台。</p>
            <button
              type="button"
              class="mt-8 border border-brand px-5 py-3 font-mono text-xs text-brand hover:bg-brand/10"
              @click="navigateTo('/dashboard')"
            >
              返回实例列表 →
            </button>
          </section>
          <section
            v-else-if="data.mode === 'package' && step === 1"
            key="package-upload"
            class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">01 / PACKAGE UPLOAD</p>
            <h2 class="mt-4 font-serif text-3xl">上传整合包</h2>
            <p class="mt-3 text-sm text-text-secondary">支持自动解压、路径安全校验和核心检测。</p>
            <label
              data-package-dropzone tabindex="0" role="button"
              :class="dragging ? 'border-brand bg-brand/10' : ''"
              @dragover.prevent="dragging = true"
              @dragleave.prevent="dragging = false"
              @drop.prevent="onDrop"
              @keydown.enter.prevent="packageInput?.click()"
              @keydown.space.prevent="packageInput?.click()"
              class="mt-8 flex cursor-pointer flex-col items-center border border-dashed border-border p-10 text-center hover:border-brand"
              ><span class="text-3xl text-brand">↑</span
              ><strong class="mt-3 font-mono text-sm">{{ data.packageFile?.name || '拖放文件到此处，或点击选择 ZIP / TAR.GZ / TGZ' }}</strong
              ><small class="mt-2 text-xs text-text-secondary">最大 {{packageLimitMb}}MB</small
              ><input ref="packageInput" class="hidden" type="file" accept=".zip,.tar.gz,.tgz" @change="onPackage"
            /></label>
          </section>
          <section
            v-else-if="
              ((data.mode === 'quick' || data.mode === 'bedrock' || data.mode === 'mcdr') && step === 1) ||
              (data.mode === 'package' && step === 2)
            "
            key="basic"
            class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">
              {{ String(step).padStart(2, '0') }} / BASIC INFO
            </p>
            <h2 class="mt-4 font-serif text-3xl">实例基本信息</h2>
            <p v-if="data.mode==='mcdr'" class="mt-4 text-sm leading-7 text-text-secondary">将创建实例专用 Python 环境安装 MCDReforged，插件独立存放在 mcdr_plugins；不会改动面板 Python 依赖。</p><p v-if="data.mode==='bedrock'" class="mt-4 text-sm leading-7 text-text-secondary">原生 BDS 不需要 Java；内存值仅作为监测预算，不会伪装成 JVM 内存限制。</p><div v-if="data.mode==='bedrock'" class="mt-5 space-y-4"><label class="block text-sm">IPv6 UDP 端口<input v-model.number="ipv6Port" type="number" min="1" max="65535" class="mt-2 w-full border border-border bg-transparent p-3"/></label></div><div class="mt-8 space-y-5">
              <label class="block text-xs text-text-secondary"
                >实例名称<input
                  v-model="data.name"
                  class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                  placeholder="Survival-Server" /></label
              ><label class="block text-xs text-text-secondary"
                >服务端口<input
                  v-model.number="data.port"
                  class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                  type="number"
              /></label>
            </div>
          </section>
          <section v-else-if="(data.mode === 'quick'||data.mode==='mcdr') && step === 2" key="quick-core" class="mt-12">
            <Step2CoreSelector @select="setCore"></Step2CoreSelector>
          </section>
          <AtmosphereCard v-else-if="data.mode==='bedrock'&&step===2" key="bedrock-version" :interactive="false" class="mx-auto mt-12 max-w-xl"><h2 class="font-serif text-2xl">基岩版官方服务端</h2><p class="my-5 text-sm leading-7 text-text-secondary">从 Mojang 官方目录获取本机适用的正式版。需要 Windows x64 或 Ubuntu 22.04+ x64；客户端使用 UDP 端口连接。</p><p v-if="modeLoading" class="text-xs text-brand">正在读取官方版本…</p><AtmosphereSelect v-else v-model="data.mcVersion" label="BDS VERSION" :options="bedrockVersions.map(item=>({value:item.id,label:item.label}))"/><button type="button" class="mt-4 text-xs text-brand" @click="loadBedrockVersions">刷新官方目录</button></AtmosphereCard>
          <section
            v-else-if="data.mode === 'package' && step === 3"
            key="package-core"
            class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">03 / CORE CONFIG</p>
            <h2 class="mt-4 font-serif text-3xl">核心检测结果</h2>
            <p class="mt-4 text-sm text-text-secondary">
              已发现 {{ data.packageInfo?.core_candidates?.length || 0 }} 个候选核心。
            </p>
            <select
              v-model="data.coreType"
              class="mt-8 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
            >
              <option
                v-for="candidate in data.packageInfo?.core_candidates?.filter(item => item.kind === 'jar' || item.kind === 'args') || []"
                :key="candidate.path"
                :value="candidate.path"
              >
                {{ candidate.path }} · {{ candidate.kind }}
              </option>
            </select>
          </section>
          <section
            v-else-if="step === environmentStep"
            key="settings"
            class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">
              {{ String(step).padStart(2, '0') }} / ENVIRONMENT
            </p>
            <h2 class="mt-4 font-serif text-3xl">环境与设置</h2>
            <p class="mt-3 text-sm text-text-secondary">
              {{data.mode==='bedrock'?'运行官方原生 BDS，不需要 Java；内存仅作为监测预算。':data.mode==='mcdr'?'使用实例专用 Python 环境运行 MCDR，并由它启动所选 Java 核心。':'系统将检测当前主机环境；缺少 Java 时会返回安装提示。'}}
            </p>
            <label v-if="data.mode==='bedrock'" class="flex items-center gap-3 text-sm"><input v-model="acceptEula" type="checkbox" class="accent-brand"/>同意 <a href="https://aka.ms/MinecraftEULA" target="_blank" rel="noopener noreferrer" class="text-brand underline">Minecraft EULA</a></label><div class="mt-8 space-y-5">
              <label v-if="data.mode!=='bedrock'" class="block text-xs text-text-secondary"
                >Java 版本<select
                  v-model="data.javaVersion"
                  class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm"
                >
                  <option>8</option>
                  <option>17</option>
                  <option>21</option>
                </select></label
              ><label class="block text-xs text-text-secondary"
                >内存（MB）<input
                  v-model.number="data.memory"
                  class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm"
                  type="number"
                  min="512"
              /></label>
            </div>
          </section>
          <section
            v-else-if="step === confirmStep"
            key="confirm"
            class="mx-auto mt-12 max-w-2xl border border-border p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ CONFIRMATION</p>
            <h2 class="mt-4 font-serif text-3xl">确认部署信息</h2>
            <p v-if="data.mode === 'package'" class="mt-5 break-all text-sm text-text-secondary">整合包：{{ data.packageFile?.name }}</p>
            <dl class="mt-8 divide-y divide-border font-mono text-sm">
              <div class="flex justify-between py-4">
                <dt class="text-text-secondary">实例名称</dt>
                <dd>{{ data.name }}</dd>
              </div>
              <div class="flex justify-between py-4">
                <dt class="text-text-secondary">服务端口</dt>
                <dd>{{ data.port }}</dd>
              </div>
              <div class="flex justify-between py-4">
                <dt class="text-text-secondary">核心</dt>
                <dd>{{ data.coreType || data.mode }}</dd>
              </div>
              <div v-if="data.mode !== 'package'" class="flex justify-between py-4">
                <dt class="text-text-secondary">游戏版本</dt>
                <dd>{{ data.mcVersion || '—' }}</dd>
              </div>
              <div v-if="data.mode !== 'package'" class="flex justify-between py-4">
                <dt class="text-text-secondary">核心构建</dt>
                <dd>{{ data.buildVersion || '—' }}</dd>
              </div>
              <div v-if="data.mode!=='bedrock'" class="flex justify-between py-4">
                <dt class="text-text-secondary">Java</dt>
                <dd>{{ data.javaVersion }}</dd>
              </div>
              <div class="flex justify-between py-4">
                <dt class="text-text-secondary">内存</dt>
                <dd>{{ data.memory }} MB</dd>
              </div>
            </dl>
          </section>
        </Transition>
        <p
          v-if="error"
          class="mx-auto mt-5 max-w-xl border border-red-400/40 bg-red-400/10 px-4 py-3 font-mono text-xs text-red-300"
        >
          ! {{ error }}
        </p>
        <footer class="mx-auto mt-8 flex max-w-2xl justify-between border-t border-border pt-6">
          <button
            type="button"
            class="border border-border px-4 py-2 font-mono text-xs text-text-secondary hover:border-brand hover:text-brand"
            @click="back"
          >
            ← 上一步</button
          ><button
            v-if="!isComplete"
            type="button"
            class="border border-brand px-5 py-2 font-mono text-xs text-brand hover:bg-brand/10 disabled:opacity-40"
            :disabled="busy || !canContinue"
            @click="next"
          >
            {{ busy ? '处理中…' : step === confirmStep ? '确认并部署' : '下一步' }} →
          </button>
        </footer>
      </template>
      <div
        v-if="isDeploying"
        class="fixed inset-0 z-50 flex items-center justify-center bg-black/70 p-4"
        role="dialog"
        aria-modal="true"
      >
        <AtmosphereCard>
          <div class="w-full max-w-2xl space-y-6 p-4 md:p-8">
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ DEPLOYMENT PROGRESS</p>
            <h2 class="font-serif text-2xl text-text-primary">{{ data.name }}</h2>
            <p class="font-mono text-xs text-text-secondary" :class="error ? 'text-red-400' : ''">{{ deployStatus }}</p>
            <button
              v-if="error"
              type="button"
              class="border border-red-400/40 px-4 py-2 font-mono text-xs text-red-400 hover:bg-red-400/10"
              @click="isDeploying = false"
            >
              [ CLOSE ]
            </button>
            <div class="h-1 w-full overflow-hidden bg-background">
              <div
                class="h-full bg-brand transition-all duration-300"
                :class="progress === null ? 'w-1/3 animate-pulse' : ''"
                :style="progress === null ? {} : { width: progress + '%' }"
              />
            </div>
            <div class="flex items-center justify-between font-mono text-[10px] text-text-secondary">
              <span>REAL DOWNLOAD</span><span>{{ progress === null ? 'DOWNLOADING' : progress + '%' }}</span>
            </div>
            <button
              v-if="progress !== null && progress >= 100"
              type="button"
              class="border border-brand px-4 py-2 font-mono text-xs text-brand hover:bg-brand/10"
              @click="openInstanceConsole"
            >
              进入控制台 →
            </button>
          </div>
        </AtmosphereCard>
      </div>
    </div>
    <div class="mx-auto mt-10 w-full max-w-6xl">
      <a href="/dashboard"
        class="font-mono text-sm tracking-[0.18em] text-text-secondary hover:text-brand"
      >
        ← {{ t('backToControlRoom') }}
      </a>
    </div>
  </main>
  </div>
</template>
<style scoped>
.wizard-slide-enter-active,
.wizard-slide-leave-active {
  transition:
    opacity 240ms ease,
    transform 240ms ease;
}
.wizard-slide-enter-from {
  opacity: 0;
  transform: translateX(18px);
}
.wizard-slide-leave-to {
  opacity: 0;
  transform: translateX(-18px);
}
</style>
