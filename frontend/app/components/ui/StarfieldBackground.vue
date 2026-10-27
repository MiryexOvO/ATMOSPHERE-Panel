<template>
  <div class="fixed inset-0 z-[-1] pointer-events-none overflow-hidden bg-background" aria-hidden="true">
    <div class="absolute inset-0 bg-[radial-gradient(circle_at_center,color-mix(in_srgb,var(--brand)_12%,transparent),transparent_55%)] opacity-70" />
    <svg class="absolute inset-0 h-full w-full opacity-30" viewBox="0 0 1200 800" preserveAspectRatio="none">
      <g fill="none" stroke="currentColor" stroke-width=".6" class="text-brand constellation-line">
        <path d="M80 160 L210 90 L360 180 L520 120 L690 230" />
        <path d="M760 80 L840 210 L1010 150 L1130 280" />
        <path d="M120 610 L290 520 L430 650 L610 560 L790 690" />
        <path d="M850 520 L960 430 L1100 570 L1180 470" />
      </g>
    </svg>
    <i v-for="n in 9" :key="n" :class="'star-cross cross-' + n">+</i>
    <b v-for="n in 28" :key="'dot-' + n" :class="'star-dot dot-' + n"></b>
  </div>
</template>
<style scoped>
.star-cross{position:absolute;color:var(--brand);font:14px Georgia,serif;opacity:.4;animation:star-breathe 4s ease-in-out infinite}.star-dot{position:absolute;width:3px;height:3px;border-radius:50%;background:var(--text-secondary);opacity:.55;animation:dot-flicker 5s ease-in-out infinite}.constellation-line{animation:line-drift 24s ease-in-out infinite}.cross-1{left:8%;top:18%}.cross-2{left:26%;top:11%;animation-delay:-1s}.cross-3{left:48%;top:25%;animation-delay:-2s}.cross-4{left:71%;top:14%;animation-delay:-3s}.cross-5{left:91%;top:28%;animation-delay:-.5s}.cross-6{left:18%;top:76%;animation-delay:-2.5s}.cross-7{left:42%;top:68%;animation-delay:-1.5s}.cross-8{left:68%;top:82%;animation-delay:-3.5s}.cross-9{left:88%;top:72%;animation-delay:-4s}.dot-1{left:4%;top:9%}.dot-2{left:13%;top:33%}.dot-3{left:21%;top:17%}.dot-4{left:34%;top:42%}.dot-5{left:43%;top:8%}.dot-6{left:57%;top:31%}.dot-7{left:66%;top:18%}.dot-8{left:78%;top:39%}.dot-9{left:94%;top:12%}.dot-10{left:9%;top:57%}.dot-11{left:27%;top:65%}.dot-12{left:39%;top:78%}.dot-13{left:53%;top:58%}.dot-14{left:62%;top:91%}.dot-15{left:74%;top:67%}.dot-16{left:86%;top:84%}.dot-17{left:97%;top:59%}.dot-18{left:16%;top:92%}.dot-19{left:31%;top:28%}.dot-20{left:47%;top:49%}.dot-21{left:59%;top:72%}.dot-22{left:72%;top:6%}.dot-23{left:82%;top:54%}.dot-24{left:90%;top:91%}.dot-25{left:3%;top:82%}.dot-26{left:37%;top:93%}.dot-27{left:69%;top:47%}.dot-28{left:99%;top:35%}@keyframes star-breathe{50%{opacity:.9;transform:scale(1.2)}}@keyframes dot-flicker{50%{opacity:.18;transform:scale(.7)}}@keyframes line-drift{50%{transform:translate(8px,-5px);opacity:.55}}
</style>