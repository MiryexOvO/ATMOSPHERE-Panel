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
const bedrockVersions = ref<{ id: string; label: string }[]>([])
const modeLoading = ref(false),
  acceptEula = ref(false)
const ipv6Port = ref(19133)
const busy = ref(false)
const dragging = ref(false)
const packageLimitMb = ref(500)
const packageInput = ref<HTMLInputElement | null>(null)
const error = ref('')
const result = ref<DeployResult | null>(null)
const isDeploying = ref(false)
const progress = ref<number | null>(0)
const deployStatus = ref('')
const deployInstanceId = ref('')
const deploySource = useState('wizard-source', () => 'fastmirror')
let deployStream: EventSource | null = null
// 新向导使用面板默认环境；不改动已进行的步骤。
onMounted(async () => {
  try {
    const result = await useApi().request<{ settings: { upload_limit_mb: number } }>('/api/panel/settings')
    packageLimitMb.value = result.settings.upload_limit_mb
  } catch {}
})
onUnmounted(() => deployStream?.close())
const { request, getErrorMessage } = useApi()

function openInstanceConsole() {
  isDeploying.value = false
  navigateTo('/instances/' + deployInstanceId.value)
}

// computed 保证切换语言后标题与描述会重新计算。
const modes = computed<{ id: Mode; title: string; desc: string; icon: string }[]>(() => [
  {
    id: 'quick',
    title: t('deploy_quick_deploy'),
    desc: t('deploy_pick_a_core_version_and_build_online'),
    icon: '',
  },
  {
    id: 'bedrock',
    title: t('deploy_bedrock'),
    desc: t('deploy_deploy_bedrock_dedicated_server'),
    icon: '◇',
  },
  {
    id: 'package',
    title: t('deploy_upload_modpack'),
    desc: t('deploy_upload_extract_and_auto_detect_the_server_core'),
    icon: '↑',
  },
  {
    id: 'mcdr',
    title: 'MCDR',
    desc: t('deploy_manage_the_minecraft_server_with_python'),
    icon: '⌘',
  },
])

const steps = computed(() => {
  // 在 computed 内取文案，切换语言后会重新计算。
  const label = {
    basic: t('deploy_basic_info'),
    core: t('deploy_core_files'),
    version: t('deploy_server_version'),
    upload: t('deploy_upload_modpack_2'),
    coreConfig: t('deploy_core_config'),
    environment: t('deploy_environment'),
    confirm: t('deploy_confirmation'),
    deploy: t('deploy_deploy'),
    result: t('deploy_result'),
  }
  return data.value.mode === 'quick'
    ? [label.basic, label.core, label.environment, label.confirm, label.deploy, label.result]
    : data.value.mode === 'bedrock'
      ? [label.basic, label.version, label.environment, label.confirm, label.deploy, label.result]
      : data.value.mode === 'package'
        ? [label.upload, label.basic, label.coreConfig, label.environment, label.confirm, label.deploy, label.result]
        : [label.basic, label.core, label.environment, label.confirm, label.deploy, label.result]
})

// 整合包多一步上传，环境与确认步骤随模式偏移。
const environmentStep = computed(() => (data.value.mode === 'package' ? 4 : 3))
const confirmStep = computed(() => (data.value.mode === 'package' ? 5 : 4))
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
  if ((data.value.mode === 'quick' || data.value.mode === 'mcdr') && step.value === 2)
    return Boolean(data.value.coreType && data.value.mcVersion && data.value.buildVersion)
  if (data.value.mode === 'package' && step.value === 2) return validBasic.value
  if (data.value.mode === 'bedrock' && step.value === 2) return Boolean(data.value.mcVersion) && !modeLoading.value
  if (step.value === environmentStep.value)
    return (
      data.value.memory >= 512 &&
      data.value.memory <= 131072 &&
      (data.value.mode !== 'bedrock' || (acceptEula.value && ipv6Port.value !== data.value.port))
    )
  if (data.value.mode === 'package' && step.value === 3) return Boolean(data.value.coreType)
  if (step.value === confirmStep.value) return true
  return true
})

