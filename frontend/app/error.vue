<script setup lang="ts">
import AtmosphereCard from '~/components/AtmosphereCard.vue'
import DotField from '~/components/ui/DotField.vue'
import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'

type ErrorLike = { statusCode?: number; statusMessage?: string; message?: string; url?: string }
const props = defineProps<{ error: ErrorLike | null }>()

type Tr = (zh: string, en: string, ja: string) => string
// i18n 插件异常时也要能显示错误页，退回中文。
let tr: Tr = (zh) => zh
try {
  tr = usePanelText()
} catch {
  /* 保持中文兜底 */
}

// 仅开发环境支持用 ?code=500 预览不同状态的错误页。
const previewCode =
  import.meta.dev && typeof window !== 'undefined'
    ? Number(new URLSearchParams(window.location.search).get('code')) || 0
    : 0
const previewing = previewCode > 0

const code = computed(() => previewCode || props.error?.statusCode || 500)
const path = computed(() => props.error?.url || (typeof window !== 'undefined' ? window.location.pathname : '/'))
const detail = computed(() =>
  previewing ? `DEV PREVIEW · ?code=${code.value}` : props.error?.message || props.error?.statusMessage || '',
)

type Copy = { title: string; description: string }
// 每一类错误对应一段面向用户的说明，未列出的状态码使用通用文案。
const copy = computed<Copy>(() => {
  const table: Record<number, Copy> = {
    400: {
      title: tr('请求无效', 'Invalid request', '無効なリクエスト'),
      description: tr(
        '请求缺少必要参数，或格式无法识别。请返回控制台重新操作。',
        'The request is missing required parameters or has an unrecognized format. Return to the console and try again.',
        'リクエストに必要なパラメータが欠けているか、形式を認識できません。コンソールに戻ってやり直してください。',
      ),
    },
    401: {
      title: tr('需要身份验证', 'Authentication required', '認証が必要です'),
      description: tr(
        '会话已失效，请重新登录后继续。',
        'Your session has expired. Sign in again to continue.',
        'セッションが切れました。再度ログインして続行してください。',
      ),
    },
    403: {
      title: tr('访问被拒绝', 'Access denied', 'アクセスが拒否されました'),
      description: tr(
        '当前账户没有访问此资源的权限。',
        'The current account does not have permission to access this resource.',
        '現在のアカウントにはこのリソースへのアクセス権がありません。',
      ),
    },
    404: {
      title: tr('页面不存在', 'Page not found', 'ページが見つかりません'),
      description: tr(
        '这条航线上没有对应的坐标。请返回控制台重新导航。',
        'No coordinates match this route. Return to the console and navigate again.',
        'この航路に対応する座標はありません。コンソールに戻って再移動してください。',
      ),
    },
    405: {
      title: tr('请求方式不支持', 'Method not allowed', 'メソッドが許可されていません'),
      description: tr(
        '该地址不接受当前的请求方式。请从面板重新发起操作。',
        'This address does not accept the current request method. Start the action again from the panel.',
        'このアドレスでは現在のリクエスト方式を受け付けません。パネルから操作をやり直してください。',
      ),
    },
    408: {
      title: tr('请求超时', 'Request timeout', 'リクエストがタイムアウトしました'),
      description: tr(
        '等待响应的时间过长，请检查网络后重试。',
        'The response took too long. Check your connection and try again.',
        '応答に時間がかかりすぎました。ネットワークを確認して再試行してください。',
      ),
    },
    409: {
      title: tr('状态冲突', 'Conflict', '状態が競合しています'),
      description: tr(
        '资源状态已经变化，请刷新后再试。',
        'The resource state has changed. Refresh and try again.',
        'リソースの状態が変更されました。更新してから再試行してください。',
      ),
    },
    422: {
      title: tr('数据校验失败', 'Validation failed', 'データ検証に失敗しました'),
      description: tr(
        '提交的数据未通过校验，请检查后重试。',
        'The submitted data failed validation. Check it and try again.',
        '送信されたデータが検証に通りませんでした。確認して再試行してください。',
      ),
    },
    429: {
      title: tr('请求过于频繁', 'Too many requests', 'リクエストが多すぎます'),
      description: tr(
        '操作频率超出限制，请稍等片刻再试。',
        'The request rate exceeded the limit. Wait a moment and try again.',
        'リクエスト頻度が制限を超えました。少し待ってから再試行してください。',
      ),
    },
    500: {
      title: tr('面板内部错误', 'Internal error', '内部エラー'),
      description: tr(
        '面板运行时遇到异常，请稍后重试或查看服务日志。',
        'The panel encountered an unexpected error. Try again later or check the service logs.',
        'パネルの実行中に例外が発生しました。しばらくしてから再試行するか、サービスログを確認してください。',
      ),
    },
    502: {
      title: tr('后端连接失败', 'Bad gateway', 'バックエンド接続エラー'),
      description: tr(
        '面板无法连接到后端服务，请确认服务正在运行。',
        'The panel cannot reach the backend service. Make sure it is running.',
        'パネルがバックエンドサービスに接続できません。サービスが稼働しているか確認してください。',
      ),
    },
    503: {
      title: tr('服务暂不可用', 'Service unavailable', 'サービスを利用できません'),
      description: tr(
        '服务正在维护或尚未就绪，请稍后再试。',
        'The service is under maintenance or not ready yet. Try again later.',
        'サービスはメンテナンス中か、まだ準備ができていません。後でもう一度お試しください。',
      ),
    },
    504: {
      title: tr('后端响应超时', 'Gateway timeout', 'ゲートウェイタイムアウト'),
      description: tr(
        '后端响应超时，请稍后重试。',
        'The backend took too long to respond. Try again later.',
        'バックエンドの応答がタイムアウトしました。後でもう一度お試しください。',
      ),
    },
  }
  return (
    table[code.value] || {
      title: tr('未知错误', 'Unknown error', '不明なエラー'),
      description: tr(
        '请求未能完成，请返回控制台后重试。',
        'The request could not be completed. Return to the console and try again.',
        'リクエストを完了できませんでした。コンソールに戻って再試行してください。',
      ),
    }
  )
})

