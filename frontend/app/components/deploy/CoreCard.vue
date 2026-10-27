<script setup lang="ts">
defineProps<{ name: string; icon?: string; description: string; versions?: number }>()
defineEmits<{ select: [] }>()
</script>
<template>
  <button class="core-card-new" @click="$emit('select')">
    <span class="core-card-icon">{{ icon || '✦' }}</span>
    <span class="core-card-arrow">↗</span>
    <strong>{{ name }}</strong>
    <small>{{ description }}</small>
    <em>{{ versions || 0 }} VERSIONS</em>
  </button>
</template>
