<script setup lang="ts">
withDefaults(defineProps<{ interactive?: boolean }>(), { interactive: false })
</script>
<template>
  <div
    class="bg-surface/75 relative border-l border-t border-border p-6 shadow-2xl transition-all duration-300"
    :class="interactive ? 'hover:border-brand/60 hover:-translate-y-1 hover:bg-surface' : ''"
  >
    <div
      class="bg-background/40 pointer-events-none absolute inset-0 translate-x-2 translate-y-2 border border-border"
    />
    <div class="relative"><slot /></div>
  </div>
</template>
