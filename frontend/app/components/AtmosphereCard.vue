<script setup lang="ts">
import { computed, useAttrs } from 'vue'

defineOptions({ inheritAttrs: false })

type CssColor = string
interface AtmosphereCardProps {
  interactive?: boolean
  bgColor?: CssColor
  bgOpacity?: number
  borderColor?: CssColor
  borderWidth?: number
  borderTop?: boolean
  borderLeft?: boolean
  borderBottom?: boolean
  borderRight?: boolean
  hasShadow?: boolean
  shadowOffsetX?: number
  shadowOffsetY?: number
  shadowColor?: CssColor
}

const props = withDefaults(defineProps<AtmosphereCardProps>(), {
  interactive: true,
  bgColor: 'rgba(0, 0, 0, 0.2)',
  bgOpacity: 0.2,
  borderColor: 'rgba(255, 255, 255, 0.2)',
  borderWidth: 1,
  borderTop: true,
  borderLeft: true,
  borderBottom: false,
  borderRight: false,
  hasShadow: true,
  shadowOffsetX: 6,
  shadowOffsetY: 6,
  shadowColor: 'rgba(255, 255, 255, 0.05)',
})

const attrs = useAttrs()
const forwardedAttrs = computed(() => {
  const { class: _class, style: _style, ...rest } = attrs
  return rest
})
const normalizedOpacity = computed(() => Math.min(1, Math.max(0, props.bgOpacity)))
const backgroundColor = computed(() => {
  const value = props.bgColor.trim()
  if (/^rgba?\(/i.test(value) || /^hsla?\(/i.test(value) || value.startsWith('color(')) return value
  if (/^\d+\s*,\s*\d+\s*,\s*\d+$/.test(value)) return `rgb(${value} / ${normalizedOpacity.value})`
  return `color-mix(in srgb, ${value} ${normalizedOpacity.value * 100}%, transparent)`
})
const cardStyle = computed<Record<string, string>>(() => ({
  backgroundColor: backgroundColor.value,
  '--card-border-color': props.borderColor,
  borderStyle: 'solid',
  borderTopWidth: props.borderTop ? `${props.borderWidth}px` : '0px',
  borderLeftWidth: props.borderLeft ? `${props.borderWidth}px` : '0px',
  borderBottomWidth: props.borderBottom ? `${props.borderWidth}px` : '0px',
  borderRightWidth: props.borderRight ? `${props.borderWidth}px` : '0px',
}))
const shadowStyle = computed<Record<string, string>>(() => ({
  transform: `translate(${props.shadowOffsetX}px, ${props.shadowOffsetY}px)`,
  borderColor: props.shadowColor,
}))
</script>

<template>
  <div v-bind="forwardedAttrs" :class="[attrs.class, 'group relative isolate p-8 backdrop-blur-[2px] border-t border-l border-[color:var(--card-border-color)] transition-all duration-300', props.interactive ? 'cursor-pointer hover:-translate-y-1 hover:border-brand/60' : '']" :style="[cardStyle, attrs.style]">
    <div v-if="props.hasShadow" aria-hidden="true" class="pointer-events-none absolute inset-0 -z-10 border bg-transparent" :style="shadowStyle" />
    <div class="relative"><slot /></div>
  </div>
</template>

<!--
  ============================================================================
   ATMOCARD组件使用指南 (之后还要完善)
  ============================================================================

  TYPE 1：默认卡片（登录页风格 左上亮边 右下无边框）

  <AtmosphereCard>
    <div class="text-text-primary">你的内容</div>
  </AtmosphereCard>

  TYPE 2：全包围细线边框（仪表盘数据块风格）

  <AtmosphereCard
    :border-bottom="true"
    :border-right="true"
    variant="glass-light"
  >
    <h3>ACTIVE INSTANCES</h3>
  </AtmosphereCard>

  TYPE 3：颜色+边框定制（比如说你要做警告红框 / 特定边框距离）

  <AtmosphereCard
    bg-color="rgba(255, 0, 0, 0.1)"
    border-color="rgba(255, 0, 0, 0.3)"
    :shadow-offset-x="6"
    :shadow-offset-y="6"
    shadow-color="rgba(255,0,0,0.2)"
  >
    <h3 class="text-red-500">危险警告</h3>
  </AtmosphereCard>

  TYPE 4：无阴影的扁平卡片

  <AtmosphereCard :has-shadow="false">
    [内容]
  </AtmosphereCard>

  Props 表 (非常好VUE)

  variant         String   'glass'                预设：'glass' / 'glass-light' / 'solid'
  bgColor         String   '#000000'              背景基础色
  bgOpacity       Number   0.2                    背景透明度（0~1）
  borderColor     String   rgba(255,255,255,0.2)  边框颜色
  borderWidth     Number   1                      边框粗细
  borderTop       Boolean  true                   顶部边框
  borderLeft      Boolean  true                   左侧边框
  borderBottom    Boolean  false                  底部边框
  borderRight     Boolean  false                  右侧边框
  hasShadow       Boolean  true                   右下偏移错位阴影
  shadowOffsetX   Number   3                      阴影 X 偏移
  shadowOffsetY   Number   3                      阴影 Y 偏移
  shadowColor     String   rgba(255,255,255,0.05) 阴影边框颜色

  注：组件已启用 inheritAttrs: false 并自动透传 $attrs。
  特殊需求仅可用 class 覆盖微调，如
  <AtmosphereCard class="bg-black/50 backdrop-blur-2xl">。
  ============================================================================
-->
