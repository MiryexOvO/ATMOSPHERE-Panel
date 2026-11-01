<script setup lang="ts">
const seam = useRouteSeam()

// 距视口边缘
const EDGE = 0

const styles = computed(() => {
  const s = seam.value
  if (s.phase === 'at-card') {
    return {
      tl: { left: `${s.x - 34}px`, top: `${s.y - 34}px`, width: `${s.w}px`, height: `${s.h}px` },
      br: { left: `${s.x + 34}px`, top: `${s.y + 34}px`, width: `${s.w}px`, height: `${s.h}px` },
      veil: { left: `${s.x}px`, top: `${s.y}px`, width: `${s.w}px`, height: `${s.h}px` },
    }
  }
  const veil = { left: '0px', top: '0px', width: '100vw', height: '100vh' }
  // 只移动位置，不改变长度：右下角的右/下边贴住视口边缘
  return {
    tl: { left: `${EDGE}px`, top: `${EDGE}px`, width: `${s.w}px`, height: `${s.h}px` },
    br: {
      left: `calc(100vw - ${EDGE + s.w}px)`,
      top: `calc(100vh - ${EDGE + s.h}px)`,
      width: `${s.w}px`,
      height: `${s.h}px`,
    },
    veil,
  }
})
</script>

<template>
  <!-- 矩形单独一层，进入仪表盘后仍在页面之上完成淡出，避免页面元素瞬间出现 -->
  <div
    v-if="seam.phase !== 'idle'"
    class="route-seam-veil-layer"
    :class="{
      'is-away':
        seam.phase === 'away' || seam.phase === 'clearing' || seam.phase === 'completed' || seam.phase === 'retracting',
      'is-clearing': seam.phase === 'clearing',
      'is-completed': seam.phase === 'completed',
      'is-retracting': seam.phase === 'retracting',
    }"
    aria-hidden="true"
  >
    <div class="route-seam-veil" :style="styles.veil" />
  </div>
  <!-- 消失时被页面覆盖 -->
  <div
    v-if="seam.phase !== 'idle'"
    class="route-seam"
    :class="{
      'is-away':
        seam.phase === 'away' || seam.phase === 'clearing' || seam.phase === 'completed' || seam.phase === 'retracting',
      'is-clearing': seam.phase === 'clearing',
      'is-completed': seam.phase === 'completed',
      'is-retracting': seam.phase === 'retracting',
    }"
    aria-hidden="true"
  >
    <div class="route-seam-piece route-seam-tl" :style="styles.tl">
      <span class="route-seam-bar route-seam-bar-h" />
      <span class="route-seam-bar route-seam-bar-v" />
    </div>
    <div class="route-seam-piece route-seam-br" :style="styles.br">
      <span class="route-seam-bar route-seam-bar-h" />
      <span class="route-seam-bar route-seam-bar-v" />
    </div>
  </div>
  <!-- 矩形右上角的状态文字 -->
  <div v-if="seam.phase !== 'idle'" class="route-seam-status" aria-hidden="true">
    <div class="route-seam-status-box" :style="styles.veil">
      <span
        class="route-seam-status-text"
        :class="{
          'is-auth': seam.phase === 'away' || seam.phase === 'clearing',
          'is-blinking': seam.phase === 'completed',
        }"
        >Authenticating...</span
      >
      <span
        class="route-seam-status-text is-done"
        :class="{ 'is-showing': seam.phase === 'completed' || seam.phase === 'retracting' }"
        >[Completed]</span
      >
    </div>
  </div>
</template>

