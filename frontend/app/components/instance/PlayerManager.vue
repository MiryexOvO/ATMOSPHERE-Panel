<script setup lang="ts">
const props = defineProps<{ instanceId: string }>()
const tr = usePanelText(),
  { request, getErrorMessage } = useApi()
const names = ref<string[]>([]),
  selected = ref<string[]>([]),
  message = ref(''),
  busy = ref(false),
  action = ref('kick')
const actions = computed(() => [
  { value: 'op', label: tr('授予 OP', 'GRANT OP', 'OP を付与') },
  { value: 'deop', label: tr('取消 OP', 'REVOKE OP', 'OP を解除') },
  { value: 'kick', label: tr('踢出', 'KICK', 'キック') },
  { value: 'ban', label: tr('封禁', 'BAN', 'BAN') },
  { value: 'pardon', label: tr('解封', 'PARDON', 'BAN 解除') },
  { value: 'whitelist-add', label: tr('加入白名单', 'ADD TO WHITELIST', 'ホワイトリスト追加') },
  { value: 'whitelist-remove', label: tr('移出白名单', 'REMOVE FROM WHITELIST', 'ホワイトリスト削除') },
])
let timer: ReturnType<typeof setInterval> | undefined
async function load() {
  try {
    const data = await request<{ players: string[] }>(`/api/instances/${encodeURIComponent(props.instanceId)}/players`)
    names.value = data.players
    selected.value = selected.value.filter((name) => names.value.includes(name))
    message.value = ''
  } catch (error) {
    names.value = []
    message.value = getErrorMessage(error)
  }
}
// 危险操作确认后逐人执行并反馈结果。
async function apply() {
  if (!selected.value.length || busy.value) return
  if (!window.confirm(actions.value.find((a) => a.value === action.value)?.label + ' · ' + selected.value.join(', ')))
    return
  busy.value = true
  const results: string[] = []
  for (const name of selected.value) {
    try {
      await request(`/api/instances/${encodeURIComponent(props.instanceId)}/players/action`, {
        method: 'POST',
        body: { name, action: action.value },
      })
      results.push(name + ' OK')
    } catch (error) {
      results.push(name + ': ' + getErrorMessage(error))
    }
  }
  message.value = results.join(' / ')
  busy.value = false
}
onMounted(() => {
  load()
  timer = setInterval(load, 10000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
<template>
  <AtmosphereCard :interactive="false"
    ><header class="flex justify-between">
      <div>
        <p class="font-mono text-xs tracking-widest text-brand">/ PLAYER OPERATIONS</p>
        <h2 class="mt-3 font-serif text-2xl">
          {{ tr('在线玩家', 'ONLINE PLAYERS', 'オンラインプレイヤー') }}
          <small class="ml-2 font-mono text-sm text-text-secondary">{{ names.length }}</small>
        </h2>
      </div>
      <button class="text-xs text-brand" @click="load">{{ tr('刷新', 'REFRESH', '更新') }}</button>
    </header>
    <p v-if="message" role="status" class="mt-5 text-sm whitespace-pre-wrap text-brand">{{ message }}</p>
    <div class="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <label
        v-for="name in names"
        :key="name"
        class="flex cursor-pointer items-center gap-4 border border-border p-4 transition-colors hover:border-brand"
        ><input v-model="selected" type="checkbox" :value="name" class="accent-brand" /><img
          :src="`/api/instances/${encodeURIComponent(instanceId)}/players/avatar/${encodeURIComponent(name)}`"
          width="48"
          height="48"
          :alt="name"
          class="pixel-avatar"
          loading="lazy"
        /><span class="font-mono text-sm">{{ name }}</span></label
      >
    </div>
    <p v-if="!names.length && !message" class="py-10 text-sm text-text-secondary">
      {{ tr('目前没有在线玩家', 'NO ONLINE PLAYERS', 'オンラインプレイヤーはいません') }}
    </p>
    <div class="mt-7 flex flex-wrap items-center gap-4 border-t border-border pt-6">
      <div class="w-64">
        <AtmosphereSelect
          v-model="action"
          :options="actions"
          :label="tr('玩家操作', 'PLAYER ACTION', 'プレイヤー操作')"
        />
      </div>
      <button
        :disabled="busy || !selected.length"
        class="border border-brand px-5 py-3 text-sm text-brand disabled:opacity-30"
        @click="apply"
      >
        {{ tr('执行选中操作', 'APPLY TO SELECTED', '選択した操作を実行') }} · {{ selected.length }}
      </button>
    </div></AtmosphereCard
  >
</template>
<style scoped>
.pixel-avatar {
  image-rendering: pixelated;
  background: var(--border);
}
</style>
