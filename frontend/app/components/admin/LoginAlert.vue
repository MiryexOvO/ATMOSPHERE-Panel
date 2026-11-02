<script setup lang="ts">
const tr=usePanelText(),{request}=useApi()
const alert=ref<{id:number;ip:string;created_at:number}|null>(null)
// 已确认的提醒保存在当前浏览器，其他设备仍可查看。
function dismiss(){if(alert.value)localStorage.setItem('atmosphere-login-alert',String(alert.value.id));alert.value=null}
onMounted(async()=>{try{const data=await request<{events:{id:number;ip:string;unusual:boolean;created_at:number}[]}>('/api/account/security');const seen=Number(localStorage.getItem('atmosphere-login-alert')||0);alert.value=data.events.find(event=>event.unusual&&event.id>seen)||null}catch{}})
</script>
<template><AtmosphereCard v-if="alert" :interactive="false" class="mb-6"><div class="flex items-center justify-between gap-4"><p class="text-sm text-amber-300">{{tr('检测到新网络登录，请检查是否为本人操作：','New-network sign-in detected. Verify this activity:','新しいネットワークからのログインを確認してください：')}} {{alert.ip}} · {{new Date(alert.created_at*1000).toLocaleString()}}</p><button class="shrink-0 text-xs text-brand" @click="dismiss">{{tr('已知晓','DISMISS','確認済み')}}</button></div></AtmosphereCard></template>
