<script setup lang="ts">
const props=defineProps<{replace?:boolean}>()
const shell=ref<HTMLElement|null>(null)
let contentObserver:ResizeObserver|undefined
let contentMotion:Animation|undefined
let panelMotion:Animation|undefined
let panelVersion=0
// 异步列表与分页改变高度时，卡片继续平滑伸缩。
function followContent(node:HTMLElement){
  contentObserver?.disconnect()
  if(!props.replace||!shell.value)return
  let previous=node.getBoundingClientRect().height
  contentObserver=new ResizeObserver(()=>{
    const height=node.getBoundingClientRect().height,wrapper=shell.value
    if(!wrapper||Math.abs(height-previous)<1)return
    // 自然布局已变更时仍从上一帧高度起步，避免先跳到终点。
    const start=contentMotion?wrapper.getBoundingClientRect().height:previous
    previous=height
    contentMotion?.cancel()
    if(window.matchMedia('(prefers-reduced-motion: reduce)').matches){wrapper.style.height='';wrapper.style.overflow='';return}
    wrapper.style.height=start+'px';wrapper.style.overflow='hidden'
    const motion=wrapper.animate([{height:start+'px'},{height:height+'px'}],{duration:420,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'})
    contentMotion=motion
    motion.onfinish=()=>{if(contentMotion!==motion)return;motion.cancel();contentMotion=undefined;wrapper.style.height='';wrapper.style.overflow=''}
  })
  contentObserver.observe(node)
}
onMounted(()=>{const node=shell.value?.firstElementChild;if(node instanceof HTMLElement)followContent(node)})
onUnmounted(()=>{panelVersion++;contentObserver?.disconnect();contentMotion?.cancel();panelMotion?.cancel()})
// 高度参与布局，让卡片随内容展开和收起。
function animate(element: Element, done: () => void, entering: boolean) {
  const node = element as HTMLElement
  if (window.matchMedia('(prefers-reduced-motion: reduce)').matches) { done(); return }
  node.style.overflow = 'hidden'
  const height = node.getBoundingClientRect().height || node.scrollHeight
  if(props.replace&&shell.value){
    // 切换面板保留旧高度，再缓缓伸缩到新内容高度。
    const wrapper=shell.value
    const previous=wrapper.getBoundingClientRect().height
    // 快速切换时取消旧高度动画，防止回调覆盖新卡片。
    const version=++panelVersion
    panelMotion?.cancel()
    contentObserver?.disconnect();contentMotion?.cancel();contentMotion=undefined
    wrapper.style.height=previous+'px';wrapper.style.overflow='hidden'
    if(entering){
      const resize=wrapper.animate([{height:previous+'px'},{height:height+'px'}],{duration:650,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'})
      panelMotion=resize
      const reveal=node.animate([{opacity:0,transform:'translateY(10px)'},{opacity:1,transform:'none'}],{duration:520,easing:'ease-out'})
      const finish=()=>{if(version!==panelVersion)return;resize.cancel();contentMotion?.cancel();contentMotion=undefined;wrapper.style.height='';wrapper.style.overflow='';node.style.overflow='';followContent(node);done()}
      resize.onfinish=()=>{
        if(version!==panelVersion)return
        // 首段动画结束时重新测量，避免加载完成后高度跳变。
        const actual=node.getBoundingClientRect().height
        if(Math.abs(actual-height)<1){finish();return}
        wrapper.style.height=height+'px';resize.cancel()
        contentMotion=wrapper.animate([{height:height+'px'},{height:actual+'px'}],{duration:420,easing:'cubic-bezier(.4,0,.2,1)',fill:'forwards'})
        contentMotion.onfinish=finish
      }
      reveal.onfinish=()=>reveal.cancel()
    }else{
      const fade=node.animate([{opacity:1},{opacity:0}],{duration:180,easing:'ease-in'})
      panelMotion=fade
      fade.onfinish=()=>{node.style.overflow='';done()}
    }
    return
  }
  const frames = entering
    ? [{ height: '0px', opacity: 0, transform: 'translateY(8px)' }, { height: height + 'px', opacity: 1, transform: 'translateY(0)' }]
    : [{ height: height + 'px', opacity: 1 }, { height: '0px', opacity: 0 }]
  const animation = node.animate(frames, { duration: entering ? 650 : 360, easing: 'cubic-bezier(.4,0,.2,1)' })
  const finish = () => { node.style.overflow = ''; done() }
  animation.onfinish = finish
  animation.oncancel = finish
}
</script>

<template>
  <div ref="shell" class="min-w-0"><Transition :css="false" mode="out-in" @enter="(el, done) => animate(el, done, true)" @leave="(el, done) => animate(el, done, false)">
    <slot />
  </Transition></div>
</template>
