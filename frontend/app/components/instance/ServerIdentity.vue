<script setup lang="ts">
const props=defineProps<{instanceId:string;running:boolean}>()
const tr=usePanelText(),{request,getErrorMessage}=useApi()
const canvas=ref<HTMLCanvasElement|null>(null),image=shallowRef<HTMLImageElement|null>(null),zoom=ref(1),x=ref(0),y=ref(0),message=ref(''),busy=ref(false),stamp=ref(0)
let objectUrl=''
// 方形取景框缩放、平移后生成标准图标。
function draw(){const context=canvas.value?.getContext('2d'),img=image.value;if(!context||!img)return;const side=Math.min(img.width,img.height)/zoom.value;const left=(img.width-side)*(x.value+100)/200;const top=(img.height-side)*(y.value+100)/200;context.clearRect(0,0,256,256);context.drawImage(img,left,top,side,side,0,0,256,256)}
function choose(event:Event){const file=(event.target as HTMLInputElement).files?.[0];if(!file)return;if(!['image/jpeg','image/png'].includes(file.type)||file.size>10*1048576){message.value=tr('请选择小于 10 MB 的 JPG / PNG','Choose JPG / PNG under 10 MB','10 MB 以下の JPG / PNG を選択');return}if(objectUrl)URL.revokeObjectURL(objectUrl);objectUrl=URL.createObjectURL(file);const img=new Image();img.onload=()=>{image.value=img;zoom.value=1;x.value=y.value=0;nextTick(draw)};img.onerror=()=>{message.value=tr('无法读取图片','Unable to read image','画像を読み込めません')};img.src=objectUrl}
watch([zoom,x,y],draw)
async function save(){if(!image.value||!canvas.value)return;busy.value=true;try{const output=document.createElement('canvas');output.width=output.height=64;output.getContext('2d')!.drawImage(canvas.value,0,0,64,64);const blob=await new Promise<Blob|null>(resolve=>output.toBlob(resolve,'image/png'));if(!blob)throw Error('PNG encoding failed');const form=new FormData();form.append('file',blob,'server-icon.png');await request(`/api/instances/${encodeURIComponent(props.instanceId)}/icon`,{method:'POST',body:form});stamp.value=Date.now();message.value=tr('图标已保存，启动后生效','Icon saved; takes effect on start','アイコンを保存しました。起動後に反映されます')}catch(error){message.value=getErrorMessage(error)}finally{busy.value=false}}
// 支持的浏览器直接流式写盘，避免整服压缩包占满内存。
async function exportServer(){
 busy.value=true;message.value=''
 let writer:any=null
 try{
  const picker=(window as any).showSaveFilePicker
  const handle=picker?await picker({suggestedName:props.instanceId+'-server.zip',types:[{description:'ZIP',accept:{'application/zip':['.zip']}}]}):null
  const response=await fetch(`/api/instances/${encodeURIComponent(props.instanceId)}/export`)
  if(!response.ok){const data=await response.json();throw Error(data.detail||data.message||response.statusText)}
  if(handle&&response.body){
   writer=await handle.createWritable();const reader=response.body.getReader();let bytes=0
   try{while(true){const {done,value}=await reader.read();if(done)break;await writer.write(value);bytes+=value.byteLength;message.value=tr('正在导出 ','EXPORTING ','エクスポート中 ')+(bytes/1048576).toFixed(1)+' MB'}}finally{reader.releaseLock()}
   await writer.close();writer=null;message.value=tr('服务端已导出','Server exported','エクスポート完了')
  }else{
   const url=URL.createObjectURL(await response.blob()),link=document.createElement('a');link.href=url;link.download=props.instanceId+'-server.zip';link.click();setTimeout(()=>URL.revokeObjectURL(url),60000)
  }
 }catch(error){if(writer)await writer.abort().catch(()=>{});if((error as Error).name!=='AbortError')message.value=getErrorMessage(error)}finally{busy.value=false}
}
onUnmounted(()=>{if(objectUrl)URL.revokeObjectURL(objectUrl)})
</script>
<template><section class="space-y-5 border-t border-border pt-6"><h3 class="font-serif text-lg">{{tr('服务器图标与导出','SERVER ICON & EXPORT','サーバーアイコンとエクスポート')}}</h3><div class="flex flex-wrap items-center gap-5"><img :key="stamp" :src="`/api/instances/${encodeURIComponent(instanceId)}/icon?v=${stamp}`" width="64" height="64" alt="SERVER ICON" class="border border-border [image-rendering:pixelated]" @error="($event.target as HTMLImageElement).style.visibility='hidden'"/><label class="cursor-pointer border border-border px-4 py-3 text-xs text-brand">{{tr('选择 JPG / PNG','CHOOSE JPG / PNG','JPG / PNG を選択')}}<input type="file" accept="image/png,image/jpeg" class="hidden" :disabled="running||busy" @change="choose"/></label><button type="button" :disabled="running||busy" class="border border-border px-4 py-3 text-xs text-brand disabled:opacity-40" @click="exportServer">{{busy?tr('处理中…','PROCESSING…','処理中…'):tr('导出完整服务端','EXPORT FULL SERVER','サーバー全体をエクスポート')}}</button></div><p class="text-xs leading-6 text-text-secondary">{{tr('停服后操作。导出包含世界存档、插件、MODS、配置文件与核心。','Stop the server first. Export includes worlds, plugins, mods, configuration and core.','停止後に操作してください。ワールド、プラグイン、MOD、設定、コアを含みます。')}}</p><div v-if="image" class="grid max-w-xl gap-5 sm:grid-cols-2"><canvas ref="canvas" width="256" height="256" class="w-full border border-brand"/><div class="space-y-4"><label class="block text-xs">{{tr('缩放','ZOOM','拡大')}}<input v-model.number="zoom" type="range" min="1" max="4" step=".01" class="mt-2 block w-full accent-brand"/></label><label class="block text-xs">X<input v-model.number="x" type="range" min="-100" max="100" class="mt-2 block w-full accent-brand"/></label><label class="block text-xs">Y<input v-model.number="y" type="range" min="-100" max="100" class="mt-2 block w-full accent-brand"/></label><button type="button" :disabled="running||busy" class="border border-brand px-4 py-2 text-xs text-brand" @click="save">{{tr('保存裁剪 · 64×64','SAVE CROP · 64×64','切り抜きを保存 · 64×64')}}</button></div></div><p v-if="message" role="status" class="text-sm text-brand">{{message}}</p></section></template>
