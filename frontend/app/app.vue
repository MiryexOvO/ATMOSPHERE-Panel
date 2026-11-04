<script setup lang="ts">
import RouteSeam from '~/components/ui/RouteSeam.vue'

const colorMode = useColorMode()
// 挂载上就恢复自定义的颜色
usePanelTheme()
watch(
  () => colorMode.value,
  (mode) => {
    if (import.meta.client && !localStorage.getItem(THEME_STORAGE_KEY))
      applyTheme(themePresets[mode === 'light' ? 'light' : 'dark'])
  },
)
</script>
<template>
  <NuxtLayout>
    <NuxtPage :transition="false" />
  </NuxtLayout>
  <RouteSeam />
</template>
