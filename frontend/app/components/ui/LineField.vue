<script setup lang="ts">
// 间距
const SPACING = 72
// 鼠标半径
const RADIUS = 260
// 推动力度
const PUSH = 14
const NX = -Math.SQRT1_2
const NY = -Math.SQRT1_2

const host = ref<HTMLElement | null>(null)
let frame = 0
let resizeFrame = 0
let pointer = { x: -1e4, y: -1e4 }
let origin = { x: 0, y: 0 }
let lines: { el: HTMLElement; s: number }[] = []
let reduced = false

// 每隔 SPACING 生成一条斜线
function build(animate = false) {
  const el = host.value
  if (!el) return
  el.replaceChildren()
  lines = []
  const width = el.clientWidth
  const height = el.clientHeight
  origin = { x: width / 2, y: height / 2 }
  const length = Math.hypot(width, height) * 1.25
  const extent = Math.abs(width * NX) + Math.abs(height * NY)
  const count = Math.ceil(extent / SPACING / 2) + 1
  for (let i = -count; i <= count; i++) {
    const s = i * SPACING
    // 外层 和 内曾
    const wrapper = document.createElement('span')
    wrapper.className = 'lf-line'
    wrapper.style.left = `${origin.x + NX * s}px`
    wrapper.style.top = `${origin.y + NY * s}px`
    if (animate) {
      // 每条线速度不同
      wrapper.style.animationDuration = `${900 + ((Math.abs(i) * 137) % 600)}ms`
    } else {
      wrapper.style.animation = 'none'
    }
    const bar = document.createElement('span')
    bar.className = 'lf-line-bar'
    bar.style.width = `${length}px`
    wrapper.appendChild(bar)
    el.appendChild(wrapper)
    lines.push({ el: bar, s })
  }
}

// 鼠标靠近时线条沿法线方向避让
function update() {
  frame = 0
  for (const line of lines) {
    const distance = (pointer.x - origin.x) * NX + (pointer.y - origin.y) * NY - line.s
    const falloff = Math.abs(distance)
    const offset = falloff < RADIUS ? -Math.sign(distance) * (1 - falloff / RADIUS) ** 2 * PUSH : 0
    line.el.style.transform = `translate(-50%, -50%) rotate(135deg) translateY(${offset.toFixed(2)}px)`
  }
}

function schedule() {
  if (frame) return
  frame = requestAnimationFrame(update)
}

function onPointerMove(event: PointerEvent) {
  pointer = { x: event.clientX, y: event.clientY }
  schedule()
}

function onPointerLeave() {
  pointer = { x: -1e4, y: -1e4 }
  schedule()
}

function onResize() {
  if (resizeFrame) return
  resizeFrame = requestAnimationFrame(() => {
    resizeFrame = 0
    build()
    update()
  })
}

onMounted(() => {
  build(true)
  reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches
  if (!reduced) {
    window.addEventListener('pointermove', onPointerMove, { passive: true })
    document.documentElement.addEventListener('mouseleave', onPointerLeave)
  }
  window.addEventListener('resize', onResize)
})

onUnmounted(() => {
  window.removeEventListener('pointermove', onPointerMove)
  document.documentElement.removeEventListener('mouseleave', onPointerLeave)
  window.removeEventListener('resize', onResize)
  if (frame) cancelAnimationFrame(frame)
  if (resizeFrame) cancelAnimationFrame(resizeFrame)
})
</script>

<template>
  <div ref="host" class="lf-field" aria-hidden="true" />
</template>

<!-- 全局样式 -->
<style>
.lf-field {
  position: absolute;
  inset: 0;
  overflow: hidden;
  pointer-events: none;
}
.lf-line {
  position: absolute;
  pointer-events: none;
  /* 从右侧滑入，每条线的时长在 JS 里按序设置 */
  animation: lf-enter 1200ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.lf-line-bar {
  display: block;
  height: 1px;
  background: var(--text-secondary);
  opacity: 0.06;
  pointer-events: none;
  transform: translate(-50%, -50%) rotate(135deg);
  transition: transform 620ms cubic-bezier(0.22, 1, 0.36, 1);
}
@keyframes lf-enter {
  from {
    transform: translateX(110vw);
  }
  to {
    transform: translateX(0);
  }
}
</style>
