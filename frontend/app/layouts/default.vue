<script setup lang="ts">
import { ref, onMounted } from 'vue'
import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'
const now = ref(new Date()), menu = ref(false), colorMode = useColorMode()
onMounted(() => setInterval(() => now.value = new Date(), 1000))
function toggleTheme(){colorMode.preference=colorMode.value==='dark'?'light':'dark'}
async function logout(){await $fetch('/api/logout',{method:'POST',credentials:'include'});await navigateTo('/')}
</script>
<template>
  <div class="relative min-h-screen overflow-hidden bg-background text-text-main"><StarfieldBackground/><header class="relative z-10 flex h-20 items-center justify-between border-b border-white/10 px-8"><div class="flex items-center gap-5"><span class="text-brand">✦</span><strong class="font-mono tracking-[.18em]">ATMOSPHERE</strong><small class="font-mono text-xs text-text-secondary tracking-[.18em]">MC SERVER OPERATIONS / 02</small></div><div class="flex items-center gap-4 font-mono text-xs text-text-secondary"><button class="border border-white/10 px-3 py-2 hover:border-brand hover:text-brand">◒ PALETTE</button><span>CPU 12% · RAM 4.2G</span><span class="text-data-live">● SIGNAL / OK</span><span>{{now.toLocaleTimeString('en-GB')}}</span><button class="avatar" @click="menu=!menu">A</button><div v-if="menu" class="user-menu"><button @click="toggleTheme">主题切换</button><button @click="logout">登出</button></div></div></header><slot/></div>
</template>
