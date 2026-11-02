<script setup lang="ts">
const props=withDefaults(defineProps<{values:number[];limit?:number;label:string;color?:string}>(),{limit:100,color:'var(--brand)'})
const gradient=useId().replace(/\W/g,'')
// 自适应真实峰值，零值仍保留基线。
const line=computed(()=>{
  const max=Math.max(props.limit,...props.values,1)
  return props.values.map((value,index)=>`${index?'L':'M'}${(index/Math.max(props.values.length-1,1)*480).toFixed(1)},${(128-Math.min(1,value/max)*112).toFixed(1)}`).join(' ')
})
const area=computed(()=>line.value?`${line.value} L480,140 L0,140 Z`:'')
</script>
<template>
  <svg viewBox="0 0 480 140" class="h-36 w-full overflow-visible" role="img" :aria-label="label">
    <defs><linearGradient :id="gradient" x1="0" y1="0" x2="0" y2="1"><stop :stop-color="color" stop-opacity=".26"/><stop offset="1" :stop-color="color" stop-opacity="0"/></linearGradient></defs>
    <path v-for="y in [16,54,92,130]" :key="y" :d="`M0,${y}H480`" stroke="currentColor" stroke-opacity=".1" fill="none"/>
    <path :d="area" :fill="`url(#${gradient})`"/>
    <path :d="line" :stroke="color" stroke-width="2" fill="none" vector-effect="non-scaling-stroke"/>
  </svg>
</template>
