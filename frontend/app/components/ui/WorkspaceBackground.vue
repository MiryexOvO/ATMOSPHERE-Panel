<script setup lang="ts">
import LineField from './LineField.vue'
</script>
<template>
  <!-- 与仪表盘共用线场，仅保留低对比路径。 -->
  <div class="workspace-background pointer-events-none fixed inset-0 z-0 overflow-hidden" aria-hidden="true">
    <LineField />
    <svg
      viewBox="0 0 1440 900"
      preserveAspectRatio="none"
      class="workspace-paths absolute inset-0 h-full w-full"
      fill="none"
      stroke="currentColor"
      stroke-width=".45"
    >
      <path d="M-80 650L260 420L520 540L860 280L1520 410" />
      <path d="M-80 220L340 340L760 110L1170 260L1520 90" />
      <path d="M140 980L450 660L890 760L1340 480" />
    </svg>
  </div>
</template>
<style scoped>
.workspace-background {
  color: var(--brand);
  opacity: 0.5;
}
.workspace-paths {
  opacity: 0.12;
  animation: workspace-drift 28s ease-in-out infinite alternate;
}
@keyframes workspace-drift {
  from {
    transform: translateY(-10px);
  }
  to {
    transform: translateY(12px);
  }
}
@media (prefers-reduced-motion: reduce) {
  .workspace-paths {
    animation: none;
  }
}
</style>
