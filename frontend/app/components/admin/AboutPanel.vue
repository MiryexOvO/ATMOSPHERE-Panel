<script setup lang="ts">
defineProps<{ version?: string }>()
const { t } = useI18n()

const repository = 'https://github.com/MiryexOvO/ATMOSPHERE-Panel'
const readme = 'https://github.com/MiryexOvO/ATMOSPHERE-Panel/blob/main/README.md'

const changes = computed(() => [t('aboutChange1'), t('aboutChange2'), t('aboutChange3')])

// 简介文案可直接换行，渲染时去掉模板缩进。
const intro = computed(() =>
  t('aboutIntro')
    .split('\n')
    .map((line) => line.trim())
    .join('\n'),
)

const capabilities = computed(() => [
  t('aboutCapability1'),
  t('aboutCapability2'),
  t('aboutCapability3'),
  t('aboutCapability4'),
  t('aboutCapability5'),
  t('aboutCapability6'),
])
</script>
<template>
  <div class="space-y-6">
    <AtmosphereCard :interactive="false">
      <div class="flex flex-wrap items-start justify-between gap-6">
        <div class="max-w-2xl min-w-0">
          <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ PROJECT DOSSIER</p>
          <h2 class="mt-3 font-serif text-2xl">
            {{ t('aboutTitle') }}
          </h2>
          <p class="mt-4 text-sm leading-7 whitespace-pre-line text-text-secondary">{{ intro }}</p>
        </div>
        <div class="shrink-0 border border-border px-4 py-3 font-mono">
          <p class="text-[10px] tracking-[.2em] text-text-secondary">PANEL VERSION</p>
          <p class="mt-1 text-sm text-brand">{{ version || 'ATMOSPHERE / 02' }}</p>
        </div>
      </div>
      <div class="mt-6 flex flex-wrap items-center gap-5 border-t border-border pt-5 font-mono text-xs text-brand">
        <a :href="repository" target="_blank" rel="noopener noreferrer" class="hover:text-text-primary">
          {{ t('aboutGithub') }} →
        </a>
        <a :href="readme" target="_blank" rel="noopener noreferrer" class="hover:text-text-primary"> README → </a>
        <a
          href="https://opensource.org/licenses/MIT"
          target="_blank"
          rel="noopener noreferrer"
          class="hover:text-text-primary"
        >
          MIT LICENSE →
        </a>
      </div>
    </AtmosphereCard>
    <div class="grid gap-6 lg:grid-cols-3">
      <AtmosphereCard :interactive="false">
        <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ CHANGELOG</p>
        <h3 class="mt-2 font-serif text-xl">{{ t('aboutStack') }}</h3>
        <p class="mt-4 font-mono text-[10px] text-brand">2026.11 / RELEASE PREVIEW</p>
        <ol class="mt-2 font-mono text-xs">
          <li v-for="(change, index) in changes" :key="change" class="flex gap-3 border-b border-border/60 py-3 leading-6 last:border-b-0">
            <span class="text-brand">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="text-text-secondary">{{ change }}</span>
          </li>
        </ol>
        <a :href="`${repository}/releases`" target="_blank" rel="noopener noreferrer" class="mt-5 inline-block font-mono text-xs text-brand">GitHub Releases →</a>
      </AtmosphereCard>
      <AtmosphereCard :interactive="false">
        <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ FEATURE SET</p>
        <h3 class="mt-2 font-serif text-xl">{{ t('aboutCapabilities') }}</h3>
        <ol class="mt-5 font-mono text-xs">
          <li
            v-for="(item, index) in capabilities"
            :key="item"
            class="flex gap-3 border-b border-border/60 py-3 leading-6 last:border-b-0"
          >
            <span class="text-[10px] text-brand">{{ String(index + 1).padStart(2, '0') }}</span>
            <span class="text-text-secondary">{{ item }}</span>
          </li>
        </ol>
      </AtmosphereCard>
      <AtmosphereCard :interactive="false">
        <p class="font-mono text-[10px] tracking-[.2em] text-brand">/ HOW IT RUNS</p>
        <h3 class="mt-2 font-serif text-xl">{{ t('aboutDeployment') }}</h3>
        <dl class="mt-5 font-mono text-xs">
          <div class="flex items-center justify-between gap-4 border-b border-border/60 py-3">
            <dt class="text-text-secondary">PLATFORM</dt>
            <dd class="text-right text-text-primary">Linux / Windows / macOS</dd>
          </div>
          <div class="flex items-center justify-between gap-4 border-b border-border/60 py-3">
            <dt class="text-text-secondary">PROCESS</dt>
            <dd class="text-right text-text-primary">
              {{ t('aboutProcess') }}
            </dd>
          </div>
          <div class="flex items-center justify-between gap-4 border-b border-border/60 py-3">
            <dt class="text-text-secondary">PANEL / API</dt>
            <dd class="text-right text-text-primary">27777</dd>
          </div>
          <div class="flex items-center justify-between gap-4 border-b border-border/60 py-3">
            <dt class="text-text-secondary">WEB ENTRY</dt>
            <dd class="text-right text-text-primary">27777</dd>
          </div>
          <div class="flex items-center justify-between gap-4 py-3">
            <dt class="text-text-secondary">HOSTING</dt>
            <dd class="text-right text-text-primary">{{ t('aboutHosting') }}</dd>
          </div>
        </dl>
      </AtmosphereCard>
    </div>
    <footer
      class="space-y-2 border-t border-border pt-5 text-center font-mono text-[10px] tracking-[.2em] text-text-secondary"
    >
      <p>AUTHORS · MIRYEX / KIPPU</p>
      <p>© 2026 MIRYEX · ATMOSPHERE-PANEL · MIT LICENSE</p>
    </footer>
  </div>
</template>
