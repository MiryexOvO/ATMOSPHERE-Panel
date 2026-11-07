<script setup lang="ts">
const { t } = useI18n()
const props = defineProps<{ instanceId: string }>()
const { instanceRequest, path, getErrorMessage } = useInstanceApi(() => props.instanceId)
const names = ref<string[]>([]),
  selected = ref<string[]>([]),
  message = ref(''),
  busy = ref(false),
  action = ref('kick')
const actions = computed(() => [
  { value: 'op', label: t('msg_grant_op') },
  { value: 'deop', label: t('msg_revoke_op') },
  { value: 'kick', label: t('msg_kick') },
  { value: 'ban', label: t('msg_ban') },
  { value: 'pardon', label: t('msg_pardon') },
  { value: 'whitelist-add', label: t('msg_add_to_whitelist') },
  { value: 'whitelist-remove', label: t('msg_remove_from_whitelist') },
])
let timer: ReturnType<typeof setInterval> | undefined
async function load() {
  try {
    const data = await instanceRequest<{ players: string[] }>('/players')
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
      await instanceRequest('/players/action', {
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
        <p class="font-mono text-xs tracking-widest text-brand">/ ONLINE ROSTER</p>
        <h2 class="mt-3 font-serif text-2xl">
          {{ t('msg_online_players') }}
          <small class="ml-2 font-mono text-sm text-text-secondary">{{ names.length }}</small>
        </h2>
      </div>
      <button class="text-xs text-brand" @click="load">{{ t('msg_refresh') }}</button>
    </header>
    <p v-if="message" role="status" class="mt-5 text-sm whitespace-pre-wrap text-brand">{{ message }}</p>
    <div class="mt-7 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
      <label
        v-for="name in names"
        :key="name"
        class="flex cursor-pointer items-center gap-4 border border-border p-4 transition-colors hover:border-brand"
        ><input v-model="selected" type="checkbox" :value="name" class="accent-brand" /><img
          :src="path(`/players/avatar/${encodeURIComponent(name)}`)"
          width="48"
          height="48"
          :alt="name"
          class="pixel-avatar"
          loading="lazy"
        /><span class="font-mono text-sm">{{ name }}</span></label
      >
    </div>
    <p v-if="!names.length && !message" class="py-10 text-sm text-text-secondary">
      {{ t('msg_no_online_players') }}
    </p>
    <div class="mt-7 flex flex-wrap items-center gap-4 border-t border-border pt-6">
      <div class="w-64">
        <AtmosphereSelect v-model="action" :options="actions" :label="t('msg_player_action')" />
      </div>
      <button
        :disabled="busy || !selected.length"
        class="border border-brand px-5 py-3 text-sm text-brand disabled:opacity-30"
        @click="apply"
      >
        {{ t('msg_apply_to_selected') }} · {{ selected.length }}
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
