<script setup lang="ts">
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
const busy = ref(false)
const error = ref('')
const result = ref<DeployResult | null>(null)
const { request } = useApi()

const modes = [
  { id: 'quick', title: '快速部署', desc: '在线选择核心、版本与构建', icon: '↗' },
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
        : ['基本信息', 'Python 环境', '核心文件', '环境与设置', '确认信息', '执行部署', '完成结果'],
)

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
  if (data.value.mode === 'quick' && step.value === 2)
    return Boolean(data.value.coreType && data.value.mcVersion && data.value.buildVersion)
  if (data.value.mode === 'package' && step.value === 3) return Boolean(data.value.coreType)
  if (data.value.mode === 'mcdr' && step.value === 3) return Boolean(data.value.coreType)
  if (step.value === steps.value.length - 2) return true
  return true
})

function selectMode(mode: Mode) {
  data.value.mode = mode
  step.value = 1
  error.value = ''
  result.value = null
}
function setCore(value: { core: string; version: string; build: string }) {
  data.value.coreType = value.core
  data.value.mcVersion = value.version
  data.value.buildVersion = value.build
  data.value.javaVersion = value.version.startsWith('1.20') ? '17' : '21'
}
function onPackage(event: Event) {
  const file = (event.target as HTMLInputElement).files?.[0]
  if (!file) return
  if (!/\.(zip|tar\.gz|tgz)$/i.test(file.name)) {
    error.value = '仅支持 .zip、.tar.gz 或 .tgz 整合包。'
    return
  }
  if (file.size > 500 * 1024 * 1024) {
    error.value = '整合包不能超过 500MB。'
    return
  }
  data.value.packageFile = file
  error.value = ''
}

