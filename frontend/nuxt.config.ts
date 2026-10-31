import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: false,

  modules: ['@nuxtjs/color-mode', '@nuxtjs/i18n'],

  colorMode: {
    classSuffix: '',
    preference: 'dark',
    fallback: 'dark',
  },
  typescript: {
    nodeTsConfig: {
      compilerOptions: { types: ['node'] },
    },
  },
  i18n: {
    defaultLocale: 'zh',
    strategy: 'no_prefix',
    locales: [
      { code: 'zh', name: '中文' },
      { code: 'en', name: 'English' },
      { code: 'ja', name: '日本語' },
    ],
    vueI18n: './i18n.config.ts',
  },

  css: ['~/assets/css/main.css'],

  postcss: {
    plugins: {
      '@tailwindcss/postcss': {},
    },
  },

  devServer: { port: 5173 },
  runtimeConfig: {
    public: { apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api' },
  },
  vite: { clearScreen: false, logLevel: 'error' },
  devtools: { enabled: true, timeline: { enabled: false } },
  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:27777/api', changeOrigin: true },
    },
  },
  app: {
    head: {
      title: 'ATMOSPHERE / 01',
      meta: [{ name: 'theme-color', content: '#11151b' }],
    },
  },
})
