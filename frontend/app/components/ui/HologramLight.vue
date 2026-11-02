<script setup lang="ts">
defineProps<{ active: boolean }>()
const lamp = ref<HTMLElement | null>(null)

// 对齐页面时间轴，新开启的灯也保持同相呼吸。
function synchronize() {
  for (const animation of lamp.value?.getAnimations() || []) animation.startTime = 0
}
onMounted(synchronize)
onUpdated(synchronize)
</script>

<template>
  <span ref="lamp" aria-hidden="true" class="hologram-lamp" :class="{ 'is-active': active }" />
</template>

<style scoped>
.hologram-lamp { display: inline-block; width: 8px; height: 8px; flex-shrink: 0; border-radius: 50%; background: #66746f; opacity: 0.55; }
/* 中心亮点叠加双层绿光。 */
.hologram-lamp.is-active { background: #bdffe0; opacity: 1; box-shadow: 0 0 3px #bcffe0, 0 0 9px #43ffa1, 0 0 18px #24f69680; animation: hologram-breathe 3s ease-in-out infinite; }
@keyframes hologram-breathe {
  0%, 100% { opacity: 0.65; box-shadow: 0 0 2px #bcffe0, 0 0 5px #43ffa1a0, 0 0 11px #24f69640; }
  50% { opacity: 1; box-shadow: 0 0 4px #e2fff1, 0 0 11px #43ffa1, 0 0 22px #24f69690; }
}
@media (prefers-reduced-motion: reduce) { .hologram-lamp.is-active { animation: none; } }
</style>