async function analyzePackage() {
  if (!data.value.packageFile) return
  busy.value = true
  error.value = ''
  try {
    const form = new FormData()
    form.set('instance_id', 'scan-' + Date.now().toString(36))
    form.set('name', 'Package Scan')
    form.set('port', String(data.value.port))
    form.set('eula', 'false')
    form.set('package', data.value.packageFile)
    const response = await request<PackageInfo>('/api/instances/package/inspect', {
      method: 'POST',
      body: form,
    })
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
  error.value = ''
  try {
    if (data.value.mode === 'package' && data.value.packageFile) {
      const form = new FormData()
      form.set('instance_id', data.value.name.toLowerCase())
      form.set('name', data.value.name)
      form.set('port', String(data.value.port))
      form.set('eula', 'true')
      form.set('package', data.value.packageFile)
      result.value = await request<DeployResult>('/api/instances/package', { method: 'POST', body: form })
    } else {
      result.value = await request<DeployResult>('/api/deploy/modes', {
        method: 'POST',
        body: {
          mode: data.value.mode,
          instance_id: data.value.name.toLowerCase(),
          port: data.value.port,
          version: data.value.mcVersion,
          resource: data.value.coreType,
          java_version: data.value.javaVersion,
          memory: data.value.memory,
        },
      })
    }
    step.value = steps.value.length
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = err.data?.message || err.message || '部署失败。'
  } finally {
    busy.value = false
  }
}

function next() {
  error.value = ''
  if (!canContinue.value) {
    error.value = '请先完成当前步骤。'
    return
  }
  if (data.value.mode === 'package' && step.value === 1) {
    analyzePackage()
    return
  }
  if (step.value === steps.value.length - 2) {
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
          class="bg-surface/50 group border border-border p-7 text-left transition-all hover:-translate-y-1 hover:border-brand hover:bg-surface"
          @click="selectMode(mode.id)"
        >
          <div class="flex items-start justify-between">
            <span class="font-mono text-lg font-bold text-text-primary">{{ mode.title }}</span
            ><span class="text-xl text-brand transition-transform group-hover:translate-x-1">{{ mode.icon }}</span>
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
            class="border-brand/50 bg-surface/60 mx-auto mt-12 max-w-xl border p-10 text-center"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">/ DEPLOYMENT COMPLETE</p>
            <h2 class="mt-4 font-serif text-3xl">实例已创建</h2>
            <p class="mt-4 text-sm text-text-secondary">服务端已写入独立实例目录，可以进入控制台。</p>
            <button
              type="button"
              class="hover:bg-brand/10 mt-8 border border-brand px-5 py-3 font-mono text-xs text-brand"
              @click="navigateTo('/dashboard')"
            >
              返回实例列表 →
            </button>
          </section>
          <section
            v-else-if="data.mode === 'package' && step === 1"
            key="package-upload"
            class="bg-surface/50 mx-auto mt-12 max-w-xl border border-border p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">01 / PACKAGE UPLOAD</p>
            <h2 class="mt-4 font-serif text-3xl">上传整合包</h2>
            <p class="mt-3 text-sm text-text-secondary">支持自动解压、路径安全校验和核心检测。</p>
            <label
              class="mt-8 flex cursor-pointer flex-col items-center border border-dashed border-border p-10 text-center hover:border-brand"
              ><span class="text-3xl text-brand">↑</span
              ><strong class="mt-3 font-mono text-sm">{{ data.packageFile?.name || '选择 ZIP / TAR.GZ / TGZ' }}</strong
              ><small class="mt-2 text-xs text-text-secondary">最大 500MB</small
              ><input class="hidden" type="file" accept=".zip,.tar.gz,.tgz" @change="onPackage"
            /></label>
          </section>
          <section
            v-else-if="
              ((data.mode === 'quick' || data.mode === 'bedrock' || data.mode === 'mcdr') && step === 1) ||
              (data.mode === 'package' && step === 2)
            "
            key="basic"
            class="bg-surface/50 mx-auto mt-12 max-w-xl border border-border p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">
              {{ String(step).padStart(2, '0') }} / BASIC INFO
            </p>
            <h2 class="mt-4 font-serif text-3xl">实例基本信息</h2>
            <div class="mt-8 space-y-5">
              <label class="block text-xs text-text-secondary"
                >实例名称<input
                  v-model="data.name"
                  class="bg-background/50 mt-2 w-full border border-border px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                  placeholder="Survival-Server" /></label
              ><label class="block text-xs text-text-secondary"
                >服务端口<input
                  v-model.number="data.port"
                  class="bg-background/50 mt-2 w-full border border-border px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                  type="number"
              /></label>
            </div>
          </section>
          <section v-else-if="data.mode === 'quick' && step === 2" key="quick-core" class="mt-12">
            <Step2CoreSelector @select="setCore"></Step2CoreSelector>
          </section>
          <section
            v-else-if="data.mode === 'package' && step === 3"
            key="package-core"
            class="bg-surface/50 mx-auto mt-12 max-w-xl border border-border p-8"
          >
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">03 / CORE CONFIG</p>
            <h2 class="mt-4 font-serif text-3xl">核心检测结果</h2>
            <p class="mt-4 text-sm text-text-secondary">
              已发现 {{ data.packageInfo?.core_candidates?.length || 0 }} 个候选核心。
            </p>
            <select
              v-model="data.coreType"
              class="bg-background/50 mt-8 w-full border border-border px-4 py-3 font-mono text-sm outline-none focus:border-brand"
            >
              <option
                v-for="candidate in data.packageInfo?.core_candidates || []"
                :key="candidate.path"
                :value="candidate.path"
              >
                {{ candidate.path }} · {{ candidate.kind }}
              </option>
            </select>
          </section>
          <section v-else key="settings" class="bg-surface/50 mx-auto mt-12 max-w-xl border border-border p-8">
            <p class="font-mono text-[10px] tracking-[0.2em] text-brand">
              {{ String(step).padStart(2, '0') }} / ENVIRONMENT
            </p>
            <h2 class="mt-4 font-serif text-3xl">环境与设置</h2>
            <p class="mt-3 text-sm text-text-secondary">
              系统将检测当前主机环境；缺少 Java 或 Python 时会返回安装提示。
            </p>
            <div class="mt-8 space-y-5">
              <label class="block text-xs text-text-secondary"
                >Java 版本<select
                  v-model="data.javaVersion"
                  class="bg-background/50 mt-2 w-full border border-border px-4 py-3 font-mono text-sm"
                >
                  <option>8</option>
                  <option>17</option>
                  <option>21</option>
                </select></label
              ><label class="block text-xs text-text-secondary"
                >内存（MB）<input
                  v-model.number="data.memory"
                  class="bg-background/50 mt-2 w-full border border-border px-4 py-3 font-mono text-sm"
                  type="number"
                  min="512"
              /></label>
            </div>
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
            class="hover:bg-brand/10 border border-brand px-5 py-2 font-mono text-xs text-brand disabled:opacity-40"
            :disabled="busy || !canContinue"
            @click="next"
          >
            {{ busy ? '处理中…' : step === steps.length - 2 ? '确认并部署' : '下一步' }} →
          </button>
        </footer>
      </template>
    </div>
    <div class="mx-auto mt-10 w-full max-w-6xl">
      <button
        type="button"
        class="font-mono text-sm tracking-[0.18em] text-text-secondary hover:text-brand"
        @click="navigateTo('/dashboard')"
      >
        ← {{ t('backToControlRoom') }}
      </button>
    </div>
  </main>
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
