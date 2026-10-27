<script setup lang="ts">
defineProps<{ error: { statusCode?: number; message?: string } }>()
</script>
<template>
  <main class="min-h-screen bg-background p-12 text-text-primary">
    <span class="font-mono text-xs text-text-secondary">/ ATMOSPHERE / RUNTIME</span>
    <h1 class="mt-8 font-serif text-6xl">{{ error?.statusCode || 500 }}</h1>
    <p class="mt-4 text-text-secondary">{{ error?.message || '页面暂时无法加载' }}</p>
    <button class="mt-8 border border-border px-4 py-2" @click="clearError({ redirect: '/' })">返回首页</button>
  </main>
</template>
