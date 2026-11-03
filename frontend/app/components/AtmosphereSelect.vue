<script setup lang="ts">
const props = defineProps<{ modelValue: string; options: { value: string; label: string }[]; label: string }>()
const emit = defineEmits<{ 'update:modelValue': [value: string] }>()
const open = ref(false)
const root = ref<HTMLElement | null>(null)
const trigger = ref<HTMLButtonElement | null>(null)
const menu = ref<HTMLElement | null>(null)
const menuStyle = ref<Record<string, string>>({})
const menuId = useId()
const current = computed(() => props.options.find((item) => item.value === props.modelValue)?.label || props.modelValue)

// 统一下载源与设置菜单的选择行为。
function choose(value: string) {
  if (trigger.value?.matches(':disabled')) return
  emit('update:modelValue', value)
  open.value = false
  trigger.value?.focus({ preventScroll: true })
}
function outside(event: PointerEvent) {
  if (!root.value?.contains(event.target as Node) && !menu.value?.contains(event.target as Node)) open.value = false
}
// 关闭菜单并把焦点交还触发器，避免多语句内联处理器被格式化拆行后无法编译。
function dismiss() {
  open.value = false
  trigger.value?.focus()
}
async function move(direction: number) {
  open.value = true
  await nextTick()
  const items = Array.from(menu.value?.querySelectorAll<HTMLButtonElement>('[role="option"]') || [])
  const index = items.indexOf(document.activeElement as HTMLButtonElement)
  items[(index + direction + items.length) % items.length]?.focus()
}
// 菜单挂到页面顶层，绕过卡片层叠与高度裁剪。
function position() {
  if (!open.value || !trigger.value) return
  const box = trigger.value.getBoundingClientRect()
  if (box.bottom < 0 || box.top > innerHeight || trigger.value.matches(':disabled')) {
    open.value = false
    return
  }
  const below = innerHeight - box.bottom - 12,
    above = box.top - 12
  const height = Math.max(48, Math.min(256, Math.max(below, above)))
  const actual = Math.min(height, props.options.length * 36 + 10)
  const width = Math.min(box.width, innerWidth - 16)
  menuStyle.value = {
    position: 'fixed',
    left: Math.max(8, Math.min(box.left, innerWidth - width - 8)) + 'px',
    top: (below >= actual ? box.bottom + 4 : Math.max(8, box.top - actual - 4)) + 'px',
    width: width + 'px',
    maxHeight: height + 'px',
  }
}
watch(open, async (value) => {
  if (value) {
    position()
    await nextTick()
    position()
  }
})
onMounted(() => {
  document.addEventListener('pointerdown', outside)
  window.addEventListener('resize', position)
  window.addEventListener('scroll', position, true)
})
onUnmounted(() => {
  document.removeEventListener('pointerdown', outside)
  window.removeEventListener('resize', position)
  window.removeEventListener('scroll', position, true)
})
</script>

<template>
  <div
    ref="root"
    class="relative"
    @keydown.esc.stop.prevent="dismiss"
    @keydown.down.stop.prevent="move(1)"
    @keydown.up.stop.prevent="move(-1)"
  >
    <button
      ref="trigger"
      type="button"
      :aria-label="label"
      aria-haspopup="listbox"
      :aria-expanded="open"
      :aria-controls="menuId"
      class="select-trigger flex w-full items-center justify-between border border-border bg-background/50 px-4 py-3 text-left font-mono text-sm text-text-primary outline-none hover:border-brand focus:border-brand"
      @click="open = !open"
    >
      {{ current }} <span class="select-caret text-text-secondary" aria-hidden="true">▾</span>
    </button>
    <Teleport to="body"
      ><Transition name="select-menu">
        <div
          v-if="open"
          ref="menu"
          :id="menuId"
          role="listbox"
          :aria-label="label"
          class="z-[3000] overflow-y-auto border border-border p-1 shadow-2xl"
          :style="{ ...menuStyle, background: 'var(--surface)' }"
          @keydown.esc.stop.prevent="dismiss"
          @keydown.down.stop.prevent="move(1)"
          @keydown.up.stop.prevent="move(-1)"
        >
          <button
            v-for="option in options"
            :key="option.value"
            type="button"
            role="option"
            :aria-selected="modelValue === option.value"
            class="select-option block w-full px-3 py-2 text-left font-mono text-sm outline-none focus:bg-background focus:text-text-primary"
            :class="
              modelValue === option.value
                ? 'text-brand'
                : 'text-text-secondary hover:bg-background hover:text-text-primary'
            "
            @click="choose(option.value)"
          >
            {{ option.label }}
          </button>
        </div>
      </Transition></Teleport
    >
  </div>
</template>

<style scoped>
/* 下拉菜单不跟随按下位移，按下时反色填充，避免展开和选项点击时抖动。 */
.select-trigger:active {
  transform: none;
  border-color: var(--brand);
  background: var(--brand);
  color: var(--background);
  transition:
    background-color 120ms ease,
    border-color 120ms ease,
    color 120ms ease;
}
.select-trigger:active .select-caret {
  color: var(--background);
}
.select-caret {
  transition: color 120ms ease;
}
.select-option:active {
  transform: none;
  background: var(--brand);
  color: var(--background);
  transition:
    background-color 120ms ease,
    color 120ms ease;
}
/* 沿用下载源菜单的浮入动效。 */
.select-menu-enter-active,
.select-menu-leave-active {
  transition:
    opacity 260ms ease,
    transform 260ms ease;
}
.select-menu-enter-from {
  opacity: 0;
  transform: translateY(12px);
}
.select-menu-leave-to {
  opacity: 0;
  transform: translateY(-8px);
}
@media (prefers-reduced-motion: reduce) {
  .select-menu-enter-active,
  .select-menu-leave-active {
    transition: none;
  }
}
</style>