function selectMode(mode: Mode) {
  data.value.mode = mode
  data.value.port = mode === 'bedrock' ? 19132 : 25565
  acceptEula.value = false
  if (mode === 'bedrock') loadBedrockVersions()
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
async function loadBedrockVersions() {
  modeLoading.value = true
  try {
    const result = await request<{ supported: boolean; message?: string; versions: typeof bedrockVersions.value }>(
      '/api/deploy/bedrock/versions',
    )
    if (!result.supported) throw Error(result.message)
    bedrockVersions.value = result.versions
    data.value.coreType = 'bedrock'
    data.value.mcVersion = result.versions[0]?.id || ''
    data.value.buildVersion = data.value.mcVersion
  } catch (cause) {
    error.value = getErrorMessage(cause)
  } finally {
    modeLoading.value = false
  }
}
function setCore(value: { core: string; version: string; build: string; source?: string }) {
  deploySource.value = value.source || 'fastmirror'
  data.value.coreType = value.core
  data.value.mcVersion = value.version
  data.value.buildVersion = value.build
  // 低于核心最低要求时才提升默认 Java。
  const match = value.version.match(/^(\d+)(?:\.(\d+))?(?:\.(\d+))?/)
  const minimum =
    Number(match?.[1]) >= 26
      ? 25
      : Number(match?.[2]) >= 21 || (Number(match?.[2]) === 20 && Number(match?.[3]) >= 5)
        ? 21
        : 17
  if (Number(data.value.javaVersion) < minimum) data.value.javaVersion = String(minimum)
}
// 点击和拖放共用校验，换包时清除旧的核心信息。
function choosePackage(file?: File) {
  if (!file) return
  if (!/\.(zip|tar\.gz|tgz)$/i.test(file.name)) {
    error.value = t('deploy_only_zip_tar_gz_or_tgz_modpacks_are_supported')
    return
  }
  if (file.size > packageLimitMb.value * 1024 * 1024) {
    error.value = t('deploy_modpack_too_large', { size: packageLimitMb.value })
    return
  }
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
  if (event.dataTransfer?.files.length !== 1) {
    error.value = t('deploy_select_one_modpack_at_a_time')
    return
  }
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
    if (!response.core_candidates?.some((item) => item.kind === 'jar' || item.kind === 'args'))
      throw new Error(t('deploy_no_launchable_core_found_in_the_modpack'))
    data.value.packageInfo = response
    const candidate = response.core_candidates?.find((item) => item.recommended) || response.core_candidates?.[0]
    if (candidate) data.value.coreType = candidate.path
    step.value++
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = err.data?.message || err.message || t('deploy_could_not_analyze_the_modpack')
  } finally {
    busy.value = false
  }
}

async function deploy() {
  busy.value = true
  isDeploying.value = true
  progress.value = 0
  deployStatus.value = t('deploy_preparing_deployment')
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
      deployStatus.value = t('deploy_uploading_and_validating_the_modpack_the_instanc')
      progress.value = null
      result.value = await request<DeployResult>('/api/instances/package', { method: 'POST', body: form })
      progress.value = 100
      deployStatus.value = t('deploy_modpack_imported_and_instance_created_start_it_m')
      step.value = steps.value.length
      return
    } else {
      result.value = await request<DeployResult>('/api/instances/deploy', {
        method: 'POST',
        body: {
          mode: data.value.mode === 'mcdr' ? 'mcdr' : data.value.mode === 'bedrock' ? 'bedrock' : 'java',
          accept_eula: acceptEula.value,
          ipv6_port: ipv6Port.value,
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
        deployStatus.value = t('deploy_deployment_complete')
        step.value = steps.value.length
      }
    }
    deployStream.onerror = () => {
      deployStream?.close()
      error.value = t('deploy_deployment_progress_connection_lost_check_the_ba')
      deployStatus.value = error.value
    }
  } catch (cause: unknown) {
    const err = cause as { data?: { message?: string }; message?: string }
    error.value = err.data?.message || err.message || t('deploy_deployment_failed')
    deployStatus.value = error.value
  } finally {
    busy.value = false
  }
}

