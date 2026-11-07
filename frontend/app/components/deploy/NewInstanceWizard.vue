<script setup lang="ts">
import DeployLayout from './DeployLayout.vue'
import VersionWizardModal from './VersionWizardModal.vue'
const { t } = useI18n()

const emit = defineEmits<{ close: []; complete: [] }>()
const step = ref(1)
const formData = reactive({
  name: '',
  port: 25565,
  coreType: '',
  mcVersion: '',
  buildVersion: '',
  javaVersion: '',
  memory: '4G',
  useAikar: true,
})
const coreModal = ref(false)
type CoreOption = { id: string; name: string }
const selectedCore = ref<CoreOption | null>(null)
const versions = ref<string[]>([])
const builds = ref<Record<string, string[]>>({})
const { request } = useApi()
async function openCoreModal(core: CoreOption) {
  selectedCore.value = core
  versions.value = []
  try {
    const response = await request<{ versions: { id: string }[] }>(`/api/resources/cores/${core.id}/versions`)
    versions.value = response.versions.map((item) => item.id)
    coreModal.value = true
  } catch (error) {
    deployMessage.value = error instanceof Error ? error.message : t('deploy_failed_to_load_versions')
  }
}
const deployStatus = ref('idle')
const deployPercent = ref(0)
const deployMessage = ref('')
const deploySteps = ref([
  { state: 'pending' },
  { state: 'pending' },
  { state: 'pending' },
  { state: 'pending' },
  { state: 'pending' },
])
const deployStepLabels = computed(() => [
  t('deploy_create_instance_directory'),
  t('deploy_download_java_runtime'),
  t('deploy_download_core_files'),
  t('deploy_generate_configuration'),
  t('deploy_start_the_server'),
])
const wizardSteps = computed(() => [
  t('deploy_basic_info'),
  t('deploy_core_files'),
  t('deploy_java_jvm'),
  t('deploy_confirmation'),
  t('deploy_deploy'),
])
const validBasic = computed(
  () => /^[A-Za-z0-9-]{2,48}$/.test(formData.name) && formData.port > 0 && formData.port < 65536,
)
const canNext = computed(() =>
  step.value === 1
    ? validBasic.value
    : step.value === 2
      ? !!formData.coreType && !!formData.mcVersion && !!formData.buildVersion
      : step.value === 3
        ? !!formData.javaVersion && !!formData.memory
        : true,
)
function chooseCore(core: CoreOption, version: string, build: string) {
  selectedCore.value = core
  formData.coreType = core.name
  formData.mcVersion = version
  formData.buildVersion = build
  coreModal.value = false
}
function recommendJava(version: string) {
  formData.javaVersion = version.startsWith('1.16')
    ? '8'
    : version.startsWith('1.17')
      ? '16'
      : version.startsWith('1.18') || version.startsWith('1.19') || version === '1.20.4'
        ? '17'
        : '21'
}
watch(
  () => formData.mcVersion,
  (value) => {
    if (value) recommendJava(value)
  },
)
function next() {
  if (!canNext.value) return
  if (step.value < 4) step.value++
  else if (step.value === 4) {
    step.value = 5
    startDeploy()
  }
}
function back() {
  if (step.value > 1 && step.value < 5) step.value--
}
async function startDeploy() {
  deployStatus.value = 'running'
  deployMessage.value = t('deploy_preparing_deployment_2')
  try {
    const fd = new FormData()
    fd.set('instance_id', formData.name.toLowerCase())
    fd.set('resource', formData.coreType.toLowerCase())
    fd.set('version', formData.mcVersion)
    fd.set('build', formData.buildVersion)
    fd.set('java_version', formData.javaVersion)
    const result = await $fetch<{ task_id: string }>('/api/deploy/tasks', {
      method: 'POST',
      credentials: 'include',
      body: fd,
    })
    const source = new EventSource(`/api/deploy/stream?task_id=${encodeURIComponent(result.task_id)}`)
    source.onmessage = (event) => {
      const data = JSON.parse(event.data)
      deployPercent.value = data.percent || 0
      deployMessage.value = data.stage || data.status
      if (data.status === 'completed') {
        deploySteps.value.forEach((item) => (item.state = 'done'))
        deployStatus.value = 'done'
        source.close()
      }
      if (data.status === 'failed') {
        deployStatus.value = 'failed'
        source.close()
      }
    }
  } catch (error: unknown) {
    const err = error as { data?: { message?: string }; message?: string }
    deployStatus.value = 'failed'
    deployMessage.value = err.data?.message || err.message || t('deploy_deployment_failed_2')
  }
}
</script>
<template>
  <div class="new-wizard-page">
    <header class="wizard-page-header">
      <button class="ghost" :disabled="step === 5" @click="emit('close')">← {{ t('deploy_back_2') }}</button>
      <div>
        <span>ATMOSPHERE / INSTANCE PROVISIONING</span>
        <h1>{{ t('deploy_new_instance') }}</h1>
      </div>
    </header>
    <nav class="wizard-stepper">
      <div
        v-for="item in wizardSteps"
        :key="item"
        :class="{
          active: step === wizardSteps.indexOf(item) + 1,
          done: wizardSteps.indexOf(item) + 1 < step,
        }"
      >
        {{ item }}
      </div>
    </nav>
    <Transition name="wizard-slide" mode="out-in">
      <section v-if="step === 1" key="basic" class="wizard-step-panel">
        <h2>{{ t('deploy_basic_info') }}</h2>
        <p>
          {{ t('deploy_set_the_instance_name_and_network_port') }}
        </p>
        <label
          >{{ t('deploy_instance_name')
          }}<input class="atmo-input" v-model="formData.name" placeholder="Survival-Server" /></label
        ><label
          >{{ t('deploy_server_port_2') }}<input class="atmo-input" type="number" v-model.number="formData.port"
        /></label>
        <p v-if="formData.name && !validBasic" class="wizard-error">
          {{ t('deploy_the_name_may_only_contain_letters_digits_and_hyp') }}
        </p>
      </section>
      <section v-else-if="step === 2" key="core" class="wizard-step-panel">
        <h2>{{ t('deploy_core_files') }}</h2>
        <p>
          {{ t('deploy_selecting_a_core_does_not_download_it_now_it_hap') }}
        </p>
        <button
          class="core-selected"
          @click="openCoreModal(selectedCore || { id: formData.coreType.toLowerCase(), name: formData.coreType })"
        >
          {{
            formData.coreType
              ? `${formData.coreType} ${formData.mcVersion} · Build ${formData.buildVersion}`
              : t('deploy_choose_a_server_core')
          }}
        </button>
        <div v-if="formData.coreType" class="selection-summary">
          {{ t('deploy_selected') }}<strong>{{ formData.coreType }}</strong> / {{ formData.mcVersion }} / Build
          {{ formData.buildVersion }}
        </div>
      </section>
      <section v-else-if="step === 3" key="java" class="wizard-step-panel">
        <h2>{{ t('deploy_java_jvm_settings') }}</h2>
        <p>
          {{ t('deploy_java') }} {{ formData.javaVersion || '17' }}
          {{ t('deploy_has_been_matched_automatically') }}
        </p>
        <label
          >{{ t('deploy_java_version')
          }}<select class="atmo-input" v-model="formData.javaVersion">
            <option>8</option>
            <option>17</option>
            <option>21</option>
          </select></label
        ><label>{{ t('deploy_memory_2') }}<input class="atmo-input" v-model="formData.memory" /></label
        ><label class="switch-line"
          ><input type="checkbox" v-model="formData.useAikar" /> {{ t('deploy_use_aikar_s_flags') }}</label
        >
      </section>
      <section v-else-if="step === 4" key="confirm" class="wizard-step-panel">
        <h2>{{ t('deploy_confirmation') }}</h2>
        <div class="confirm-grid">
          <div>
            <span>{{ t('deploy_instance_name') }}</span
            ><strong>{{ formData.name }}</strong>
          </div>
          <div>
            <span>{{ t('deploy_port') }}</span
            ><strong>{{ formData.port }}</strong>
          </div>
          <div>
            <span>{{ t('deploy_core') }}</span
            ><strong>{{ formData.coreType }}</strong>
          </div>
          <div>
            <span>{{ t('deploy_version') }}</span
            ><strong>{{ formData.mcVersion }} / {{ formData.buildVersion }}</strong>
          </div>
          <div>
            <span>Java</span><strong>{{ formData.javaVersion }}</strong>
          </div>
          <div>
            <span>{{ t('deploy_memory') }}</span
            ><strong>{{ formData.memory }}</strong>
          </div>
        </div>
      </section>
      <section v-else key="deploy" class="wizard-step-panel deploy-progress-panel">
        <h2>
          {{ deployStatus === 'done' ? t('deploy_created_successfully') : t('deploy_deploying') }}
        </h2>
        <p>{{ deployMessage }}</p>
        <div class="deploy-progress-bar"><i :style="{ width: `${deployPercent}%` }"></i></div>
        <strong>{{ deployPercent }}%</strong>
        <div class="deploy-timeline">
          <div v-for="(item, index) in deploySteps" :key="index" :class="item.state">
            {{ item.state === 'done' ? '✓' : '○' }} {{ deployStepLabels[index] }}
          </div>
        </div>
        <button v-if="deployStatus === 'done'" class="primary" @click="emit('complete')">
          {{ t('deploy_open_instance_list') }} →
        </button>
      </section>
    </Transition>
    <footer class="wizard-footer">
      <button class="ghost" :disabled="step === 1 || step === 5" @click="back">
        {{ t('deploy_back') }}</button
      ><button v-if="step < 5" class="primary" :disabled="!canNext" @click="next">
        {{ step === 4 ? t('deploy_confirm_create') : t('deploy_next') }} →
      </button>
    </footer>
    <VersionWizardModal
      v-if="coreModal"
      :open="coreModal"
      :core="selectedCore || { id: 'paper', name: t('deploy_server_core') }"
      :versions="versions"
      @close="coreModal = false"
      @deploy="chooseCore(selectedCore || { name: 'Paper' }, $event[0], $event[1])"
    />
  </div>
</template>
