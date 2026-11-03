<script setup lang="ts">
const model = defineModel<boolean>({ required: true })
defineProps<{ label: string; disabled?: boolean }>()
</script>
<template>
  <button
    type="button"
    role="switch"
    :aria-label="label"
    :aria-checked="model"
    :disabled="disabled"
    class="mechanical-switch"
    :class="{ 'is-on': model }"
    @click="model = !model"
  >
    <span />
  </button>
</template>
<style scoped>
/* 方形拨片中央保留机械凹槽。 */
.mechanical-switch {
  position: relative;
  width: 48px;
  height: 26px;
  flex-shrink: 0;
  border: 1px solid var(--border);
  background: transparent;
  transition:
    border-color 0.3s,
    box-shadow 0.3s;
}
.mechanical-switch span {
  position: absolute;
  top: 3px;
  left: 3px;
  width: 18px;
  height: 18px;
  background: var(--text-secondary);
  transition:
    transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    background 0.3s;
}
.mechanical-switch span::after {
  content: '';
  position: absolute;
  left: 8px;
  top: 4px;
  width: 1px;
  height: 10px;
  background: var(--background);
  box-shadow: 1px 0 rgba(255, 255, 255, 0.25);
}
.mechanical-switch.is-on {
  border-color: #58cfa1;
  box-shadow: inset 0 0 12px #58cfa118;
}
.mechanical-switch.is-on span {
  transform: translateX(22px);
  background: #bbffdd;
  box-shadow: 0 0 9px #58cfa166;
}
.mechanical-switch:disabled {
  opacity: 0.4;
}
/* 按住时方块反色代替按钮下沉。 */
.mechanical-switch:active {
  transform: none;
}
.mechanical-switch:active span {
  background: #fff;
  transition:
    transform 0.35s cubic-bezier(0.4, 0, 0.2, 1),
    background 0.12s;
}
.mechanical-switch.is-on:active span {
  background: var(--text-secondary);
  box-shadow: none;
}
</style>
