<script setup lang="ts">
const tr = usePanelText(),
  { request, getErrorMessage } = useApi()
const instances = ref<{ id: string; name: string }[]>([]),
  selected = ref<string[]>([]),
  action = ref('restart'),
  command = ref(''),
  busy = ref(false),
  message = ref('')
async function load() {
  try {
    instances.value = (await request<{ instances: typeof instances.value }>('/api/instances')).instances
  } catch (error) {
    message.value = getErrorMessage(error)
  }
}
// 限制并发并返回每台实例的真实结果。
async function run() {
  if (!selected.value.length || busy.value) return
  if (
    action.value !== 'command' &&
    !window.confirm(tr('确认操作选中的实例？', 'Apply to selected servers?', '選択したサーバーに実行しますか？'))
  )
    return
  busy.value = true
  try {
    const data = await request<{ results: { id: string; ok: boolean; result: string }[] }>('/api/batch', {
      method: 'POST',
      body: { instance_ids: selected.value, action: action.value, command: command.value },
      timeout: 600000,
    })
    message.value = data.results
      .map((result) => result.id + ' · ' + (result.ok ? 'OK' : 'ERROR') + ' ' + result.result)
      .join('\n')
  } catch (error) {
    message.value = getErrorMessage(error)
  } finally {
    busy.value = false
  }
}
onMounted(load)
</script>
<template>
  <AtmosphereCard :interactive="false" class="w-full max-w-3xl" data-batch-operations
    ><div class="space-y-5">
      <div>
        <p class="font-mono text-[10px] tracking-widest text-brand">/ FLEET COMMANDS</p>
        <h3 class="mt-3 font-serif text-xl">
          {{ tr('多实例批量操作', 'MULTI-SERVER OPERATIONS', '複数サーバー操作') }}
        </h3>
      </div>
      <div class="flex flex-wrap gap-5">
        <label v-for="instance in instances" :key="instance.id" class="flex items-center gap-2 text-xs"
          ><input v-model="selected" type="checkbox" :value="instance.id" class="accent-brand" />{{
            instance.name
          }}</label
        >
      </div>
      <div class="grid items-start gap-3 sm:grid-cols-[minmax(180px,240px)_1fr_auto]">
        <div class="min-w-0">
          <AtmosphereSelect
            v-model="action"
            label="ACTION"
            :options="[
              { value: 'restart', label: tr('一键重启', 'RESTART SELECTED', '一括再起動') },
              { value: 'command', label: tr('同步命令', 'BROADCAST COMMAND', 'コマンド同期') },
              { value: 'start', label: tr('批量启动', 'START SELECTED', '一括起動') },
              { value: 'stop', label: tr('批量停止', 'STOP SELECTED', '一括停止') },
            ]"
          />
        </div>
        <input
          v-if="action === 'command'"
          v-model="command"
          maxlength="512"
          :placeholder="tr('单行服务器命令', 'SINGLE SERVER COMMAND', 'サーバーコマンド')"
          class="min-w-0 flex-1 border border-border bg-transparent p-3 font-mono text-sm"
        /><button
          :disabled="busy || !selected.length || (action === 'command' && !command.trim())"
          class="min-h-[46px] border border-brand px-5 text-xs text-brand disabled:opacity-40"
          :class="action === 'command' ? '' : 'sm:col-start-2 sm:justify-self-start'"
          @click="run"
        >
          {{ busy ? tr('执行中…', 'RUNNING…', '実行中…') : tr('执行', 'EXECUTE', '実行') }}
        </button>
      </div>
      <p v-if="message" role="status" class="font-mono text-xs leading-6 whitespace-pre-wrap text-brand">
        {{ message }}
      </p>
    </div></AtmosphereCard
  >
</template>
