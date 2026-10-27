export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: false,
  srcDir: 'app/',
  modules: ['@nuxtjs/color-mode', '@nuxtjs/tailwindcss'],
  colorMode: { classSuffix: '', preference: 'system', fallback: 'dark' },
  css: ['~/assets/css/main.css'],
  devServer: { port: 5173 },
  runtimeConfig: {
    public: { apiBase: process.env.NUXT_PUBLIC_API_BASE || '' }
  },
  vite: { clearScreen: false, logLevel: 'error' },
  devtools: { enabled: false, timeline: { enabled: false } },
  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:27777/api', changeOrigin: true }
    }
  },
  app: { head: { title: 'ATMOSPHERE / 01', meta: [{ name: 'theme-color', content: '#11151b' }] } }
})
