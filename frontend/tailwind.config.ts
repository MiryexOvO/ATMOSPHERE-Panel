/** @type {import('tailwindcss').Config} */
module.exports = {
  darkMode: 'class',
  content: ['./app/components/**/*.{vue,js,ts}', './app/layouts/**/*.vue', './app/pages/**/*.vue', './app/app.vue'],
  theme: {
    extend: {
      colors: {
        // 映射
        background: 'var(--background)',
        surface: 'var(--surface)',
        brand: 'var(--brand)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        border: 'var(--border)',
      },
      fontFamily: {
        serif: ['Bodoni 72', 'Didot', 'Times New Roman', 'serif'],
        mono: ['ui-monospace', 'SFMono-Regular', 'Menlo', 'Monaco', 'monospace'],
      },
    },
  },
  plugins: [],
}
