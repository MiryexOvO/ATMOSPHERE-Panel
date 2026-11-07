<script setup lang="ts">
import LocalScrollRuler from '~/components/ui/LocalScrollRuler.vue'
const { t } = useI18n()
const { request, getErrorMessage } = useApi()
const enabled = ref(false),
  password = ref(''),
  code = ref(''),
  secret = ref(''),
  uri = ref(''),
  busy = ref(false),
  message = ref('')
const events = ref<
  { id: number; ip: string; network: string; success: boolean; unusual: boolean; created_at: number }[]
>([])
const eventsViewport = ref<HTMLElement | null>(null)
async function load() {
  try {
    const data = await request<{ totp_enabled: boolean; events: typeof events.value }>('/api/account/security')
    enabled.value = data.totp_enabled
    events.value = data.events
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
// 密钥只在本地展示，不使用外部二维码服务。
async function act(action: 'setup' | 'confirm' | 'disable') {
  busy.value = true
  message.value = ''
  try {
    const data = await request<{ secret?: string; uri?: string }>('/api/account/totp/' + action, {
      method: 'POST',
      body: { password: password.value, code: code.value },
    })
    if (action === 'setup') {
      secret.value = data.secret || ''
      uri.value = data.uri || ''
    } else {
      secret.value = ''
      uri.value = ''
      password.value = ''
      code.value = ''
      await load()
      message.value = t('msg_two_factor_settings_saved')
    }
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>
<template>
  <AtmosphereCard :interactive="false"
    ><section class="space-y-5">
      <header class="flex items-center justify-between">
        <div>
          <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ ACCESS GUARD</p>
          <h3 class="mt-2 font-serif text-xl">{{ t('msg_login_security') }}</h3>
        </div>
        <span class="font-mono text-xs" :class="enabled ? 'text-data-live' : 'text-text-secondary'"
          >TOTP · {{ enabled ? 'ON' : 'OFF' }}</span
        >
      </header>
      <p class="text-xs leading-6 text-text-secondary">
        {{ t('msg_use_an_authenticator_for_six_digit_codes_new') }}
      </p>
      <div class="grid gap-4 md:grid-cols-2">
        <label class="space-y-2 text-xs"
          >{{ t('msg_current_password')
          }}<input
            v-model="password"
            type="password"
            autocomplete="current-password"
            maxlength="72"
            class="block w-full border border-border bg-transparent p-3" /></label
        ><label class="space-y-2 text-xs"
          >TOTP<input
            v-model="code"
            inputmode="numeric"
            autocomplete="one-time-code"
            maxlength="6"
            pattern="[0-9]{6}"
            class="block w-full border border-border bg-transparent p-3 font-mono"
        /></label>
      </div>
      <div v-if="secret" class="space-y-3 border-l border-brand pl-4">
        <p class="text-xs text-text-secondary">
          {{ t('msg_add_this_secret_in_your_authenticator_then_c') }}
        </p>
        <code class="text-sm break-all text-brand">{{ secret }}</code
        ><a :href="uri" class="block text-xs text-brand underline">{{ t('msg_open_authenticator') }}</a>
      </div>
      <div class="flex gap-5 text-xs text-brand">
        <button v-if="!enabled && !secret" :disabled="busy || !password" @click="act('setup')">
          {{ t('msg_set_up_two_factor') }}</button
        ><button v-if="secret" :disabled="busy || code.length !== 6" @click="act('confirm')">
          {{ t('msg_confirm_enable') }}</button
        ><button v-if="enabled" :disabled="busy || !password || code.length !== 6" @click="act('disable')">
          {{ t('msg_disable_two_factor') }}
        </button>
      </div>
      <p v-if="message" role="status" class="text-sm text-brand">{{ message }}</p>
      <div class="relative">
        <div ref="eventsViewport" class="max-h-64 overflow-y-auto border-t border-border pt-3 pr-6">
          <div
            v-for="event in events"
            :key="event.id"
            class="grid grid-cols-[minmax(0,1fr)_minmax(0,1fr)_7rem] items-center gap-3 border-b border-border py-3 font-mono text-xs"
          >
            <span class="truncate">{{ new Date(event.created_at * 1000).toLocaleString() }}</span>
            <span class="truncate pl-[80px]">{{ event.ip }}</span>
            <span
              class="text-right"
              :class="event.unusual ? 'text-amber-300' : event.success ? 'text-text-secondary' : 'text-red-400'"
              >{{ event.unusual ? t('msg_new_network') : event.success ? 'OK' : 'FAILED' }}</span
            >
          </div>
        </div>
        <LocalScrollRuler :target="eventsViewport" />
      </div></section
  ></AtmosphereCard>
</template>
