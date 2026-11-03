<script setup lang="ts">
const props = defineProps<{ target: HTMLElement | null }>()
const height = ref(0),
  progress = ref(0),
  visible = ref(false)
let resize: ResizeObserver | undefined, mutation: MutationObserver | undefined
let observed: HTMLElement | null = null
let frame = 0,
  dragging = false
const marks = computed(() => Array.from({ length: Math.floor(height.value / 8) }, (_, i) => i))
// 小刻度尺跟随局部容器，不增加第二条页面滚动条。
function measure() {
  const node = props.target
  if (!node) return
  height.value = node.clientHeight
  const max = node.scrollHeight - node.clientHeight
  visible.value = max > 1
  progress.value = max > 0 ? node.scrollTop / max : 0
}
function schedule() {
  if (!frame)
    frame = requestAnimationFrame(() => {
      frame = 0
      measure()
    })
}
function disconnect() {
  observed?.removeEventListener('scroll', schedule)
  observed?.classList.remove('ruler-scroll-content')
  resize?.disconnect()
  mutation?.disconnect()
}
watch(
  () => props.target,
  (node) => {
    disconnect()
    observed = node
    if (!node) return
    node.classList.add('ruler-scroll-content')
    node.addEventListener('scroll', schedule, { passive: true })
    resize = new ResizeObserver(schedule)
    resize.observe(node)
    mutation = new MutationObserver(schedule)
    mutation.observe(node, { childList: true, subtree: true, characterData: true })
    schedule()
  },
  { flush: 'post', immediate: true },
)
function seek(event: PointerEvent) {
  if (!props.target) return
  const box = (event.currentTarget as HTMLElement).getBoundingClientRect()
  const ratio = Math.max(0, Math.min(1, (event.clientY - box.top) / box.height))
  props.target.scrollTop = ratio * (props.target.scrollHeight - props.target.clientHeight)
}
function begin(event: PointerEvent) {
  dragging = true
  ;(event.currentTarget as HTMLElement).setPointerCapture(event.pointerId)
  seek(event)
}
function keyboard(event: KeyboardEvent) {
  if (!props.target) return
  const node = props.target
  const delta =
    event.key === 'ArrowDown'
      ? 32
      : event.key === 'ArrowUp'
        ? -32
        : event.key === 'PageDown'
          ? node.clientHeight
          : event.key === 'PageUp'
            ? -node.clientHeight
            : 0
  if (delta) {
    event.preventDefault()
    node.scrollTop += delta
  } else if (event.key === 'Home' || event.key === 'End') {
    event.preventDefault()
    node.scrollTop = event.key === 'Home' ? 0 : node.scrollHeight
  }
}
onUnmounted(() => {
  disconnect()
  if (frame) cancelAnimationFrame(frame)
})
</script>
<template>
  <div
    v-if="visible"
    class="local-ruler"
    role="scrollbar"
    tabindex="0"
    aria-label="Scroll"
    aria-orientation="vertical"
    :aria-valuenow="Math.round(progress * 100)"
    :aria-valuemin="0"
    :aria-valuemax="100"
    @pointerdown.prevent="begin"
    @pointermove="dragging && seek($event)"
    @pointerup="dragging = false"
    @lostpointercapture="dragging = false"
    @keydown="keyboard"
    @wheel.prevent="target?.scrollBy(0, $event.deltaY)"
  >
    <i
      v-for="mark in marks"
      :key="mark"
      :style="{ top: mark * 8 + 'px', width: mark % 5 === 0 ? '12px' : '5px', opacity: mark % 5 === 0 ? 0.5 : 0.2 }"
    />
    <span class="local-ruler-position" :style="{ top: Math.min(height - 2, progress * height) + 'px' }" />
  </div>
</template>
<style scoped>
.local-ruler {
  position: absolute;
  right: 0;
  top: 0;
  bottom: 0;
  width: 20px;
  touch-action: none;
  cursor: ns-resize;
  outline: none;
  background: linear-gradient(90deg, transparent, color-mix(in srgb, var(--background) 85%, transparent));
}
.local-ruler i {
  position: absolute;
  right: 1px;
  height: 1px;
  background: var(--text-secondary);
  pointer-events: none;
}
.local-ruler-position {
  position: absolute;
  right: 0;
  height: 1px;
  width: 19px;
  background: var(--brand);
  box-shadow: 0 0 6px color-mix(in srgb, var(--brand) 35%, transparent);
  pointer-events: none;
}
.local-ruler:focus-visible {
  outline: 1px solid var(--brand);
  outline-offset: 2px;
}
</style>
