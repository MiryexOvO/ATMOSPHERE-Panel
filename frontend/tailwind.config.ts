import type { Config } from 'tailwindcss'

export default <Partial<Config>>{
  darkMode: 'class',
  content: ['./app/**/*.{vue,ts,js}'],
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        surface: 'var(--surface)',
        border: 'var(--border)',
        brand: 'var(--brand)',
        'text-main': 'var(--text-primary)',
        'text-sub': 'var(--text-secondary)',
        'text-secondary': 'var(--text-secondary)',
        primary: 'var(--primary)',
        'primary-foreground': 'var(--primary-foreground)',
        'data-live': 'var(--data-live)',
        danger: 'var(--danger)'
      }
    }
  }
}