function next() {
  if (busy.value || isDeploying.value) return
  error.value = ''
  if (!canContinue.value) {
    error.value = t('deploy_complete_the_current_step_first')
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
    <WorkspaceBackground />
    <main class="relative z-10 min-h-screen px-6 py-10 text-text-primary md:px-10">
      <div class="mx-auto w-full max-w-6xl">
        <header class="flex items-end justify-between border-b border-border pb-7">
          <div>
            <p class="font-mono text-[10px] tracking-[0.22em] text-text-secondary">
              / ATMOSPHERE / INSTANCE PROVISIONING
            </p>
            <h1 class="mt-3 font-serif text-4xl md:text-5xl">
              {{ step === 0 ? t('deploy_choose_a_mode') : t('deploy_new_instance') }}
            </h1>
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
              ><span v-if="mode.icon" class="text-xl text-brand transition-transform group-hover:translate-x-1">{{
                mode.icon
              }}</span>
            </div>
            <p class="mt-8 text-sm text-text-secondary">{{ mode.desc }}</p>
            <span class="mt-5 block font-mono text-[10px] tracking-[0.16em] text-brand"
              >{{ t('deploy_select_mode') }} →</span
            >
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
              <h2 class="mt-4 font-serif text-3xl">
                {{ t('deploy_instance_created') }}
              </h2>
              <p class="mt-4 text-sm text-text-secondary">
                {{ t('deploy_the_server_was_written_to_an_isolated_instance_d') }}
              </p>
              <button
                type="button"
                class="mt-8 border border-brand px-5 py-3 font-mono text-xs text-brand hover:bg-brand/10"
                @click="navigateTo('/dashboard')"
              >
                {{ t('deploy_back_to_instances') }} →
              </button>
            </section>
            <section
              v-else-if="data.mode === 'package' && step === 1"
              key="package-upload"
              class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
            >
              <p class="font-mono text-[10px] tracking-[0.2em] text-brand">01 / PACKAGE UPLOAD</p>
              <h2 class="mt-4 font-serif text-3xl">
                {{ t('deploy_upload_modpack') }}
              </h2>
              <p class="mt-3 text-sm text-text-secondary">
                {{ t('deploy_auto_extraction_path_safety_checks_and_core_dete') }}
              </p>
              <label
                data-package-dropzone
                tabindex="0"
                role="button"
                :class="dragging ? 'border-brand bg-brand/10' : ''"
                @dragover.prevent="dragging = true"
                @dragleave.prevent="dragging = false"
                @drop.prevent="onDrop"
                @keydown.enter.prevent="packageInput?.click()"
                @keydown.space.prevent="packageInput?.click()"
                class="mt-8 flex cursor-pointer flex-col items-center border border-dashed border-border p-10 text-center hover:border-brand"
                ><span class="text-3xl text-brand">↑</span
                ><strong class="mt-3 font-mono text-sm">{{
                  data.packageFile?.name || t('deploy_drop_a_file_here_or_click_to_choose_zip_tar_gz_t')
                }}</strong
                ><small class="mt-2 text-xs text-text-secondary">{{ t('deploy_up_to') }} {{ packageLimitMb }}MB</small
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
              <h2 class="mt-4 font-serif text-3xl">
                {{ t('deploy_instance_basics') }}
              </h2>
              <p v-if="data.mode === 'mcdr'" class="mt-4 text-sm leading-7 text-text-secondary">
                {{ t('deploy_creates_an_instance_local_python_environment_for') }}
              </p>
              <p v-if="data.mode === 'bedrock'" class="mt-4 text-sm leading-7 text-text-secondary">
                {{ t('deploy_native_bds_does_not_need_java_the_memory_value_i') }}
              </p>
              <div v-if="data.mode === 'bedrock'" class="mt-5 space-y-4">
                <label class="block text-sm"
                  >{{ t('deploy_ipv6_udp_port')
                  }}<input
                    v-model.number="ipv6Port"
                    type="number"
                    min="1"
                    max="65535"
                    class="mt-2 w-full border border-border bg-transparent p-3"
                /></label>
              </div>
              <div class="mt-8 space-y-5">
                <label class="block text-xs text-text-secondary"
                  >{{ t('deploy_instance_name')
                  }}<input
                    v-model="data.name"
                    class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                    placeholder="Survival-Server" /></label
                ><label class="block text-xs text-text-secondary"
                  >{{ t('deploy_server_port')
                  }}<input
                    v-model.number="data.port"
                    class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
                    type="number"
                /></label>
              </div>
            </section>
            <section
              v-else-if="(data.mode === 'quick' || data.mode === 'mcdr') && step === 2"
              key="quick-core"
              class="mt-12"
            >
              <Step2CoreSelector @select="setCore"></Step2CoreSelector>
            </section>
            <AtmosphereCard
              v-else-if="data.mode === 'bedrock' && step === 2"
              key="bedrock-version"
              :interactive="false"
              class="mx-auto mt-12 max-w-xl"
              ><h2 class="font-serif text-2xl">
                {{ t('deploy_official_bedrock_server') }}
              </h2>
              <p class="my-5 text-sm leading-7 text-text-secondary">
                {{ t('deploy_fetches_the_supported_stable_release_from_mojang') }}
              </p>
              <p v-if="modeLoading" class="text-xs text-brand">
                {{ t('deploy_loading_official_versions') }}
              </p>
              <AtmosphereSelect
                v-else
                v-model="data.mcVersion"
                label="BDS VERSION"
                :options="bedrockVersions.map((item) => ({ value: item.id, label: item.label }))"
              /><button type="button" class="mt-4 text-xs text-brand" @click="loadBedrockVersions">
                {{ t('deploy_refresh_catalog') }}
              </button></AtmosphereCard
            >
            <section
              v-else-if="data.mode === 'package' && step === 3"
              key="package-core"
              class="mx-auto mt-12 max-w-xl border border-border bg-surface/50 p-8"
            >
              <p class="font-mono text-[10px] tracking-[0.2em] text-brand">03 / CORE CONFIG</p>
              <h2 class="mt-4 font-serif text-3xl">{{ t('deploy_core_detection') }}</h2>
              <p class="mt-4 text-sm text-text-secondary">
                {{ t('deploy_found') }} {{ data.packageInfo?.core_candidates?.length || 0 }}
                {{ t('deploy_candidate_cores') }}
              </p>
              <select
                v-model="data.coreType"
                class="mt-8 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm outline-none focus:border-brand"
              >
                <option
                  v-for="candidate in data.packageInfo?.core_candidates?.filter(
                    (item) => item.kind === 'jar' || item.kind === 'args',
                  ) || []"
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
              <h2 class="mt-4 font-serif text-3xl">{{ t('deploy_environment_settings') }}</h2>
              <p class="mt-3 text-sm text-text-secondary">
                {{
                  data.mode === 'bedrock'
                    ? t('deploy_runs_the_native_official_bds_no_java_needed_memo')
                    : data.mode === 'mcdr'
                      ? t('deploy_runs_mcdr_in_an_instance_local_python_environmen')
                      : t('deploy_the_host_environment_is_checked_a_setup_hint_app')
                }}
              </p>
              <label v-if="data.mode === 'bedrock'" class="flex items-center gap-3 text-sm"
                ><input v-model="acceptEula" type="checkbox" class="accent-brand" />{{ t('deploy_agree') }}
                <a
                  href="https://aka.ms/MinecraftEULA"
                  target="_blank"
                  rel="noopener noreferrer"
                  class="text-brand underline"
                  >Minecraft EULA</a
                ></label
              >
              <div class="mt-8 space-y-5">
                <label v-if="data.mode !== 'bedrock'" class="block text-xs text-text-secondary"
                  >{{ t('deploy_java_version')
                  }}<select
                    v-model="data.javaVersion"
                    class="mt-2 w-full border border-border bg-background/50 px-4 py-3 font-mono text-sm"
                  >
                    <option>8</option>
                    <option>17</option>
                    <option>21</option>
                  </select></label
                ><label class="block text-xs text-text-secondary"
                  >{{ t('deploy_memory_mb')
                  }}<input
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
              <h2 class="mt-4 font-serif text-3xl">
                {{ t('deploy_confirm_deployment') }}
              </h2>
              <p v-if="data.mode === 'package'" class="mt-5 text-sm break-all text-text-secondary">
                {{ t('deploy_modpack') }}{{ data.packageFile?.name }}
              </p>
              <dl class="mt-8 divide-y divide-border font-mono text-sm">
                <div class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_instance_name') }}</dt>
                  <dd>{{ data.name }}</dd>
                </div>
                <div class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_server_port') }}</dt>
                  <dd>{{ data.port }}</dd>
                </div>
                <div class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_core') }}</dt>
                  <dd>{{ data.coreType || data.mode }}</dd>
                </div>
                <div v-if="data.mode !== 'package'" class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_game_version') }}</dt>
                  <dd>{{ data.mcVersion || '—' }}</dd>
                </div>
                <div v-if="data.mode !== 'package'" class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_build') }}</dt>
                  <dd>{{ data.buildVersion || '—' }}</dd>
                </div>
                <div v-if="data.mode !== 'bedrock'" class="flex justify-between py-4">
                  <dt class="text-text-secondary">Java</dt>
                  <dd>{{ data.javaVersion }}</dd>
                </div>
                <div class="flex justify-between py-4">
                  <dt class="text-text-secondary">{{ t('deploy_memory') }}</dt>
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
              ← {{ t('deploy_back') }}</button
            ><button
              v-if="!isComplete"
              type="button"
              class="border border-brand px-5 py-2 font-mono text-xs text-brand hover:bg-brand/10 disabled:opacity-40"
              :disabled="busy || !canContinue"
              @click="next"
            >
              {{ busy ? t('deploy_working') : step === confirmStep ? t('deploy_confirm_deploy') : t('deploy_next') }}
              →
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
              <p class="font-mono text-xs text-text-secondary" :class="error ? 'text-red-400' : ''">
                {{ deployStatus }}
              </p>
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
                {{ t('deploy_open_console') }} →
              </button>
            </div>
          </AtmosphereCard>
        </div>
      </div>
      <div class="mx-auto mt-10 w-full max-w-6xl">
        <a href="/dashboard" class="font-mono text-sm tracking-[0.18em] text-text-secondary hover:text-brand">
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
