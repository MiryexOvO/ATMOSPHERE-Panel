<script setup lang="ts">
import MechanicalSwitch from '~/components/ui/MechanicalSwitch.vue'
const { t } = useI18n()
const { request, getErrorMessage } = useApi()
type Task = {
  id: number
  name: string
  instance_id: string
  cron: string
  action: string
  command: string
  enabled: boolean
  next_run: number
  last_run: number | null
  last_result: string
}
type Instance = { id: string; name: string }
const tasks = ref<Task[]>([]),
  instances = ref<Instance[]>([]),
  editing = ref<number | null>(null),
  open = ref(false),
  busy = ref(false),
  message = ref('')
const form = reactive({ name: '', instance_id: '', cron: '0 4 * * *', action: 'restart', command: '', enabled: true })
const actions = computed(() => [
  { value: 'command', label: t('msg_send_command') },
  { value: 'restart', label: t('msg_restart_server') },
  { value: 'start', label: t('msg_start_server') },
  { value: 'stop', label: t('msg_stop_server') },
  { value: 'backup', label: t('msg_offline_backup') },
])
async function load() {
  try {
    const data = await request<{ tasks: Task[] }>('/api/schedules')
    tasks.value = data.tasks
    instances.value = (await request<{ instances: Instance[] }>('/api/instances')).instances
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
function edit(task?: Task) {
  editing.value = task?.id || null
  Object.assign(form, {
    name: task?.name || '',
    instance_id: task?.instance_id || instances.value[0]?.id || '',
    cron: task?.cron || '0 4 * * *',
    action: task?.action || 'restart',
    command: task?.command || '',
    enabled: task ? Boolean(task.enabled) : true,
  })
  message.value = ''
  open.value = true
}
// Cron 与执行动作持久化到后端，由统一调度器执行。
async function save() {
  busy.value = true
  try {
    await request('/api/schedules' + (editing.value ? '/' + editing.value : ''), {
      method: editing.value ? 'PUT' : 'POST',
      body: form,
    })
    open.value = false
    await load()
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
async function remove(task: Task) {
  if (!window.confirm(t('msg_delete_this_task'))) return
  try {
    await request('/api/schedules/' + task.id, { method: 'DELETE' })
    await load()
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
async function toggle(task: Task) {
  try {
    await request('/api/schedules/' + task.id, { method: 'PUT', body: { ...task, enabled: !task.enabled } })
    await load()
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
// 手动执行便于验证任务，仍由后端校验权限。
async function run(task: Task) {
  if (busy.value || !window.confirm(t('msg_run_this_task_now'))) return
  busy.value = true
  try {
    const result = await request<{ result: string }>('/api/schedules/' + task.id + '/run', {
      method: 'POST',
      timeout: 600000,
    })
    message.value = result.result
    await load()
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
    <AtmosphereCard :interactive="false"
      ><header class="flex justify-between gap-4">
        <div>
          <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ CRON AUTOMATION</p>
          <h2 class="mt-3 font-serif text-2xl">{{ t('msg_global_schedules') }}</h2>
          <p class="mt-3 text-xs text-text-secondary">
            {{ t('msg_five_or_six_field_cron_utc_missed_executions') }}
          </p>
        </div>
        <button class="shrink-0 self-start border border-brand px-4 py-3 text-xs text-brand" @click="edit()">
          {{ t('msg_new_task') }}
        </button>
      </header>
      <p v-if="message" role="status" class="mt-5 text-sm text-brand">{{ message }}</p></AtmosphereCard
    ><AtmosphereCard v-for="instance in instances" :key="instance.id" :interactive="false"
      ><header class="flex items-center justify-between border-b border-border pb-4">
        <h3 class="font-serif text-xl">{{ instance.name }}</h3>
        <span class="font-mono text-xs text-text-secondary"
          >{{ instance.id }} · {{ tasks.filter((task) => task.instance_id === instance.id).length }}</span
        >
      </header>
      <div
        v-for="task in tasks.filter((task) => task.instance_id === instance.id)"
        :key="task.id"
        class="grid items-center gap-4 border-b border-border py-5 md:grid-cols-[1fr_1fr_auto]"
      >
        <div>
          <h4 class="text-sm">{{ task.name }}</h4>
          <p class="mt-2 font-mono text-xs text-brand">{{ task.cron }} · {{ task.action.toUpperCase() }}</p>
          <p v-if="task.command" class="mt-2 font-mono text-xs break-all text-text-secondary">{{ task.command }}</p>
        </div>
        <div class="text-xs leading-6 text-text-secondary">
          <p>{{ t('msg_next_run') }}: {{ new Date(task.next_run * 1000).toLocaleString() }}</p>
          <p v-if="task.last_run">{{ new Date(task.last_run * 1000).toLocaleString() }} · {{ task.last_result }}</p>
        </div>
        <div class="flex items-center gap-4 text-xs text-brand">
          <MechanicalSwitch
            :model-value="Boolean(task.enabled)"
            :label="task.name"
            @update:model-value="toggle(task)"
          /><button :disabled="busy" @click="run(task)">{{ t('msg_run_now') }}</button
          ><button @click="edit(task)">{{ t('msg_edit') }}</button
          ><button class="text-red-400" @click="remove(task)">{{ t('msg_delete') }}</button>
        </div>
      </div>
      <p
        v-if="!tasks.some((task) => task.instance_id === instance.id)"
        class="py-8 text-center text-xs text-text-secondary"
      >
        {{ t('msg_no_scheduled_tasks') }}
      </p></AtmosphereCard
    ><Teleport to="body"
      ><div v-if="open" class="fixed inset-0 z-50 flex items-center justify-center overflow-y-auto bg-black/70 p-5">
        <AtmosphereCard :interactive="false" class="max-h-[90vh] w-full max-w-xl overflow-y-auto"
          ><form class="space-y-5" @submit.prevent="save">
            <h3 class="font-serif text-2xl">{{ t('msg_scheduled_task') }}</h3>
            <label class="block space-y-2 text-xs"
              >{{ t('msg_instance')
              }}<AtmosphereSelect
                v-model="form.instance_id"
                :options="instances.map((instance) => ({ value: instance.id, label: instance.name }))"
                label="INSTANCE" /></label
            ><label class="block space-y-2 text-xs"
              >{{ t('msg_task_name')
              }}<input
                v-model="form.name"
                required
                maxlength="100"
                class="w-full border border-border bg-transparent p-3" /></label
            ><label class="block space-y-2 text-xs"
              >CRON · UTC<input
                v-model="form.cron"
                required
                class="w-full border border-border bg-transparent p-3 font-mono"
            /></label>
            <div class="flex flex-wrap gap-3 text-[10px] text-brand">
              <button type="button" @click="form.cron = '*/30 * * * *'">
                {{ t('msg_every_30_min') }}</button
              ><button type="button" @click="form.cron = '0 4 * * *'">
                {{ t('msg_daily_04_00_utc') }}
              </button>
            </div>
            <AtmosphereSelect v-model="form.action" :options="actions" label="ACTION" /><label
              v-if="form.action === 'command'"
              class="block space-y-2 text-xs"
              >{{ t('msg_console_command')
              }}<input
                v-model="form.command"
                required
                maxlength="512"
                class="w-full border border-border bg-transparent p-3 font-mono"
            /></label>
            <div class="flex items-center justify-between text-sm">
              {{ t('msg_enable_task') }}<MechanicalSwitch v-model="form.enabled" label="ENABLE TASK" />
            </div>
            <p v-if="message" role="status" class="text-sm text-brand">{{ message }}</p>
            <div class="flex justify-end gap-5 text-sm">
              <button type="button" :disabled="busy" @click="open = false">
                {{ t('msg_cancel') }}</button
              ><button :disabled="busy" class="text-brand">{{ t('msg_save_task') }}</button>
            </div>
          </form></AtmosphereCard
        >
      </div></Teleport
    >
  </div>
</template>
