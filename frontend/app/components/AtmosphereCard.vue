<script setup lang="ts">
withDefaults(defineProps<{ interactive?: boolean }>(), { interactive: false })
</script>
<template>
  <div class="relative border-l border-t border-border bg-surface/75 p-6 shadow-2xl transition-all duration-300" :class="interactive ? 'hover:-translate-y-1 hover:border-brand/60 hover:bg-surface' : ''">
    <div class="pointer-events-none absolute inset-0 translate-x-2 translate-y-2 border border-border bg-background/40" />
    <div class="relative"><slot /></div>
  </div>
</template>