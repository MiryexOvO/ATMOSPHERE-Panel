<script setup lang="ts">
const RADIUS = 140 // 鼠标影响半径
const PUSH = 11 // 最大推开距离

const host = ref<HTMLElement | null>(null)
let frame = 0
let resizeFrame = 0
let pointer = { x: -1e4, y: -1e4 }
let dots: { el: HTMLElement; x: number; y: number; push: number; spread: number; angle: number }[] = []
let reduced = false

// 按原背景的间距生成点阵：小点 83×71，品牌色点 211×193
function addLattice(el: HTMLElement, width: number, height: number, stepX: number, stepY: number, groupClass: string) {
  const group = document.createElement('div')
  group.className = `df-group ${groupClass}`
  for (let y = stepY / 2; y < height; y += stepY) {
    for (let x = stepX / 2; x < width; x += stepX) {
      const dot = document.createElement('span')
      dot.className = 'df-dot'
      dot.style.left = `${x}px`
      dot.style.top = `${y}px`
      group.appendChild(dot)
      // 每颗星星的反应力度和感应范围略有差异，移动时更像零散星点而非水波
      dots.push({
        el: dot,
        x,
        y,
        push: 0.55 + Math.random() * 0.8,
        spread: 0.8 + Math.random() * 0.45,
        angle: (Math.random() - 0.5) * 0.7,
      })
    }
  }
  el.appendChild(group)
}

function build() {
  const el = host.value
  if (!el) return
  el.replaceChildren()
  dots = []
  const width = el.clientWidth
  const height = el.clientHeight
  addLattice(el, width, height, 83, 71, 'df-group-sm')
  addLattice(el, width, height, 211, 193, 'df-group-lg')
}

// 距离越近推得越远，方向为「点 → 远离鼠标」，离开半径后回原位；
// 三次方衰减 + 每颗点的随机系数，避免出现一圈同步扩散的水波感
function update() {
  frame = 0
  for (const dot of dots) {
    const dx = dot.x - pointer.x
    const dy = dot.y - pointer.y
    const range = RADIUS * dot.spread
    const distance = Math.hypot(dx, dy)
    if (distance < range && distance > 0.5) {
      const force = (1 - distance / range) ** 3 * PUSH * dot.push
      const angle = Math.atan2(dy, dx) + dot.angle
      dot.el.style.transform = `translate(${(Math.cos(angle) * force).toFixed(2)}px, ${(Math.sin(angle) * force).toFixed(2)}px)`
    } else {
      dot.el.style.transform = ''
    }
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
  build()
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
  <div ref="host" class="df-dot-field" aria-hidden="true" />
</template>

<!-- 圆点是运行时创建的，拿不到 scoped 的 data-v 属性，因此用全局样式（类名已加 df- 前缀避免冲突） -->
<style>
.df-dot-field {
  position: absolute;
  inset: 0;
}
.df-group {
  position: absolute;
  inset: 0;
}
.df-group-sm {
  animation: df-twinkle 9s ease-in-out infinite;
}
.df-group-lg {
  animation: df-twinkle-lg 13s ease-in-out infinite reverse;
}
.df-dot {
  position: absolute;
  border-radius: 50%;
  transition: transform 680ms cubic-bezier(0.22, 1, 0.36, 1);
}
.df-group-sm .df-dot {
  width: 2px;
  height: 2px;
  margin: -1px 0 0 -1px;
  background: var(--text-primary);
  opacity: 0.5;
}
.df-group-lg .df-dot {
  width: 3px;
  height: 3px;
  margin: -1.5px 0 0 -1.5px;
  background: var(--brand);
  opacity: 0.55;
}
@keyframes df-twinkle {
  50% {
    opacity: 0.44;
  }
}
@keyframes df-twinkle-lg {
  50% {
    opacity: 0.4;
  }
}
</style>
