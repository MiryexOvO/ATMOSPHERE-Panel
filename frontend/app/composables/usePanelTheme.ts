// 调色板逻辑
// usePanelTheme() 负责组件里的响应式状态与挂载恢复

// 主题偏好
export type ThemeMode = 'system' | 'dark' | 'light'
// 实际主题
export type ThemeName = 'dark' | 'light'

// 四个语义色
export type PanelColors = {
  textPrimary: string
  textSecondary: string
  surface: string
  background: string
}

// label 展示名
// variable CSS 变量名
// key PanelColors 字段
export type ColorField = { label: string; variable: string; key: keyof PanelColors }

// localStorage 保存自定义颜色的键名
export const THEME_STORAGE_KEY = 'custom-theme'

// 默认色板
export const themePresets: Record<ThemeName, PanelColors> = {
  dark: { textPrimary: '#e9dfc6', textSecondary: '#a4aaa3', surface: '#1c252d', background: '#11151b' },
  light: { textPrimary: '#202838', textSecondary: '#505868', surface: '#f3efe5', background: '#e9e4d8' },
}

// 四项颜色
export const colorFields: ColorField[] = [
  { label: 'TEXT1', variable: 'text-primary', key: 'textPrimary' },
  { label: 'TEXT2', variable: 'text-secondary', key: 'textSecondary' },
  { label: 'UI COLOR', variable: 'surface', key: 'surface' },
  { label: 'BACKGROUND', variable: 'background', key: 'background' },
]

//
export const themeOptions: { label: string; value: ThemeMode }[] = [
  { label: 'SYSTEM', value: 'system' },
  { label: 'DARK', value: 'dark' },
  { label: 'LIGHT', value: 'light' },
]

// 读取不到会显示 dark 的
export function resolveThemeMode(mode: ThemeMode): ThemeName {
  if (mode !== 'system') return mode
  return typeof window !== 'undefined' && window.matchMedia('(prefers-color-scheme: light)').matches ? 'light' : 'dark'
}

// 写入 CSS
export function applyTheme(colors: PanelColors, root: HTMLElement = document.documentElement) {
  root.style.setProperty('--text-primary', colors.textPrimary)
  root.style.setProperty('--text-secondary', colors.textSecondary)
  root.style.setProperty('--surface', colors.surface)
  root.style.setProperty('--background', colors.background)
  root.style.setProperty('--brand', colors.textPrimary)
}

export function readStoredTheme(): PanelColors | null {
  if (typeof localStorage === 'undefined') return null
  try {
    const saved = localStorage.getItem(THEME_STORAGE_KEY)
    return saved ? (JSON.parse(saved) as PanelColors) : null
  } catch {
    return null
  }
}

// 切换预设主题移除记录
export function saveStoredTheme(colors: PanelColors) {
  localStorage.setItem(THEME_STORAGE_KEY, JSON.stringify(colors))
}

export function usePanelTheme() {
  const colorMode = useColorMode()
  // 三处页面共用
  const colors = useState<PanelColors>('panel-colors', () => ({ ...themePresets.dark }))

  function apply() {
    applyTheme(colors.value)
  }

  // 依旧清理
  function selectTheme(mode: ThemeMode) {
    colorMode.preference = mode
    localStorage.removeItem(THEME_STORAGE_KEY)
    colors.value = { ...themePresets[resolveThemeMode(mode)] }
    apply()
  }

  // 更新共享 生效 持久化
  function applyColor(key: keyof PanelColors, value: string) {
    colors.value = { ...colors.value, [key]: value }
    apply()
    saveStoredTheme(colors.value)
  }

  function restore() {
    const saved = readStoredTheme()
    colors.value = saved ?? { ...themePresets[colorMode.value === 'light' ? 'light' : 'dark'] }
    apply()
  }

  onMounted(restore)

  return {
    // 当前颜色
    colors,
    // 调色盘
    fields: colorFields,
    // SYSTEM DARK LIGHT
    themeOptions,
    // 切换预设
    selectTheme,
    // 单个颜色的修改
    applyColor,
    // 手动恢复
    restore,
  }
}
