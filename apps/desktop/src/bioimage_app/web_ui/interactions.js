'use strict';
(() => {
  const art=document.querySelector('.home-art');
  let frame=0,point=null;
  art?.addEventListener('pointermove',event=>{
    if(uiMotion.preference()!=='expressive'||event.pointerType==='touch')return;
    const box=art.getBoundingClientRect();point={x:(event.clientX-box.left)/box.width-.5,y:(event.clientY-box.top)/box.height-.5};
    if(frame)return;frame=requestAnimationFrame(()=>{frame=0;if(!point)return;art.querySelector('.home-paper').style.transform=`translate(${point.x*4}px,${-3+point.y*2}px) rotateX(${-point.y*4}deg) rotateY(${point.x*4}deg)`;});
  });
  art?.addEventListener('pointerleave',()=>{point=null;cancelAnimationFrame(frame);frame=0;art.querySelector('.home-paper').style.transform='';});
  const tool=document.querySelector('.installed-tool');
  let toolFrame=0;
  tool?.addEventListener('pointermove',event=>{
    if(uiMotion.preference()!=='expressive'||event.pointerType==='touch')return;
    const box=tool.getBoundingClientRect(),x=(event.clientX-box.left)/box.width-.5,y=(event.clientY-box.top)/box.height-.5;
    cancelAnimationFrame(toolFrame);toolFrame=requestAnimationFrame(()=>{tool.style.setProperty('--pointer-x',x*8+'px');tool.style.setProperty('--pointer-y',y*8+'px');});
  });
  tool?.addEventListener('pointerleave',()=>{cancelAnimationFrame(toolFrame);tool.style.removeProperty('--pointer-x');tool.style.removeProperty('--pointer-y');});
  const positions=new Map();
  const originalSwitch=switchMode;
  const scrollNodes=()=>document.querySelectorAll('#source-list,#intake-workspace,.intake-measure-main,.results-scroll,#quant-profile,.inspector-content,.intake-figure-curves-scroll');
  switchMode=function(next){
    if(next!==mode)positions.set(mode,[...scrollNodes()].map(el=>({key:el.id?'#'+el.id:'.'+el.classList[0],x:el.scrollLeft,y:el.scrollTop})));
    const previous=mode;originalSwitch(next);
    if(previous!==mode){const requested=mode;requestAnimationFrame(()=>{if(requested!==mode)return;for(const item of positions.get(mode)||[]){const el=document.querySelector(item.key);if(el){el.scrollLeft=item.x;el.scrollTop=item.y;}}});}
  };
  let layoutRequest=null;
  function collapseTools(hidden){document.body.classList.toggle('tools-collapsed',hidden);document.querySelector('.workspace').classList.toggle('tools-collapsed',hidden);const b=document.querySelector('[data-ui-collapse]');b?.setAttribute('aria-pressed',String(hidden));b?.setAttribute('aria-label',hidden?'展开工具区':'收起工具区');}
  window.workbenchLayout={receive(value){if(!value||(layoutRequest&&value.receipt!==layoutRequest))return;layoutRequest=null;collapseTools(value.collapsed);if(value.error)toast(value.error);}};
  document.addEventListener('click',event=>{
    const collapse=event.target.closest('[data-ui-collapse]');
    if(collapse){const hidden=!document.querySelector('.workspace').classList.contains('tools-collapsed');collapseTools(hidden);layoutRequest='layout-'+Date.now();if(!window.desktopSession?.request('tools_layout',{requestId:layoutRequest,collapsed:hidden})){layoutRequest=null;try{localStorage.setItem('bioimage-tools-collapsed',String(hidden));}catch{toast('工具区设置无法保存');}}return;}
    const summary=event.target.closest('summary');
    const details=summary?.parentElement;
    if(!details?.matches('.quality-details,.sequence-source-meta,.session-secondary,.inspect-section details'))return;
    event.preventDefault();
    const start=details.getBoundingClientRect().height;
    const opening=details.dataset.transitioning?details.dataset.transitioning==='closing':!details.open;
    uiMotion.cancel(details);details.open=true;details.style.height='';details.style.overflow='';
    const end=opening?details.getBoundingClientRect().height:summary.getBoundingClientRect().height;
    details.dataset.transitioning=opening?'opening':'closing';details.style.overflow='hidden';
    uiMotion.run(details,[{height:start+'px'},{height:end+'px'}],220,()=>{details.open=opening;details.style.overflow='';delete details.dataset.transitioning;});
  });
  try{collapseTools(window.__wbBootstrap?window.__wbBootstrap.toolsCollapsed:localStorage.getItem('bioimage-tools-collapsed')==='true');}catch{}
  // Native titles stay available; explicit info buttons supply identical keyboard/click access.
  const preview=document.createElement('div');preview.className='quick-preview';preview.hidden=true;preview.id='quick-preview';preview.setAttribute('role','tooltip');document.body.append(preview);
  let previewTimer=0,previewTarget=null;
  function hidePreview(){clearTimeout(previewTimer);preview.hidden=true;previewTarget?.removeAttribute('aria-describedby');previewTarget=null;}
  function showPreview(button){if(!button.isConnected)return;previewTarget=button;preview.textContent=(button.dataset.quickInfo||button.dataset.previewInfo);preview.hidden=false;button.setAttribute('aria-describedby',preview.id);const rect=button.getBoundingClientRect();preview.style.left=Math.max(16,Math.min(innerWidth-preview.offsetWidth-16,rect.left))+'px';preview.style.top=Math.max(16,Math.min(innerHeight-preview.offsetHeight-16,rect.bottom+8))+'px';uiMotion.enter(preview);}
  document.addEventListener('pointerover',event=>{const b=event.target.closest('[data-quick-info],[data-preview-info]');if(!b||b===previewTarget)return;hidePreview();previewTimer=setTimeout(()=>showPreview(b),350);});
  document.addEventListener('pointerout',event=>{if(event.target.closest('[data-quick-info],[data-preview-info]')&&!event.relatedTarget?.closest?.('[data-quick-info],[data-preview-info]'))hidePreview();});
  document.addEventListener('focusin',event=>{const b=event.target.closest('[data-quick-info],[data-preview-info]');if(b){hidePreview();showPreview(b);}});
  document.addEventListener('focusout',hidePreview);
  document.addEventListener('click',event=>{const b=event.target.closest('[data-quick-info]');if(!b)return;hidePreview();openDrawer(b.closest('.session-recent-wrap')?'项目详情':'来源详情',`<div class="drawer-copy"><p>${escapeText(b.dataset.quickInfo)}</p></div>`);});
  document.addEventListener('keydown',event=>{if(event.key==='Escape')hidePreview();});
  document.addEventListener('scroll',hidePreview,true);
  let infoFrame=0;
  function attachInfo(){infoFrame=0;document.querySelectorAll('.sequence-source-caption:not([data-info-ready]),.intake-object-group>h3:not([data-info-ready])').forEach(el=>{el.dataset.infoReady='true';const text=el.getAttribute('title')||el.querySelector('[title]')?.getAttribute('title')||(el.tagName==='H3'?el.textContent.trim()+' · '+[...el.parentElement.querySelectorAll('.source-copy strong')].map(s=>s.textContent).join('、'):el.textContent.trim());if(!text)return;const b=document.createElement('button');b.className='icon-button quick-info-button';b.dataset.quickInfo=text;b.setAttribute('aria-label','查看来源：'+text);b.innerHTML=icon('file');el.append(b);});}
  const observer=new MutationObserver(()=>{if(!infoFrame)infoFrame=requestAnimationFrame(attachInfo);});observer.observe(document.querySelector('#work-view'),{childList:true,subtree:true});
  window.addEventListener('pagehide',()=>{observer.disconnect();cancelAnimationFrame(infoFrame);cancelAnimationFrame(frame);cancelAnimationFrame(toolFrame);hidePreview();});
})();
