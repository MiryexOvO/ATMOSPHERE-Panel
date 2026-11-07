<script setup lang="ts">
import AccountSecurity from './AccountSecurity.vue'
import LoginSecurity from './LoginSecurity.vue'
import HologramLight from '~/components/ui/HologramLight.vue'
import LocalScrollRuler from '~/components/ui/LocalScrollRuler.vue'
const auditViewport = ref<HTMLElement | null>(null)
const { t } = useI18n()
const tr = usePanelText()
const { request, getErrorMessage } = useApi()
type User = {
  id: number
  username: string
  nickname: string
  role: string
  enabled: boolean
  created_at: number
  last_login: number | null
  instance_ids: string[]
  permissions: string[]
}
const instances = ref<{ id: string; name: string }[]>([]),
  search = ref(''),
  page = ref(1)
const matched = computed(() =>
  users.value.filter((user) =>
    (user.username + ' ' + user.nickname).toLowerCase().includes(search.value.toLowerCase()),
  ),
)
const shown = computed(() => matched.value.slice((page.value - 1) * 20, page.value * 20))
watch(search, () => {
  page.value = 1
})
const permissionLabels = computed(() => ({
  view: tr('查看状态', 'VIEW', '状態閲覧'),
  console: tr('控制台日志', 'CONSOLE', 'ログ'),
  power: tr('电源控制', 'POWER', '電源'),
  command: tr('发送命令', 'COMMAND', 'コマンド'),
  files: tr('文件与扩展', 'FILES & ADDONS', 'ファイル'),
  backups: tr('备份', 'BACKUPS', 'バックアップ'),
  settings: tr('实例配置', 'SETTINGS', '設定'),
  players: tr('玩家管理', 'PLAYERS', 'プレイヤー'),
  schedule: tr('定时任务', 'SCHEDULES', '定期タスク'),
  delete: tr('删除实例', 'DELETE SERVER', 'サーバー削除'),
}))
const adminAccess = ref(false)
const users = ref<User[]>([]),
  currentId = ref(0),
  editing = ref<number | null>(null),
  open = ref(false),
  busy = ref(false),
  message = ref('')
