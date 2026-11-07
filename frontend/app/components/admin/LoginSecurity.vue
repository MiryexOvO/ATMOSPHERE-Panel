<script setup lang="ts">
import LocalScrollRuler from '~/components/ui/LocalScrollRuler.vue'
const tr = usePanelText(),
  { request, getErrorMessage } = useApi()
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
      message.value = tr('二步验证设置已保存', 'Two-factor settings saved', '二段階認証の設定を保存しました')
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
          <h3 class="mt-2 font-serif text-xl">{{ tr('登录验证与提醒', 'LOGIN SECURITY', 'ログイン保護') }}</h3>
        </div>
        <span class="font-mono text-xs" :class="enabled ? 'text-data-live' : 'text-text-secondary'"
          >TOTP · {{ enabled ? 'ON' : 'OFF' }}</span
        >
      </header>
      <p class="text-xs leading-6 text-text-secondary">
        {{
          tr(
            '使用认证器生成六位验证码。新网络登录会显示提醒；仅比较网络来源，不推测地理位置。请妥善保存验证器密钥。',
            'Use an authenticator for six-digit codes. New-network sign-ins are flagged without inferring location. Keep your authenticator secret safe.',
            '認証アプリの 6 桁コードを使用。新しいネットワークからのログインを通知します。位置情報の推測は行いません。鍵を安全に保管してください。',
          )
        }}
      </p>
      <div class="grid gap-4 md:grid-cols-2">
        <label class="space-y-2 text-xs"
          >{{ tr('当前密码', 'CURRENT PASSWORD', '現在のパスワード')
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
          {{
            tr(
              '在验证器中手动添加以下密钥，再输入验证码确认。',
              'Add this secret in your authenticator, then confirm with its code.',
              '認証アプリに以下の鍵を登録し、確認コードを入力してください。',
            )
          }}
        </p>
        <code class="text-sm break-all text-brand">{{ secret }}</code
        ><a :href="uri" class="block text-xs text-brand underline">{{
          tr('打开本机验证器', 'OPEN AUTHENTICATOR', '認証アプリを開く')
        }}</a>
      </div>
      <div class="flex gap-5 text-xs text-brand">
        <button v-if="!enabled && !secret" :disabled="busy || !password" @click="act('setup')">
          {{ tr('配置二步验证', 'SET UP TWO-FACTOR', '二段階認証を設定') }}</button
        ><button v-if="secret" :disabled="busy || code.length !== 6" @click="act('confirm')">
          {{ tr('确认启用', 'CONFIRM ENABLE', '有効化を確認') }}</button
        ><button v-if="enabled" :disabled="busy || !password || code.length !== 6" @click="act('disable')">
          {{ tr('关闭二步验证', 'DISABLE TWO-FACTOR', '二段階認証を無効化') }}
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
              >{{
                event.unusual ? tr('新网络登录', 'NEW NETWORK', '新しいネットワーク') : event.success ? 'OK' : 'FAILED'
              }}</span
            >
          </div>
        </div>
        <LocalScrollRuler :target="eventsViewport" />
      </div></section
  ></AtmosphereCard>
</template>
