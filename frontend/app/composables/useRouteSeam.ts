export type SeamPhase =
  | 'idle'
  | 'at-card'
  | 'away'
  | 'clearing'
  | 'completed'
  | 'retracting'
  // 登出反向动画：覆盖仪表盘 → 收拢回登录卡片
  | 'sealing'
  | 'sealed'
  | 'returning'

// 无缝路由
// 半透明矩形从卡片中心铺满屏幕

export function useRouteSeam() {
  return useState<{ phase: SeamPhase; x: number; y: number; w: number; h: number }>('route-seam', () => ({
    phase: 'idle',
    x: 0,
    y: 0,
    w: 0,
    h: 0,
  }))
}