const events = ref<{ id: number; username: string; action: string; detail: string; created_at: number }[]>([])
const form = reactive({
  username: '',
  nickname: '',
  password: '',
  role: 'operator',
  enabled: true,
  instance_ids: [] as string[],
  permissions: ['view', 'console'] as string[],
})
const roles = computed(() => [
  { value: 'admin', label: t('usersAdmin') },
  { value: 'operator', label: t('usersOperator') },
  { value: 'viewer', label: t('usersViewer') },
])
async function load() {
  try {
    const identity = await request<{ user: { role: string } }>('/api/me')
    adminAccess.value = identity.user.role === 'admin'
    if (!adminAccess.value) return
    const result = await request<{ users: User[]; current_id: number }>('/api/users')
    users.value = result.users
    currentId.value = result.current_id
    instances.value = (await request<{ instances: typeof instances.value }>('/api/instances')).instances
    events.value = (await request<{ events: typeof events.value }>('/api/audit')).events
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
function edit(user?: User) {
  editing.value = user?.id || null
  Object.assign(form, {
    username: user?.username || '',
    nickname: user?.nickname || '',
    password: '',
    role: user?.role || 'operator',
    enabled: user ? Boolean(user.enabled) : true,
    instance_ids: [...(user?.instance_ids || [])],
    permissions: [...(user?.permissions || ['view', 'console'])],
  })
  open.value = true
}
// 账户修改由管理员接口校验，并同步注销旧会话。
async function save() {
  busy.value = true
  try {
    await request('/api/users' + (editing.value ? '/' + editing.value : ''), {
      method: editing.value ? 'PUT' : 'POST',
      body: form,
    })
    open.value = false
    await load()
    message.value = t('fileDone')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
async function action(user: User, operation: 'delete' | 'sessions') {
  if (operation === 'delete' && !window.confirm(t('usersDelete') + ' ' + user.username)) return
  busy.value = true
  try {
    await request(`/api/users/${user.id}${operation === 'sessions' ? '/sessions' : ''}`, { method: 'DELETE' })
    await load()
    message.value = t('fileDone')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>
<template>
  <div class="space-y-6">
    <AccountSecurity />
    <LoginSecurity />
    <AtmosphereCard v-if="adminAccess" :interactive="false">
      <header class="flex items-start justify-between gap-4">
        <div>
          <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ USER DIRECTORY</p>
          <h2 class="mt-3 font-serif text-2xl">{{ t('usersTitle') }}</h2>
        </div>
        <button type="button" class="border border-brand px-4 py-2 text-xs text-brand" @click="edit()">
          {{ t('usersNew') }}
        </button>
      </header>
      <p class="mt-5 text-xs leading-6 text-text-secondary">
        {{
          tr(
            '管理员管理全站；操作员仅管理分配的实例及所选能力；只读账户不能执行写入操作。',
            'Administrators manage all resources. Operators receive assigned servers and capabilities. Viewers cannot modify resources.',
            '管理者は全体を管理。オペレーターは割り当てられたインスタンスと権限のみ。閲覧者は変更できません。',
          )
        }}
      </p>
      <p v-if="message" role="status" class="mt-4 text-sm text-brand">{{ message }}</p>
      <input
        v-model="search"
        :placeholder="tr('搜索用户名或昵称', 'SEARCH USERS', 'ユーザーを検索')"
        class="mt-6 w-full border border-border bg-transparent p-3 text-sm"
      />
      <div class="mt-6 overflow-x-auto">
        <table class="w-full text-left text-sm">
          <thead class="border-b border-border text-xs text-text-secondary">
            <tr>
              <th class="py-3">{{ t('usersName') }}</th>
              <th>{{ t('usersRole') }}</th>
              <th>{{ t('usersEnabled') }}</th>
              <th>{{ tr('最后登录', 'LAST LOGIN', '最終ログイン') }}</th>
              <th />
            </tr>
          </thead>
          <tbody>
            <tr v-for="user in shown" :key="user.id" class="border-b border-border/50">
              <td class="py-5 font-mono">
                <span class="mr-3 inline-flex h-9 w-9 items-center justify-center border border-border text-brand">{{
                  (user.nickname || user.username).slice(0, 1).toUpperCase()
                }}</span
                >{{ user.nickname || user.username }}
                <small class="ml-2 text-text-secondary">{{ user.username }}</small>
                <HologramLight
                  v-if="user.id === currentId"
                  :active="true"
                  class="ml-3 align-middle"
                  :title="tr('当前账户', 'CURRENT ACCOUNT', '現在のアカウント')"
                />
              </td>
              <td>{{ roles.find((role) => role.value === user.role)?.label }}</td>
              <td>{{ t(user.enabled ? 'settingsOn' : 'settingsOff') }}</td>
              <td class="text-xs text-text-secondary">
                {{ user.last_login ? new Date(user.last_login * 1000).toLocaleString() : '—' }}
              </td>
              <td class="py-3">
                <div class="flex flex-wrap justify-end gap-3 text-xs text-brand">
                  <button type="button" :disabled="busy" @click="edit(user)">{{ t('usersEdit') }}</button
                  ><button type="button" :disabled="busy" @click="action(user, 'sessions')">
                    {{ t('usersRevoke') }}</button
                  ><button
                    type="button"
                    :disabled="busy || user.id === currentId"
                    class="text-red-400 disabled:opacity-30"
                    @click="action(user, 'delete')"
                  >
                    {{ t('fileDelete') }}
                  </button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
      <div class="mt-5 flex justify-end gap-5 text-xs text-text-secondary">
        <span>{{ matched.length }} · {{ page }} / {{ Math.max(1, Math.ceil(matched.length / 20)) }}</span
        ><button :disabled="page === 1" @click="page--">PREV</button
        ><button :disabled="page * 20 >= matched.length" @click="page++">NEXT</button>
      </div>
    </AtmosphereCard>
    <AtmosphereCard v-if="adminAccess" :interactive="false"
      ><div>
        <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ EVENT LOG</p>
        <h3 class="mt-2 font-serif text-xl">{{ t('usersAudit') }}</h3>
      </div>
      <div class="relative mt-5">
        <div ref="auditViewport" class="max-h-80 overflow-y-auto pr-6">
          <div
            v-for="event in events"
            :key="event.id"
            class="grid gap-2 border-b border-border/50 py-3 text-xs sm:grid-cols-[150px_120px_1fr]"
          >
            <span class="text-text-secondary">{{ new Date(event.created_at * 1000).toLocaleString() }}</span
            ><span>{{ event.username || '—' }}</span
            ><span class="font-mono break-all text-brand">{{ event.action }} {{ event.detail }}</span>
          </div>
        </div>
        <LocalScrollRuler :target="auditViewport" /></div
    ></AtmosphereCard>
    <Teleport to="body"
      ><div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-5">
        <AtmosphereCard :interactive="false" class="max-h-[90vh] w-full max-w-2xl overflow-y-auto"
          ><form class="space-y-5" @submit.prevent="save">
            <div>
              <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ USER RECORD</p>
              <h3 class="mt-2 font-serif text-xl">{{ t(editing ? 'usersEdit' : 'usersNew') }}</h3>
            </div>
            <label class="block space-y-2"
              ><span class="text-xs text-text-secondary">{{ t('usersName') }}</span
              ><input
                v-model="form.username"
                required
                minlength="2"
                maxlength="32"
                pattern="[A-Za-z0-9_-]+"
                class="w-full border border-border bg-background p-3" /></label
            ><label class="block space-y-2"
              ><span class="text-xs text-text-secondary">{{ t('usersPassword') }}</span
              ><input
                v-model="form.password"
                type="password"
                :required="!editing"
                minlength="8"
                maxlength="72"
                autocomplete="new-password"
                class="w-full border border-border bg-background p-3" /></label
            ><label class="block space-y-2 text-xs"
              >{{ tr('昵称', 'DISPLAY NAME', '表示名')
              }}<input
                v-model="form.nickname"
                maxlength="60"
                class="w-full border border-border bg-transparent p-3" /></label
            ><AtmosphereSelect v-model="form.role" :label="t('usersRole')" :options="roles" /><label
              class="flex justify-between text-sm"
              >{{ t('usersEnabled') }}<input v-model="form.enabled" type="checkbox" class="accent-brand"
            /></label>
            <section v-if="form.role !== 'admin'" class="space-y-4 border-t border-border pt-4">
              <p class="text-xs text-text-secondary">
                {{
                  tr(
                    '分配实例与操作权限（未分配不可访问）',
                    'ASSIGNED SERVERS AND PERMISSIONS',
                    'インスタンスと操作権限',
                  )
                }}
              </p>
              <div class="flex flex-wrap gap-4">
                <label v-for="instance in instances" :key="instance.id" class="flex items-center gap-2 text-xs"
                  ><input v-model="form.instance_ids" type="checkbox" :value="instance.id" class="accent-brand" />{{
                    instance.name
                  }}</label
                >
              </div>
              <div class="grid grid-cols-2 gap-3">
                <label
                  v-for="(label, permission) in permissionLabels"
                  :key="permission"
                  class="flex items-center gap-2 text-xs"
                  ><input v-model="form.permissions" type="checkbox" :value="permission" class="accent-brand" />{{
                    label
                  }}</label
                >
              </div>
            </section>
            <p v-if="message" class="text-xs text-brand">{{ message }}</p>
            <div class="flex justify-end gap-4 text-sm">
              <button type="button" :disabled="busy" @click="open = false">{{ t('fileCancel') }}</button
              ><button type="submit" :disabled="busy" class="text-brand">{{ t('fileSave') }}</button>
            </div>
          </form></AtmosphereCard
        >
      </div></Teleport
    >
  </div>
</template>
