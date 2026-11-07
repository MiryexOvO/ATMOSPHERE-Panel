// 记住用户选择的界面语言：登录页没有默认布局，靠这里在启动时恢复。
export default defineNuxtPlugin((nuxtApp) => {
  if (typeof localStorage === 'undefined') return
  const saved = localStorage.getItem('preferred-language')
  if (saved !== 'zh' && saved !== 'en' && saved !== 'ja') return
  const i18n = nuxtApp.$i18n as { locale: { value: string }; setLocale: (code: string) => unknown } | undefined
  if (!i18n || i18n.locale.value === saved) return
  i18n.setLocale(saved)
})
