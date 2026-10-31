// 禁用页面原生滚动

const EASE = 0.85 // 每 16.7ms 追赶目标的比例，越接近 1 越慢

export function useSmoothScroll() {
  // 当前实际滚动位置
  let current = 0
  // 滚轮累积出的目标位置
  let target = 0
  let frame = 0
  let lastTime = 0

  function maxScroll() {
    return Math.max(0, document.documentElement.scrollHeight - window.innerHeight)
  }

  function start() {
    if (frame) return
    lastTime = performance.now()
    frame = requestAnimationFrame(step)
  }

  // 不足 0.5px 时吸附上下
  function step(now: number) {
    const dt = Math.max(1, Math.min(64, now - lastTime))
    lastTime = now
    const diff = target - current
    if (Math.abs(diff) < 0.5) {
      current = target
      window.scrollTo(0, current)
      frame = 0
      return
    }
    current += diff * (1 - Math.pow(EASE, dt / 16.7))
    window.scrollTo(0, current)
    frame = requestAnimationFrame(step)
  }

  // 控制台、弹窗列表等
  function isScrollable(target: EventTarget | null) {
    let node = target as HTMLElement | null
    while (node && node !== document.body) {
      const style = getComputedStyle(node)
      if (/(auto|scroll)/.test(style.overflowY) && node.scrollHeight > node.clientHeight) return true
      node = node.parentElement
    }
    return false
  }

  function onWheel(event: WheelEvent) {
    if (event.ctrlKey) return
    // 还浏览器
    if (Math.abs(event.deltaX) > Math.abs(event.deltaY)) return
    const max = maxScroll()
    if (max <= 0 || isScrollable(event.target)) return
    event.preventDefault()
    const scale = event.deltaMode === 1 ? 16 : event.deltaMode === 2 ? window.innerHeight : 1
    target = Math.min(max, Math.max(0, target + event.deltaY * scale))
    start()
  }

  // scrollTo 产生的滚动 忽略
  function onScroll() {
    if (Math.abs(window.scrollY - current) > 2) {
      current = target = window.scrollY
      if (frame) {
        cancelAnimationFrame(frame)
        frame = 0
      }
    }
  }

  function onResize() {
    target = Math.min(target, maxScroll())
  }

  onMounted(() => {
    // 减少滚动时的效果
    if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) return
    current = target = window.scrollY
    window.addEventListener('wheel', onWheel, { passive: false })
    window.addEventListener('scroll', onScroll, { passive: true })
    window.addEventListener('resize', onResize)
  })

  onUnmounted(() => {
    window.removeEventListener('wheel', onWheel)
    window.removeEventListener('scroll', onScroll)
    window.removeEventListener('resize', onResize)
    if (frame) cancelAnimationFrame(frame)
  })
}
