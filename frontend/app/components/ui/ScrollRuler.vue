<script setup lang="ts">
// 小刻度
const TICK = 8 
// 五个一个大刻度
const MAJOR_EVERY = 5
// 五个一个标注刻度
const LABEL_EVERY = 5
const MAJOR_STEP = TICK * MAJOR_EVERY
// 追赶系数
const EASE = 0.93

const progress = ref(0)
// 总长度
const rulerHeight = ref(0)
let target = 0
let measureFrame = 0
let chaseFrame = 0
let lastTime = 0
let observer: ResizeObserver | undefined

const labels = computed(() => {
  const items: { top: number, value: string }[] = []
  const majors = Math.floor(rulerHeight.value / MAJOR_STEP)
  for (let i = LABEL_EVERY; i <= majors; i += LABEL_EVERY)
    items.push({ top: i * MAJOR_STEP, value: String(i).padStart(2, '0') })
  return items
})

// 百分比整数
const percentValue = computed(() => Math.min(100, Math.max(0, Math.round(progress.value * 100))))

const digits = computed(() => String(percentValue.value).padStart(3, '0').split('').map(Number))

// 已滚动距离 除以 可滚动总距离
function measure() {
  const doc = document.documentElement
  rulerHeight.value = doc.scrollHeight
  const max = doc.scrollHeight - window.innerHeight
  target = max > 0 ? Math.min(1, Math.max(0, window.scrollY / max)) : 0
  startChase()
}

function startChase() {
  if (chaseFrame) return
  lastTime = performance.now()
  chaseFrame = requestAnimationFrame(chase)
}

// 缓动
function chase(now: number) {
  const dt = Math.max(1, Math.min(64, now - lastTime))
  lastTime = now
  const diff = target - progress.value
  if (Math.abs(diff) < 0.0005) {
    progress.value = target
    chaseFrame = 0
    return
  }
  progress.value += diff * (1 - Math.pow(EASE, dt / 16.7))
  chaseFrame = requestAnimationFrame(chase)
}

// 合并同一帧内的多次触发，防抖
function schedule() {
  if (measureFrame) return
  measureFrame = requestAnimationFrame(() => {
    measureFrame = 0
    measure()
  })
}

onMounted(() => {
  measure()
  window.addEventListener('scroll', schedule, { passive: true })
  window.addEventListener('resize', schedule)
  observer = new ResizeObserver(schedule)
  observer.observe(document.body)
})

onUnmounted(() => {
  window.removeEventListener('scroll', schedule)
  window.removeEventListener('resize', schedule)
  observer?.disconnect()
  if (measureFrame) cancelAnimationFrame(measureFrame)
  if (chaseFrame) cancelAnimationFrame(chaseFrame)
})
</script>

<template>
  <div class="pointer-events-none absolute inset-y-0 right-0 z-30 w-[30px]" aria-hidden="true">
    <div class="ruler-minor absolute inset-y-0 right-0 w-[5px]" />
    <div class="ruler-major absolute inset-y-0 right-0 w-2.5" />
    <div class="ruler-labeled absolute inset-y-0 right-0 w-4" />
    <span
      v-for="label in labels"
      :key="label.top"
      class="absolute right-[19px] -translate-y-1/2 font-mono text-[8px] leading-none text-text-secondary opacity-45 tabular-nums"
      :style="{ top: `${label.top}px` }"
    >{{ label.value }}</span>
  </div>
  <!-- 视口内的标注线 + 百分比：随滚动进度从视口顶部滑到视口底部 -->
  <div
    class="pointer-events-none fixed inset-0 z-40"
    :style="{ '--ruler-progress': progress }"
    aria-hidden="true"
  >
    <div class="ruler-line absolute right-0 top-0 h-px w-[30px]" />
    <!-- 百分比翻页 -->
    <span class="ruler-percent absolute right-[34px] top-0 font-mono text-[9px] text-text-secondary tabular-nums">
      <span v-for="(digit, index) in digits" :key="index" class="ruler-digit">
        <span class="ruler-digit-strip" :style="{ transform: `translateY(${-digit}em)` }">
          <span v-for="n in 10" :key="n" class="ruler-digit-cell">{{ n - 1 }}</span>
        </span>
      </span>
      <span class="ruler-digit-cell">%</span>
    </span>
  </div>
</template>

<style scoped>
.ruler-minor {
  background-image: repeating-linear-gradient(to bottom, var(--text-secondary) 0 1px, transparent 1px 8px);
  opacity: 0.18;
}

.ruler-major {
  background-image: repeating-linear-gradient(to bottom, var(--text-secondary) 0 1px, transparent 1px 40px);
  opacity: 0.45;
}

.ruler-labeled {
  background-image: repeating-linear-gradient(to bottom, var(--text-secondary) 0 1px, transparent 1px 200px);
  opacity: 0.7;
}

.ruler-line {
  background: var(--brand);
  box-shadow: 0 0 8px var(--brand);
  transform: translateY(calc(var(--ruler-progress) * (100vh - 1px)));
}

.ruler-percent {
  display: inline-flex;
  height: 1em;
  line-height: 1;
  transform: translateY(calc(clamp(5px, calc(var(--ruler-progress) * (100vh - 1px) + 0.5px), calc(100vh - 5px)) - 50%));
}

.ruler-digit {
  display: inline-block;
  width: 0.62em;
  height: 1em;
  overflow: hidden;
  text-align: center;
}

.ruler-digit-strip {
  display: flex;
  flex-direction: column;
  transition: transform 320ms cubic-bezier(0.22, 1, 0.36, 1);
}

.ruler-digit-cell {
  display: block;
  height: 1em;
  line-height: 1em;
}
</style>