const isServerError = computed(() => code.value >= 500)
const isAuthError = computed(() => code.value === 401 || code.value === 403)

// 描述固定拆成两行：第一句一行，其余一行。
const descriptionLines = computed(() => {
  const match = copy.value.description.match(/^(.+?[。.!?！？])\s*(.+)$/s)
  return match ? [match[1], match[2]] : [copy.value.description]
})

// 英文状态大字始终全大写；小眉标用错误类别，避免与大字重复。
const englishLabels: Record<number, string> = {
  400: 'INVALID REQUEST',
  401: 'AUTHENTICATION REQUIRED',
  403: 'ACCESS DENIED',
  404: 'PAGE NOT FOUND',
  405: 'METHOD NOT ALLOWED',
  408: 'REQUEST TIMEOUT',
  409: 'CONFLICT',
  422: 'VALIDATION FAILED',
  429: 'TOO MANY REQUESTS',
  500: 'INTERNAL ERROR',
  502: 'BAD GATEWAY',
  503: 'SERVICE UNAVAILABLE',
  504: 'GATEWAY TIMEOUT',
}
const englishLabel = computed(() => englishLabels[code.value] || 'UNKNOWN ERROR')
const errorCategory = computed(() => (code.value >= 500 ? 'SERVER ERROR' : 'CLIENT ERROR'))

const hovering = ref(false)
const pointer = ref({ x: 0, y: 0 })
const pointerLabel = computed(
  () => `X ${String(pointer.value.x).padStart(4, '0')} / Y ${String(pointer.value.y).padStart(4, '0')}`,
)

