<script setup lang="ts">
// 性能指示器组件
const props = defineProps<{ instanceId: string }>()
type Point = { time: string; cpu: number; memory: number }
const points = ref<Point[]>([])
const loading = ref(true)
let timer: ReturnType<typeof setInterval> | undefined
async function sample() {
  try {
    const result = await $fetch<{ cpu_percent: number; memory_percent: number }>(
      '/api/instances/' + encodeURIComponent(props.instanceId) + '/monitor',
      { credentials: 'include' },
    )
    points.value.push({ time: new Date().toLocaleTimeString(), cpu: result.cpu_percent, memory: result.memory_percent })
    if (points.value.length > 24) points.value.shift()
  } finally {
    loading.value = false
  }
}
onMounted(() => {
  sample()
  timer = setInterval(sample, 5000)
})
onUnmounted(() => {
  if (timer) clearInterval(timer)
})
</script>
<template>
  <section class="space-y-4">
    <div class="grid gap-4 md:grid-cols-2">
      <article class="bg-surface/40 border border-border p-5">
        <p class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">CPU LOAD</p>
        <strong class="mt-3 block font-mono text-3xl text-text-primary"
          >{{ points.at(-1)?.cpu.toFixed(1) || '0.0' }}%</strong
        >
        <div class="mt-5 flex h-20 items-end gap-1 border-b border-border">
          <i
            v-for="(point, index) in points"
            :key="index"
            class="bg-brand/70 flex-1 transition-all duration-500"
            :style="{ height: Math.max(3, Math.min(100, point.cpu)) + '%' }"
          />
        </div>
      </article>
      <article class="bg-surface/40 border border-border p-5">
        <p class="font-mono text-[10px] tracking-[0.18em] text-text-secondary">MEMORY LOAD</p>
        <strong class="mt-3 block font-mono text-3xl text-text-primary"
          >{{ points.at(-1)?.memory.toFixed(1) || '0.0' }}%</strong
        >
        <div class="mt-5 flex h-20 items-end gap-1 border-b border-border">
          <i
            v-for="(point, index) in points"
            :key="index"
            class="bg-data-live/70 flex-1 transition-all duration-500"
            :style="{ height: Math.max(3, Math.min(100, point.memory)) + '%' }"
          />
        </div>
      </article>
    </div>
    <p class="font-mono text-[10px] text-text-secondary">
      {{ loading ? '读取监控数据……' : '每 5 秒采样 · 最近 ' + points.length + ' 个样本' }}
    </p>
  </section>
</template>
