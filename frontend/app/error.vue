<script setup lang="ts">
import AtmosphereCard from '~/components/AtmosphereCard.vue'
import DotField from '~/components/ui/DotField.vue'
import StarfieldBackground from '~/components/ui/StarfieldBackground.vue'

type ErrorLike = { statusCode?: number; statusMessage?: string; message?: string; url?: string }
const props = defineProps<{ error: ErrorLike | null }>()

let t: (key: string) => string = (key) => key
try {
  const i18n = useI18n()
  t = (key: string) => i18n.t(key)
} catch {
  /* i18n 不可用时退回键名 */
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
      title: t('msg_invalid_request'),
      description: t('msg_the_request_is_missing_required_parameters_o'),
    },
    401: {
      title: t('msg_authentication_required'),
      description: t('msg_your_session_has_expired_sign_in_again_to_co'),
    },
    403: {
      title: t('msg_access_denied'),
      description: t('msg_the_current_account_does_not_have_permission'),
    },
    404: {
      title: t('msg_page_not_found'),
      description: t('msg_no_coordinates_match_this_route_return_to_th'),
    },
    405: {
      title: t('msg_method_not_allowed'),
      description: t('msg_this_address_does_not_accept_the_current_req'),
    },
    408: {
      title: t('msg_request_timeout'),
      description: t('msg_the_response_took_too_long_check_your_connec'),
    },
    409: {
      title: t('msg_conflict'),
      description: t('msg_the_resource_state_has_changed_refresh_and_t'),
    },
    422: {
      title: t('msg_validation_failed'),
      description: t('msg_the_submitted_data_failed_validation_check_i'),
    },
    429: {
      title: t('msg_too_many_requests'),
      description: t('msg_the_request_rate_exceeded_the_limit_wait_a_m'),
    },
    500: {
      title: t('msg_internal_error'),
      description: t('msg_the_panel_encountered_an_unexpected_error_tr'),
    },
    502: {
      title: t('msg_bad_gateway'),
      description: t('msg_the_panel_cannot_reach_the_backend_service_m'),
    },
    503: {
      title: t('msg_service_unavailable'),
      description: t('msg_the_service_is_under_maintenance_or_not_read'),
    },
    504: {
      title: t('msg_gateway_timeout'),
      description: t('msg_the_backend_took_too_long_to_respond_try_aga'),
    },
  }
  return (
    table[code.value] || {
      title: t('msg_unknown_error'),
      description: t('msg_the_request_could_not_be_completed_return_to'),
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
  if (isAuthError.value) return { label: t('msg_sign_in_again'), run: () => clearError({ redirect: '/login' }) }
  if (isServerError.value)
    return {
      label: t('msg_reload'),
      run: () => {
        if (typeof window !== 'undefined') window.location.reload()
      },
    }
  return {
    label: t('msg_back_to_console'),
    run: () => clearError({ redirect: '/dashboard' }),
  }
})
const secondaryAction = computed<Action>(() => {
  if (isAuthError.value) return { label: t('msg_back_to_home'), run: () => clearError({ redirect: '/' }) }
  if (isServerError.value)
    return {
      label: t('msg_back_to_console'),
      run: () => clearError({ redirect: '/dashboard' }),
    }
  return { label: t('msg_sign_in'), run: () => clearError({ redirect: '/login' }) }
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
