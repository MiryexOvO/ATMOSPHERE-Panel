<script setup lang="ts">
import SystemMaintenance from './SystemMaintenance.vue'
const props = defineProps<{ section: 'system' | 'basic' }>()
const { t, locale } = useI18n()
const { request, getErrorMessage } = useApi()
const settings = reactive({
  download_source: 'default',
  metrics_interval_seconds: 5,
  session_hours: 24,
  default_locale: 'zh',
  upload_limit_mb: 500,
  update_auto_download: false,
  https_enabled: false,
  https_self_signed: true,
  https_port: 8443,
  frontend_port: 5173,
})
const loaded = ref(false),
  saving = ref(false),
  message = ref(''),
  failed = ref(false)
const fields = [
  { key: 'metrics_interval_seconds', label: 'panelInterval', type: 'number', min: 2, max: 60 },
  { key: 'session_hours', label: 'panelSession', type: 'number', min: 1, max: 168 },
  { key: 'upload_limit_mb', label: 'panelUpload', type: 'number', min: 1, max: 500 },
] as const
const sources = computed(() => [
  { value: 'default', label: t('mirrorDefault') },
  { value: 'official', label: t('mirrorOfficial') },
  { value: 'fastmirror', label: 'FASTMIRROR' },
  { value: 'polars', label: 'POLARS' },
])
const preferenceState = useState<Record<string, unknown>>('panel-preferences', () => ({}))
// 系统与基础设置共用持久化配置。
async function load() {
  try {
    const data = await request<{ settings: typeof settings }>('/api/panel/settings')
    Object.assign(settings, data.settings)
    loaded.value = true
  } catch (error) {
    failed.value = true
    message.value = getErrorMessage(error)
  }
}
async function save() {
  if (!loaded.value || saving.value) return
  saving.value = true
  try {
    const result = await request<{ settings: typeof settings }>('/api/panel/settings', {
      method: 'PUT',
      body: settings,
    })
    preferenceState.value = result.settings
    if (props.section === 'basic') locale.value = settings.default_locale as 'zh' | 'en' | 'ja'
    failed.value = false
    message.value = t('panelSaved')
  } catch (error) {
    failed.value = true
    message.value = getErrorMessage(error)
  } finally {
    saving.value = false
  }
}
onMounted(load)
</script>
<template>
  <AtmosphereCard :interactive="false">
    <form class="space-y-7" @submit.prevent="save">
      <header class="flex items-start justify-between gap-4">
        <div>
          <p class="font-mono text-[10px] tracking-[.2em] text-brand">
            / {{ section === 'system' ? 'MIRROR ROUTING' : 'OPERATOR CONFIG' }}
          </p>
          <h2 class="mt-3 font-serif text-2xl">
            {{ t(section === 'system' ? 'downloadSourceTitle' : 'panelSettingsTitle') }}
          </h2>
        </div>
        <button
          type="submit"
          :disabled="!loaded || saving"
          class="border border-brand px-4 py-2 text-xs text-brand disabled:opacity-40"
        >
          {{ t(saving ? 'settingsSaving' : 'fileSave') }}
        </button>
      </header>
      <p v-if="message" role="status" class="text-sm" :class="failed ? 'text-red-400' : 'text-brand'">{{ message }}</p>
      <fieldset :disabled="!loaded || saving" class="space-y-6">
        <template v-if="section === 'system'">
          <p class="max-w-3xl text-sm leading-7 text-text-secondary">{{ t('panelSourceHint') }}</p>
          <div class="max-w-2xl">
            <p class="mb-2 text-xs text-text-secondary">{{ t('mirrorLabel') }}</p>
            <AtmosphereSelect
              v-model="settings.download_source"
              :label="t('mirrorLabel')"
              :options="sources"
              @update:model-value="save"
            />
          </div>
        </template>
        <div v-else class="grid gap-6 md:grid-cols-2">
          <label v-for="field in fields" :key="field.key" class="space-y-2"
            ><span class="block text-xs text-text-secondary">{{ t(field.label) }}</span
            ><input
              v-model="settings[field.key]"
              :type="field.type"
              :min="field.min"
              :max="field.max"
              required
              class="w-full border border-border bg-background px-3 py-3 text-sm outline-none focus:border-brand"
          /></label>
          <div class="space-y-2">
            <span class="block text-xs text-text-secondary">{{ t('panelLanguage') }}</span
            ><AtmosphereSelect
              v-model="settings.default_locale"
              :label="t('panelLanguage')"
              :options="[
                { value: 'zh', label: '中文' },
                { value: 'en', label: 'ENGLISH' },
                { value: 'ja', label: '日本語' },
              ]"
            />
          </div>
        </div>
        <SystemMaintenance v-if="section === 'basic'" v-model="settings" @save="save" />
      </fieldset>
    </form>
  </AtmosphereCard>
</template>
