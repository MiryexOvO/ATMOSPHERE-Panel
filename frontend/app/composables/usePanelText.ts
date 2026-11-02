// 管理模块共用三语文本选择。
export function usePanelText(){
 const {locale}=useI18n()
 return (zh:string,en:string,ja:string)=>locale.value==='en'?en:locale.value==='ja'?ja:zh
}
