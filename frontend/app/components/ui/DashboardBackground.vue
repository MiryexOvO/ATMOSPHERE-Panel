<template>
  <div class="dashboard-hud fixed inset-0 z-0 pointer-events-none overflow-hidden" aria-hidden="true">
    <div class="hud-grid" />
    <div class="hud-glow" />
    <svg class="hud-radar absolute inset-0 h-full w-full" viewBox="0 0 1440 900" preserveAspectRatio="none">
      <g class="hud-crosshair" fill="none" stroke="currentColor">
        <path d="M720 0V900M0 450H1440" stroke-width=".5" />
        <path d="M0 180H1440M0 720H1440" stroke-width=".35" />
      </g>
      <g class="hud-rings" fill="none" stroke="currentColor">
        <circle cx="1160" cy="470" r="150" stroke-width=".55" stroke-dasharray="2 12" />
        <circle cx="1160" cy="470" r="260" stroke-width=".45" stroke-dasharray="1 15" />
        <circle cx="1160" cy="470" r="390" stroke-width=".4" stroke-dasharray="1 19" />
        <circle cx="1160" cy="470" r="530" stroke-width=".35" stroke-dasharray="1 24" />
      </g>
      <g class="hud-routes" fill="none" stroke="currentColor" stroke-width=".5">
        <path d="M0 690L190 540L420 610L650 430L920 520L1160 470" />
        <path d="M140 0L330 180L570 120L820 280L1100 170L1440 290" />
        <path d="M0 250L240 320L470 210L720 300L980 180L1440 230" />
      </g>
      <g class="hud-points" fill="currentColor">
        <circle cx="190" cy="540" r="2" /><circle cx="420" cy="610" r="2" /><circle cx="650" cy="430" r="2" />
        <circle cx="920" cy="520" r="2" /><circle cx="1160" cy="470" r="3" /><circle cx="820" cy="280" r="2" />
      </g>
    </svg>
    <span class="hud-symbol symbol-cross cross-a">+</span>
    <span class="hud-symbol symbol-cross cross-b">+</span>
    <span class="hud-symbol symbol-cross cross-c">+</span>
    <span class="hud-symbol symbol-cross cross-d">+</span>
    <span class="hud-symbol symbol-line line-a" />
    <span class="hud-symbol symbol-line line-b" />
    <span class="hud-symbol symbol-square square-a" />
    <span class="hud-symbol symbol-dot dot-a" />
    <span class="hud-symbol symbol-dot dot-b" />
    <span class="hud-symbol symbol-triangle triangle-a" />
    <span class="hud-symbol symbol-triangle triangle-b" />
  </div>
</template>

<style scoped>
.dashboard-hud { color: color-mix(in srgb, var(--brand) 45%, transparent); }
.hud-grid { position: absolute; inset: 0; opacity: .06; background-image: repeating-linear-gradient(135deg, transparent 0 72px, var(--text-secondary) 73px, transparent 74px); }
.hud-glow { position: absolute; inset: 8% 12%; opacity: .2; background: radial-gradient(ellipse at 70% 45%, color-mix(in srgb, var(--brand) 10%, transparent), transparent 58%); }
.hud-radar { opacity: .12; }
.hud-crosshair { color: var(--text-secondary); opacity: .55; }
.hud-rings { color: var(--text-secondary); opacity: .75; animation: radar-breathe 14s ease-in-out infinite; transform-origin: 80% 52%; }
.hud-routes { color: var(--brand); opacity: .42; animation: route-drift 22s ease-in-out infinite; }
.hud-points { color: var(--brand); opacity: .8; }
.hud-symbol { position: absolute; display: block; color: var(--brand); opacity: .45; animation: symbol-float 8s ease-in-out infinite; }
.symbol-cross { font: 16px Georgia, serif; }
.symbol-line { width: 20px; height: 1px; background: currentColor; }
.symbol-square { width: 7px; height: 7px; border: 1px solid currentColor; }
.symbol-dot { width: 4px; height: 4px; border-radius: 50%; background: currentColor; box-shadow: 0 0 8px currentColor; }
.symbol-triangle { width: 0; height: 0; border-left: 7px solid transparent; border-right: 7px solid transparent; border-bottom: 12px solid currentColor; }
.cross-a { left: 12%; top: 24%; }.cross-b { left: 34%; top: 72%; animation-delay: -2s; }.cross-c { right: 20%; top: 32%; animation-delay: -4s; }.cross-d { right: 8%; bottom: 18%; animation-delay: -6s; }
.line-a { left: 22%; top: 47%; transform: rotate(25deg); }.line-b { right: 28%; bottom: 30%; transform: rotate(-35deg); animation-delay: -3s; }
.square-a { left: 67%; top: 22%; animation-delay: -1s; }.dot-a { left: 82%; top: 58%; animation-delay: -4s; }.dot-b { left: 18%; bottom: 16%; animation-delay: -6s; }.triangle-a { left: 9%; bottom: 30%; transform: rotate(28deg); animation-delay: -2s; }.triangle-b { right: 14%; top: 12%; transform: rotate(90deg); animation-delay: -5s; }
@keyframes radar-breathe { 50% { opacity: .7; transform: scale(1.015); } }
@keyframes route-drift { 50% { transform: translate(5px, -4px); opacity: .7; } }
@keyframes symbol-float { 50% { opacity: .75; transform: translateY(-5px); } }
</style>
