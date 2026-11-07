<script setup lang="ts">
const { t } = useI18n()
const { request } = useApi()
const alert = ref<{ id: number; ip: string; created_at: number } | null>(null)
// 已确认的提醒保存在当前浏览器，其他设备仍可查看。
function dismiss() {
  if (alert.value) localStorage.setItem('atmosphere-login-alert', String(alert.value.id))
  alert.value = null
}
onMounted(async () => {
  try {
    const data = await request<{ events: { id: number; ip: string; unusual: boolean; created_at: number }[] }>(
      '/api/account/security',
    )
    const seen = Number(localStorage.getItem('atmosphere-login-alert') || 0)
    alert.value = data.events.find((event) => event.unusual && event.id > seen) || null
  } catch {}
})
</script>
<template>
  <AtmosphereCard v-if="alert" :interactive="false" class="mb-6"
    ><div class="flex items-center justify-between gap-4">
      <p class="text-sm text-amber-300">
        {{ t('msg_new_network_sign_in_detected_verify_this_act') }}
        {{ alert.ip }} · {{ new Date(alert.created_at * 1000).toLocaleString() }}
      </p>
      <button class="shrink-0 text-xs text-brand" @click="dismiss">{{ t('msg_dismiss') }}</button>
    </div></AtmosphereCard
  >
</template>
