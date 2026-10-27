<script setup lang="ts">
definePageMeta({ middleware: 'auth' })

import { onMounted, ref } from 'vue'
import DeployLayout from '~/components/deploy/DeployLayout.vue'

const activeTab = ref<'overview' | 'deploy'>('overview')
const instances = ref<any[]>([])

onMounted(async () => {
  try {
    const result: any = await $fetch('/api/instances', { credentials: 'include' })
    instances.value = result.instances || []
  } catch {
    instances.value = []
  }
})
</script>

<template>
  <main class="relative z-10 mx-auto max-w-7xl px-8 py-14">
    <header class="flex items-end justify-between border-b border-white/10 pb-8">
      <div>
        <span class="font-mono text-xs tracking-[.2em] text-text-secondary">/ CONTROL ROOM / AUTHORIZED</span>
        <h1 class="mt-6 font-serif text-6xl font-light tracking-tight text-text-primary md:text-8xl">
          Server <em class="font-sans text-brand">instances.</em>
        </h1>
      </div>
      <button class="border border-brand px-4 py-2 font-mono text-sm text-text-primary transition hover:bg-brand hover:text-primary-foreground" @click="navigateTo('/deploy')">
        [ + NEW INSTANCE ]
      </button>
    </header>

    <nav class="mt-8 flex gap-8 font-mono text-sm">
      <button :class="activeTab === 'overview' ? 'border-b-2 border-brand pb-3 text-text-primary' : 'border-b-2 border-transparent pb-3 text-text-secondary hover:text-text-primary'" @click="activeTab = 'overview'">
        ◈ 实例概览
      </button>
      <button :class="activeTab === 'deploy' ? 'border-b-2 border-brand pb-3 text-text-primary' : 'border-b-2 border-transparent pb-3 text-text-secondary hover:text-text-primary'" @click="activeTab = 'deploy'">
        ✦ 部署中心
      </button>
    </nav>

    <section v-if="activeTab === 'deploy'" class="mt-8">
      <DeployLayout />
    </section>

    <section v-else class="mt-10">
      <div class="grid grid-cols-3 border-y border-white/10 font-mono">
        <div class="p-7">
          <span class="text-xs text-text-secondary">ACTIVE INSTANCES</span>
          <strong class="mt-5 block text-3xl text-text-primary">{{ String(instances.length).padStart(2, '0') }}</strong>
          <small class="text-text-secondary">已登记的 Minecraft 实例</small>
        </div>
        <div class="border-x border-white/10 p-7">
          <span class="text-xs text-text-secondary">DEPLOYMENT MODE</span>
          <strong class="mt-5 block text-3xl text-text-primary">JAR</strong>
          <small class="text-text-secondary">安全上传与独立目录</small>
        </div>
        <div class="p-7">
          <span class="text-xs text-text-secondary">SESSION</span>
          <strong class="mt-5 block text-3xl text-text-primary">24</strong>
          <small class="text-text-secondary">管理员会话已建立</small>
        </div>
      </div>

      <div v-if="!instances.length" class="py-32 text-center">
        <span class="font-mono text-xs tracking-[.3em] text-brand">[ 00 / 00 ]</span>
        <h2 class="mt-6 font-mono text-lg tracking-[.35em] text-text-primary">NO SERVER INSTANCES</h2>
        <p class="mt-4 text-xs text-text-secondary">创建第一个实例，上传服务端核心并确认 EULA。</p>
      </div>

      <div v-else class="mt-8 divide-y divide-white/10">
        <NuxtLink v-for="(item, index) in instances" :key="item.id" :to="`/instances/${item.id}`" class="flex items-center justify-between py-7 transition hover:text-brand">
          <div class="flex items-center gap-8">
            <span class="font-mono text-xs text-brand">&gt; {{ String(index + 1).padStart(2, '0') }}</span>
            <div>
              <h2 class="font-mono text-lg font-bold text-text-primary">{{ item.name }}</h2>
              <small class="font-mono text-xs text-text-secondary">PORT {{ item.port }} · STATUS {{ item.status }}</small>
            </div>
          </div>
          <span class="font-mono text-xs">[ DETAILS + ]</span>
        </NuxtLink>
      </div>
    </section>
  </main>
</template>
