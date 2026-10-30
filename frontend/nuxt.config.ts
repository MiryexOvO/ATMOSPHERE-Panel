import { defineNuxtConfig } from 'nuxt/config'

export default defineNuxtConfig({
  compatibilityDate: '2025-01-01',
  ssr: false,
  
  modules: [
    '@nuxtjs/tailwindcss', 
    '@nuxtjs/color-mode',
    '@nuxtjs/i18n'
  ],
  
  colorMode: { 
    classSuffix: '', 
    preference: 'dark', 
    fallback: 'dark' 
  },
  i18n: {
    restructureDir: false, // 
    defaultLocale: 'zh',
    langDir: 'locales',
    strategy: 'no_prefix',
    locales: [
      { code: 'zh', name: '中文', file: 'zh.json' },
      { code: 'en', name: 'English', file: 'en.json' },
      { code: 'ja', name: '日本語', file: 'ja.json' }
    ]
  },
  
  // I HATE TAILWIND
  css: ['~/assets/css/main.css'],
  
  devServer: { port: 5173 },
  runtimeConfig: {
    public: { apiBase: process.env.NUXT_PUBLIC_API_BASE || '/api' }
  },
  vite: { clearScreen: false, logLevel: 'error' },
  devtools: { enabled: false, timeline: { enabled: false } },
  nitro: {
    devProxy: {
      '/api': { target: 'http://127.0.0.1:27777/api', changeOrigin: true }
    }
  },
  app: { 
    head: { 
      title: 'ATMOSPHERE / 01', 
      meta: [{ name: 'theme-color', content: '#11151b' }] 
    } 
  }
})