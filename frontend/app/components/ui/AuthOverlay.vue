<script setup lang="ts">
defineProps<{ phase: 'idle' | 'authenticating' }>()
</script>
<template>
  <div v-if="phase !== 'idle'" class="auth-overlay" aria-live="polite" aria-label="Authenticating">
    <span class="auth-overlay__text">[ AUTHENTICATING... ]</span>
  </div>
</template>
<style scoped>
.auth-overlay { position: fixed; inset: 0; z-index: 10002; display: grid; place-items: center; pointer-events: none; background: #09090b; color: var(--text-primary); }
.auth-overlay__text { font: 12px/1 ui-monospace, SFMono-Regular, Menlo, monospace; letter-spacing: .28em; animation: auth-flash 250ms steps(1,end) infinite; }
@keyframes auth-flash { 0%,100% { opacity: 0; } 10%,30%,50%,70% { opacity: 1; } 20%,40%,60% { opacity: 0; } }
@media (prefers-reduced-motion: reduce) { .auth-overlay__text { animation: none; opacity: 1; } }
</style>