<style scoped>
.route-seam-veil-layer {
  position: fixed;
  inset: 0;
  z-index: 69;
  pointer-events: none;
}
.route-seam {
  position: fixed;
  inset: 0;
  z-index: 70;
  pointer-events: none;
}
/* 进入仪表盘后细线降到页面内容之下 */
.route-seam.is-clearing,
.route-seam.is-completed,
.route-seam.is-retracting {
  z-index: 5;
}
.route-seam-piece {
  position: absolute;
  transition:
    left 800ms cubic-bezier(0.22, 1, 0.36, 1),
    top 800ms cubic-bezier(0.22, 1, 0.36, 1);
}
/* 细线 */
.route-seam-bar {
  position: absolute;
  display: block;
  background: rgba(255, 255, 255, 0.05);
}
.route-seam-bar-h {
  top: 0;
  right: 0;
  left: 0;
  height: 1px;
  transform-origin: left center;
  transition:
    height 800ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color 800ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 520ms cubic-bezier(0.4, 0, 0.2, 1);
}
.route-seam-bar-v {
  top: 0;
  bottom: 0;
  left: 0;
  width: 1px;
  transform-origin: center top;
  transition:
    width 800ms cubic-bezier(0.22, 1, 0.36, 1),
    background-color 800ms cubic-bezier(0.22, 1, 0.36, 1),
    transform 520ms cubic-bezier(0.4, 0, 0.2, 1);
}
.route-seam-br .route-seam-bar-h {
  top: auto;
  bottom: 0;
  transform-origin: right center;
}
.route-seam-br .route-seam-bar-v {
  left: auto;
  right: 0;
  transform-origin: center bottom;
}
/* 更粗 更亮 */
.route-seam.is-away .route-seam-bar-h {
  height: 2px;
  background-color: rgba(255, 255, 255, 0.2);
}
.route-seam.is-away .route-seam-bar-v {
  width: 2px;
  background-color: rgba(255, 255, 255, 0.2);
}
/* 消失 缩短 */
.route-seam.is-retracting .route-seam-bar-h {
  transform: scaleX(0);
}
.route-seam.is-retracting .route-seam-bar-v {
  transform: scaleY(0);
}
/* 中心矩形 淡出 */
.route-seam-veil {
  position: absolute;
  /* 与页面背景一致 */
  background: var(--background);
  opacity: 0;
  transition:
    left 800ms cubic-bezier(0.22, 1, 0.36, 1),
    top 800ms cubic-bezier(0.22, 1, 0.36, 1),
    width 800ms cubic-bezier(0.22, 1, 0.36, 1),
    height 800ms cubic-bezier(0.22, 1, 0.36, 1),
    opacity 280ms ease;
}
.route-seam-veil-layer.is-away .route-seam-veil {
  opacity: 1;
}
.route-seam-veil-layer.is-clearing .route-seam-veil,
.route-seam-veil-layer.is-completed .route-seam-veil,
.route-seam-veil-layer.is-retracting .route-seam-veil {
  opacity: 0;
}
.route-seam-status {
  position: fixed;
  inset: 0;
  z-index: 71;
  pointer-events: none;
}
.route-seam-status-box {
  position: absolute;
  transition:
    left 800ms cubic-bezier(0.22, 1, 0.36, 1),
    top 800ms cubic-bezier(0.22, 1, 0.36, 1),
    width 800ms cubic-bezier(0.22, 1, 0.36, 1),
    height 800ms cubic-bezier(0.22, 1, 0.36, 1);
}
.route-seam-status-text {
  position: absolute;
  top: 88px;
  left: 22px;
  font-family: var(--font-mono);
  font-size: 14px;
  letter-spacing: 0.18em;
  white-space: nowrap;
  color: var(--text-secondary);
  opacity: 0;
}
.route-seam-status-text.is-auth {
  opacity: 1;
}
.route-seam-status-text.is-blinking {
  opacity: 1;
  animation: seam-auth-blink 600ms steps(1, end) forwards;
}
.route-seam-status-text.is-done {
  color: #4ade80;
}
.route-seam-status-text.is-done.is-showing {
  animation: seam-done 800ms ease 600ms both;
}
@keyframes seam-auth-blink {
  0% {
    opacity: 1;
  }
  15% {
    opacity: 0;
  }
  30% {
    opacity: 1;
  }
  45% {
    opacity: 0;
  }
  60% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}
@keyframes seam-done {
  0% {
    opacity: 0;
  }
  10% {
    opacity: 1;
  }
  75% {
    opacity: 1;
  }
  100% {
    opacity: 0;
  }
}
</style>
