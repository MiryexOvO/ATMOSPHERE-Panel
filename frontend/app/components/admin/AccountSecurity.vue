<script setup lang="ts">
const {t}=useI18n(),{request,getErrorMessage}=useApi()
const form=reactive({current_password:'',new_password:'',confirmation:''})
const busy=ref(false),message=ref('')
// 仅更改当前账户密码，提交后清除输入。
async function save(){
 if(form.new_password!==form.confirmation){message.value=t('passwordMismatch');return}
 busy.value=true
 try{await request('/api/account/password',{method:'POST',body:form});Object.assign(form,{current_password:'',new_password:'',confirmation:''});message.value=t('panelSaved')}
 catch(error){message.value=getErrorMessage(error)}finally{busy.value=false}
}
</script>
<template>
  <AtmosphereCard :interactive="false"><form class="space-y-5" @submit.prevent="save"><h2 class="font-serif text-2xl">{{t('accountSecurity')}}</h2><div class="grid gap-4 md:grid-cols-3"><label v-for="field in [{key:'current_password',label:'passwordCurrent'},{key:'new_password',label:'passwordNew'},{key:'confirmation',label:'passwordConfirm'}] as const" :key="field.key" class="space-y-2"><span class="block text-xs text-text-secondary">{{t(field.label)}}</span><input v-model="form[field.key]" type="password" required :minlength="field.key==='current_password'?1:8" maxlength="72" :autocomplete="field.key==='current_password'?'current-password':'new-password'" class="w-full border border-border bg-background p-3"/></label></div><div class="flex flex-wrap items-center justify-between gap-4"><p role="status" class="text-sm text-brand">{{message}}</p><button type="submit" :disabled="busy" class="border border-brand px-4 py-2 text-xs text-brand disabled:opacity-40">{{t('fileSave')}}</button></div></form></AtmosphereCard>
</template>