// 鼠标在卡片内移动时更新准星与坐标读数。
function trackPointer(event: PointerEvent) {
  const node = event.currentTarget as HTMLElement
  const rect = node.getBoundingClientRect()
  const x = Math.round(event.clientX - rect.left)
  const y = Math.round(event.clientY - rect.top)
  pointer.value = { x, y }
  hovering.value = true
  node.style.setProperty('--pointer-x', `${x}px`)
  node.style.setProperty('--pointer-y', `${y}px`)
}
function resetPointer(event: PointerEvent) {
  hovering.value = false
  const node = event.currentTarget as HTMLElement
  node.style.setProperty('--pointer-x', '50%')
  node.style.setProperty('--pointer-y', '50%')
}

type Action = { label: string; run: () => void }
const primaryAction = computed<Action>(() => {
  if (isAuthError.value)
    return { label: tr('重新登录', 'SIGN IN AGAIN', '再ログイン'), run: () => clearError({ redirect: '/login' }) }
  if (isServerError.value)
    return {
      label: tr('重新加载', 'RELOAD', '再読み込み'),
      run: () => {
        if (typeof window !== 'undefined') window.location.reload()
      },
    }
  return {
    label: tr('返回控制台', 'BACK TO CONSOLE', 'コンソールへ'),
    run: () => clearError({ redirect: '/dashboard' }),
  }
})
const secondaryAction = computed<Action>(() => {
  if (isAuthError.value)
    return { label: tr('返回首页', 'BACK TO HOME', 'ホームへ'), run: () => clearError({ redirect: '/' }) }
  if (isServerError.value)
    return {
      label: tr('返回控制台', 'BACK TO CONSOLE', 'コンソールへ'),
      run: () => clearError({ redirect: '/dashboard' }),
    }
  return { label: tr('返回登录', 'SIGN IN', 'ログイン'), run: () => clearError({ redirect: '/login' }) }
})
</script>
<template>
  <div
    class="error-root relative min-h-screen overflow-hidden bg-background text-text-primary"
    :class="{ 'is-danger': isServerError }"
  >
    <StarfieldBackground />
    <div class="pointer-events-none fixed inset-0 z-0"><DotField /></div>
    <main class="relative z-10 mx-auto flex min-h-screen w-full max-w-6xl items-center px-6 py-16 md:px-10">
      <div class="w-full">
        <p class="error-reveal font-mono text-[10px] tracking-[.32em] text-text-secondary">/ ATMOSPHERE / RUNTIME</p>
        <AtmosphereCard class="error-panel relative mt-6 p-8" @pointermove="trackPointer" @pointerleave="resetPointer">
          <span class="error-reticle" :class="{ 'is-active': hovering }" aria-hidden="true">
            <i class="error-reticle-h" />
            <i class="error-reticle-v" />
            <b class="error-reticle-dot" />
          </span>
          <span
            class="pointer-events-none absolute top-0 right-0 z-20 font-mono text-[10px] tracking-[.16em] text-text-secondary transition-opacity duration-150"
            :class="hovering ? 'opacity-70' : 'opacity-0'"
            aria-hidden="true"
            >{{ pointerLabel }}</span
          >
          <div class="relative z-10 flex flex-col gap-9 md:flex-row md:items-start">
            <div class="shrink-0">
              <p class="font-mono text-[10px] tracking-[.28em] text-text-secondary">STATUS / {{ code }}</p>
              <div class="mt-10 flex items-center gap-2 text-8xl md:mt-12 md:text-9xl">
                <span class="error-code font-serif leading-none">{{ code }}</span>
                <span class="error-caret block h-[0.72em] w-[2px]" aria-hidden="true" />
              </div>
            </div>
            <div class="min-w-0 flex-1 border-t border-border pt-8 md:border-t-0 md:border-l md:pt-0 md:pl-10">
              <p class="font-mono text-[10px] tracking-[.24em]" :class="isServerError ? 'text-red-400' : 'text-brand'">
                {{ errorCategory }}
              </p>
              <h1 id="error-title" class="mt-3 font-serif text-4xl uppercase md:text-5xl">{{ englishLabel }}</h1>
              <p class="mt-4 max-w-2xl text-sm leading-7 text-text-secondary">
                {{ descriptionLines[0] }}<br v-if="descriptionLines[1]" />{{ descriptionLines[1] }}
              </p>
              <div class="mt-9 flex flex-wrap gap-3 font-mono text-xs">
                <button
                  type="button"
                  class="border border-text-primary/40 px-5 py-3 text-text-primary transition hover:border-text-primary hover:bg-text-primary hover:text-background focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-2 focus-visible:outline-brand"
                  @click="primaryAction.run()"
                >
                  {{ primaryAction.label }} →
                </button>
                <button
                  type="button"
                  class="border border-text-primary/25 px-5 py-3 text-text-primary transition hover:border-text-primary hover:bg-text-primary hover:text-background focus-visible:outline focus-visible:outline-1 focus-visible:outline-offset-2 focus-visible:outline-brand"
                  @click="secondaryAction.run()"
                >
                  {{ secondaryAction.label }}
                </button>
              </div>
            </div>
          </div>
        </AtmosphereCard>
        <div
          class="error-reveal mt-6 flex flex-wrap items-center justify-between gap-3 font-mono text-[10px] tracking-[.18em] text-text-secondary"
          style="animation-delay: 0.18s"
        >
          <span class="max-w-[65%] min-w-0 truncate">
            PATH / <span class="text-text-primary">{{ path }}</span>
          </span>
          <span v-if="detail" class="max-w-[65%] min-w-0 truncate uppercase">DETAIL / {{ detail }}</span>
        </div>
      </div>
    </main>
  </div>
