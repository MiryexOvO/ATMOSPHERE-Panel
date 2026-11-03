<script setup lang="ts">
import MechanicalSwitch from '~/components/ui/MechanicalSwitch.vue'
import ExpandTransition from '~/components/ui/ExpandTransition.vue'
const settings = defineModel<Record<string, any>>({ required: true })
const emit = defineEmits<{ save: [] }>()
const tr = usePanelText(),
  { request, getErrorMessage } = useApi()
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
    message.value = tr('证书已验证并保存', 'Certificate validated and saved', '証明書を検証して保存しました')
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
          <p class="font-mono text-[10px] tracking-widest text-brand">/ SOFTWARE UPDATE</p>
          <h3 class="mt-2 font-serif text-xl">{{ tr('软件更新', 'SOFTWARE UPDATE', 'ソフトウェア更新') }}</h3>
        </div>
        <button type="button" :disabled="busy" class="border border-brand px-4 py-3 text-xs text-brand" @click="check">
          {{ busy ? tr('处理中…', 'PROCESSING…', '処理中…') : tr('检查更新', 'CHECK FOR UPDATES', '更新を確認') }}
        </button>
      </header>
      <label class="flex items-center justify-between border border-border p-4 text-sm"
        >{{
          tr(
            '发现正式版本后自动下载（每小时检查）',
            'AUTO-DOWNLOAD RELEASES (HOURLY)',
            '正式版を自動ダウンロード（毎時確認）',
          )
        }}<MechanicalSwitch
          v-model="settings.update_auto_download"
          :label="tr('自动下载', 'AUTO-DOWNLOAD', '自動ダウンロード')"
      /></label>
      <div v-if="update" class="space-y-4 border-l border-brand pl-4">
        <p class="font-mono text-sm">
          {{ update.current }} <span v-if="update.latest">→ {{ update.latest }}</span>
        </p>
        <p class="text-sm text-text-secondary">
          {{
            update.message ||
            (update.available
              ? tr('发现新版本', 'NEW VERSION AVAILABLE', '新しいバージョンがあります')
              : tr('当前已是最新版本', 'UP TO DATE', '最新版です'))
          }}
        </p>
        <pre
          v-if="update.notes"
          class="max-h-60 overflow-auto font-mono text-xs leading-6 whitespace-pre-wrap text-text-secondary"
          >{{ update.notes }}</pre>
        <div class="flex flex-wrap gap-5 text-xs text-brand">
          <button v-if="update.available" type="button" :disabled="busy" @click="download">
            {{ tr('下载新版本', 'DOWNLOAD UPDATE', '更新をダウンロード') }}</button
          ><a v-if="update.page" :href="update.page" target="_blank" rel="noopener noreferrer">{{
            tr('查看发布页', 'RELEASE PAGE', 'リリースページ')
          }}</a
          ><a v-if="update.ready" href="/api/panel/updates/package">{{
            tr('保存已下载的更新包', 'SAVE DOWNLOADED PACKAGE', 'ダウンロード済みパッケージを保存')
          }}</a>
        </div>
        <p v-if="update.ready" class="font-mono text-[10px] break-all text-text-secondary">
          {{ update.ready.version }} · SHA256 {{ update.ready.sha256 }}
        </p>
      </div>
      <p class="text-xs leading-6 text-text-secondary">
        {{
          tr(
            '更新包下载到面板数据目录。不会在游戏运行时自动覆盖程序。',
            'Update packages are stored in the panel data directory. Running server files are never overwritten automatically.',
            '更新パッケージはデータ領域に保存します。稼働中のファイルは自動上書きしません。',
          )
        }}
      </p>
    </section>
    <section class="space-y-5 border-t border-border pt-7">
      <p class="font-mono text-[10px] tracking-widest text-brand">/ TRANSPORT SECURITY</p>
      <h3 class="font-serif text-xl">{{ tr('HTTPS 加密访问', 'HTTPS ACCESS', 'HTTPS アクセス') }}</h3>
      <div class="grid gap-4 md:grid-cols-2">
        <label class="flex items-center justify-between border border-border p-4 text-sm"
          >{{ tr('开启 HTTPS', 'ENABLE HTTPS', 'HTTPS を有効化')
          }}<MechanicalSwitch v-model="settings.https_enabled" label="HTTPS" /></label
        ><label class="flex items-center justify-between border border-border p-4 text-sm"
          >{{ tr('自动生成自签证书', 'SELF-SIGNED CERTIFICATE', '自己署名証明書')
          }}<MechanicalSwitch v-model="settings.https_self_signed" label="SELF-SIGNED"
        /></label>
      </div>
      <ExpandTransition
        ><div v-if="settings.https_enabled" class="grid gap-5 md:grid-cols-2">
          <label class="space-y-2 text-xs"
            >{{ tr('HTTPS 入口端口', 'HTTPS PORT', 'HTTPS ポート')
            }}<input
              v-model.number="settings.https_port"
              type="number"
              min="1024"
              max="65535"
              class="block w-full border border-border bg-transparent p-3" /></label
          ><label class="space-y-2 text-xs"
            >{{ tr('本机前端端口', 'LOCAL FRONTEND PORT', 'ローカルフロントエンドポート')
            }}<input
              v-model.number="settings.frontend_port"
              type="number"
              min="1024"
              max="65535"
              class="block w-full border border-border bg-transparent p-3"
          /></label>
          <p class="text-xs leading-6 text-text-secondary md:col-span-2">
            {{
              tr(
                '保存后使用新入口访问；自签证书首次访问需要浏览器确认，公网域名请上传正式证书。',
                'After saving, use the HTTPS entry. Browsers require approval for self-signed certificates. Upload a trusted certificate for a public domain.',
                '保存後に HTTPS 入口へアクセス。自己署名証明書はブラウザの確認が必要です。公開ドメインでは正式な証明書をご利用ください。',
              )
            }}
            <a :href="httpsAddress" target="_blank" rel="noopener noreferrer" class="text-brand underline">{{
              httpsAddress
            }}</a>
          </p>
        </div></ExpandTransition
      ><ExpandTransition
        ><div v-if="!settings.https_self_signed" class="space-y-4">
          <p class="text-xs text-text-secondary">
            {{
              tr(
                '先关闭并保存 HTTPS，再上传 PEM 证书与私钥。',
                'Disable and save HTTPS before uploading PEM certificate and key.',
                'HTTPS を無効化して保存後、PEM 証明書と秘密鍵をアップロード。',
              )
            }}
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
            {{ tr('验证并保存证书', 'VALIDATE & SAVE CERTIFICATE', '証明書を検証・保存') }}
          </button>
        </div></ExpandTransition
      >
    </section>
    <p v-if="message" role="status" class="text-sm text-brand">{{ message }}</p>
  </div>
</template>
