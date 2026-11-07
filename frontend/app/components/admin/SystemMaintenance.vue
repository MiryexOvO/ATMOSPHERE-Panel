<script setup lang="ts">
import MechanicalSwitch from '~/components/ui/MechanicalSwitch.vue'
import ExpandTransition from '~/components/ui/ExpandTransition.vue'
const { t } = useI18n()
const settings = defineModel<Record<string, any>>({ required: true })
const emit = defineEmits<{ save: [] }>()
const { request, getErrorMessage } = useApi()
type Update = {
  current: string
  latest?: string
  available: boolean
  message?: string
  notes?: string
  page?: string
  ready?: { version: string; sha256: string }
  download?: { status: string; progress: number; error: string }
}
const update = ref<Update | null>(null),
  busy = ref(false),
  message = ref(''),
  certificate = ref<File | null>(null),
  key = ref<File | null>(null)
async function check() {
  busy.value = true
  message.value = ''
  try {
    update.value = await request<Update>('/api/panel/updates')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
// 下载完成保留更新包，安装过程不触碰运行中的实例。
async function download() {
  busy.value = true
  message.value = ''
  try {
    await request('/api/panel/updates/download', { method: 'POST', timeout: 600000 })
    update.value = await request<Update>('/api/panel/updates')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
async function upload() {
  if (!certificate.value || !key.value) return
  busy.value = true
  try {
    const form = new FormData()
    form.append('certificate', certificate.value)
    form.append('private_key', key.value)
    await request('/api/panel/tls/certificate', { method: 'POST', body: form })
    message.value = t('msg_certificate_validated_and_saved')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
const httpsAddress = computed(() =>
  typeof location === 'undefined' ? '' : `https://${location.hostname}:${settings.value.https_port}`,
)
</script>
<template>
  <div class="space-y-8 border-t border-border pt-7">
    <section class="space-y-5">
      <header class="flex items-center justify-between">
        <div>
          <p class="font-mono text-[10px] tracking-widest text-brand">/ MAINTENANCE</p>
          <h3 class="mt-2 font-serif text-xl">{{ t('msg_software_update') }}</h3>
        </div>
        <button type="button" :disabled="busy" class="border border-brand px-4 py-3 text-xs text-brand" @click="check">
          {{ busy ? t('msg_processing') : t('msg_check_for_updates') }}
        </button>
      </header>
      <label class="flex items-center justify-between border border-border p-4 text-sm"
        >{{ t('msg_auto_download_releases_hourly')
        }}<MechanicalSwitch v-model="settings.update_auto_download" :label="t('msg_auto_download')"
      /></label>
      <div v-if="update" class="space-y-4 border-l border-brand pl-4">
        <p class="font-mono text-sm">
          {{ update.current }} <span v-if="update.latest">→ {{ update.latest }}</span>
        </p>
        <p class="text-sm text-text-secondary">
          {{ update.message || (update.available ? t('msg_new_version_available') : t('msg_up_to_date')) }}
        </p>
        <pre
          v-if="update.notes"
          class="max-h-60 overflow-auto font-mono text-xs leading-6 whitespace-pre-wrap text-text-secondary"
          >{{ update.notes }}</pre>
        <div class="flex flex-wrap gap-5 text-xs text-brand">
          <button v-if="update.available" type="button" :disabled="busy" @click="download">
            {{ t('msg_download_update') }}</button
          ><a v-if="update.page" :href="update.page" target="_blank" rel="noopener noreferrer">{{
            t('msg_release_page')
          }}</a
          ><a v-if="update.ready" href="/api/panel/updates/package">{{ t('msg_save_downloaded_package') }}</a>
        </div>
        <p v-if="update.ready" class="font-mono text-[10px] break-all text-text-secondary">
          {{ update.ready.version }} · SHA256 {{ update.ready.sha256 }}
        </p>
      </div>
      <p class="text-xs leading-6 text-text-secondary">
        {{ t('msg_update_packages_are_stored_in_the_panel_data') }}
      </p>
    </section>
    <section class="space-y-5 border-t border-border pt-7">
      <p class="font-mono text-[10px] tracking-widest text-brand">/ ENCRYPTION</p>
      <h3 class="font-serif text-xl">{{ t('msg_https_access') }}</h3>
      <div class="grid gap-4 md:grid-cols-2">
        <label class="flex items-center justify-between border border-border p-4 text-sm"
          >{{ t('msg_enable_https') }}<MechanicalSwitch v-model="settings.https_enabled" label="HTTPS" /></label
        ><label class="flex items-center justify-between border border-border p-4 text-sm"
          >{{ t('msg_self_signed_certificate')
          }}<MechanicalSwitch v-model="settings.https_self_signed" label="SELF-SIGNED"
        /></label>
      </div>
      <ExpandTransition
        ><div v-if="settings.https_enabled" class="grid gap-5 md:grid-cols-2">
          <label class="space-y-2 text-xs"
            >{{ t('msg_https_port')
            }}<input
              v-model.number="settings.https_port"
              type="number"
              min="1024"
              max="65535"
              class="block w-full border border-border bg-transparent p-3" /></label
          ><label class="space-y-2 text-xs"
            >{{ t('msg_local_frontend_port')
            }}<input
              v-model.number="settings.frontend_port"
              type="number"
              min="1024"
              max="65535"
              class="block w-full border border-border bg-transparent p-3"
          /></label>
          <p class="text-xs leading-6 text-text-secondary md:col-span-2">
            {{ t('msg_after_saving_use_the_https_entry_browsers_re') }}
            <a :href="httpsAddress" target="_blank" rel="noopener noreferrer" class="text-brand underline">{{
              httpsAddress
            }}</a>
          </p>
        </div></ExpandTransition
      ><ExpandTransition
        ><div v-if="!settings.https_self_signed" class="space-y-4">
          <p class="text-xs text-text-secondary">
            {{ t('msg_disable_and_save_https_before_uploading_pem_') }}
          </p>
          <label class="block text-xs"
            >CERTIFICATE PEM<input
              type="file"
              accept=".pem,.crt"
              class="mt-2 block"
              @change="certificate = ($event.target as HTMLInputElement).files?.[0] || null" /></label
          ><label class="block text-xs"
            >PRIVATE KEY PEM<input
              type="file"
              accept=".pem,.key"
              class="mt-2 block"
              @change="key = ($event.target as HTMLInputElement).files?.[0] || null" /></label
          ><button type="button" :disabled="busy || !certificate || !key" class="text-xs text-brand" @click="upload">
            {{ t('msg_validate_save_certificate') }}
          </button>
        </div></ExpandTransition
      >
    </section>
    <p v-if="message" role="status" class="text-sm text-brand">{{ message }}</p>
  </div>
</template>