</template>
<style scoped>
.error-root {
  --error-accent: var(--brand);
}
.error-root.is-danger {
  --error-accent: #f87171;
}
.error-panel {
  animation: error-panel-in 700ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
/* 鼠标准星：1px 十字线与坐标读数，不做柔光。 */
.error-reticle {
  position: absolute;
  inset: -2rem;
  z-index: 20;
  pointer-events: none;
  opacity: 0;
  transition: opacity 160ms ease;
}
.error-reticle.is-active {
  opacity: 1;
}
.error-reticle i {
  position: absolute;
  background: color-mix(in srgb, var(--error-accent) 40%, transparent);
}
.error-reticle-h {
  top: var(--pointer-y, 50%);
  right: 0;
  left: 0;
  height: 1px;
}
.error-reticle-v {
  top: 0;
  bottom: 0;
  left: var(--pointer-x, 50%);
  width: 1px;
}
.error-reticle-dot {
  position: absolute;
  top: var(--pointer-y, 50%);
  left: var(--pointer-x, 50%);
  width: 5px;
  height: 5px;
  margin: -2.5px 0 0 -2.5px;
  background: var(--error-accent);
}
.error-reveal {
  animation: error-reveal 700ms cubic-bezier(0.22, 1, 0.36, 1) both;
}
.error-code {
  color: var(--error-accent);
  letter-spacing: -0.04em;
  animation: error-glow 5s ease-in-out infinite;
}
.error-caret {
  background: var(--error-accent);
  animation: error-caret 1s steps(1, end) infinite;
}
@keyframes error-panel-in {
  from {
    opacity: 0;
    transform: translateY(16px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes error-reveal {
  from {
    opacity: 0;
    transform: translateY(8px);
  }
  to {
    opacity: 1;
    transform: none;
  }
}
@keyframes error-glow {
  0%,
  100% {
    text-shadow: 0 0 18px color-mix(in srgb, var(--error-accent) 24%, transparent);
  }
  50% {
    text-shadow: 0 0 34px color-mix(in srgb, var(--error-accent) 42%, transparent);
  }
}
@keyframes error-caret {
  0%,
  49% {
    opacity: 1;
  }
  50%,
  100% {
    opacity: 0;
  }
}
@media (prefers-reduced-motion: reduce) {
  .error-panel,
  .error-reveal,
  .error-code,
  .error-caret {
    animation: none;
  }
  .error-reticle {
    transition: none;
  }
}
</style>
