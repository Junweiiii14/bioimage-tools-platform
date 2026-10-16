'use strict';
const $ = (s, root = document) => root.querySelector(s);
const $$ = (s, root = document) => [...root.querySelectorAll(s)];
const paths = {
  grid:'M3 3h7v7H3zM14 3h7v7h-7zM3 14h7v7H3zM14 14h7v7h-7z',
  lanes:'M4 5h16v14H4zM8 8v8M12 8v8M16 8v8',
  help:'M9 9a3 3 0 0 1 6 0c0 2-3 2-3 4M12 17h.01M22 12a10 10 0 1 1-20 0 10 10 0 0 1 20 0Z',
  settings:'m9 3-1 3-3 1-2 3 2 3 1 3 3 1 3 2 3-2 3-1 1-3 2-3-2-3-3-1-1-3H9ZM15 11a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z',
  chevron:'m9 5 7 7-7 7', 'chevron-down':'m6 9 6 6 6-6',check:'m5 12 4 4L19 6',plus:'M12 5v14M5 12h14',minus:'M5 12h14',
  download:'M12 3v12m-5-5 5 5 5-5M4 16v5h16v-5',upload:'M12 16V3m-5 5 5-5 5 5M4 16v5h16v-5',arrow:'M4 12h15m-6-6 6 6-6 6',
  folder:'M3 6h7l2 3h9v11H3V6Z',scan:'M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5M7 8h10v8H7z',layout:'M3 3h18v18H3zM3 9h18M9 9v12',table:'M3 3h18v18H3zM3 9h18M3 15h18M9 3v18',sliders:'M4 7h16M4 17h16M8 4v6M16 14v6',search:'M10 17a7 7 0 1 1 0-14 7 7 0 0 1 0 14Zm5-2 6 6',shield:'m12 3 8 3v6c0 5-8 9-8 9S4 17 4 12V6l8-3Zm-4 9 3 3 5-6',undo:'M4 10h10a6 6 0 0 1 0 12M4 10l5-5M4 10l5 5',redo:'M20 10H10a6 6 0 0 0 0 12m16-12-5-5m5 5-5 5',focus:'M8 3H3v5M16 3h5v5M3 16v5h5M21 16v5h-5M8 12h8M12 8v8',expand:'M3 9V3h6M15 3h6v6M21 15v6h-6M9 21H3v-6',image:'M3 3h18v18H3zM3 17l6-6 4 4 3-3 5 5M15 7h.01',mouse:'M12 3a6 6 0 0 0-6 6v6a6 6 0 0 0 12 0V9a6 6 0 0 0-6-6ZM12 3v6',layers:'m12 3 10 6-10 6L2 9l10-6ZM2 13l10 6 10-6M2 17l10 6 10-6',close:'m6 6 12 12M6 18 18 6',warning:'m12 3 10 18H2L12 3ZM12 9v5m0 3h.01',spark:'M12 2v4m0 12v4M2 12h4m12 0h4M5 5l3 3m8 8 3 3M5 19l3-3m8-8 3-3',file:'M5 3h9l5 5v13H5V3Zm9 0v6h5M8 13h8M8 17h6',curve:'M3 19h18M3 19V3M4 16c4 0 3-10 7-10s2 10 10 10',eye:'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm13 0a3 3 0 1 1-6 0 3 3 0 0 1 6 0Z'
};
function icon(name){return `<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.6" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="${paths[name] || paths.file}"/></svg>`;}
function icons(root=document){$$('[data-icon]',root).forEach(el=>{el.innerHTML=icon(el.dataset.icon);});}
function escapeText(value){return String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));}
const number = value => value == null ? '—' : Number(value).toLocaleString('en-US',{maximumFractionDigits:2});
let state={projectName:'新建实验项目',rows:[],cells:[],selectedId:null,busy:false,status:'就绪',outputPath:'',montage:null};
let bridge=null, mode='review',filter='all',search='',zoom=1,focusCrop=true,overlay=true,selectedCell=null;
let demoOriginal=null,undoStack=[],redoStack=[],imageKey='',toastTimer,drag=null,drawerTrigger=null;
let reduced=localStorage.getItem('bioimage-reduced-motion')==='true';
document.body.classList.toggle('reduce-motion',reduced);
const needsAttention=r=>!r.reviewed||r.status!=='valid';
const row=()=>state.rows.find(r=>r.id===state.selectedId)||state.rows[0];
const send=(action,payload={})=>bridge&&bridge.request(action,JSON.stringify(payload));
function toast(message){$('#toast').textContent=message;$('#toast').classList.add('visible');clearTimeout(toastTimer);toastTimer=setTimeout(()=>$('#toast').classList.remove('visible'),3500);}
function statusLabel(status){return ({quality_review:'质量待复核',needs_review:'待复核',unreviewed:'待复核',valid:'有效',ok:'有效',excluded:'已排除',result_unavailable:'结果不可用',missing:'未完成',pending:'待计算',stale:'已修改，待重算'})[status]||'待复核';}
function setState(next){const oldId=state.selectedId;state={...state,...next};if(!state.selectedId&&state.rows.length)state.selectedId=state.rows.find(r=>r.roi)?.id||state.rows[0].id;if(oldId!==state.selectedId){focusCrop=true;zoom=1;}render();}
function render(){
  $('#project-name').textContent=state.projectName;$('#source-count').textContent=state.rows.length;$('#attention-count').textContent=state.rows.filter(needsAttention).length;
  $('#operation-status').textContent=state.status||'就绪';$('#status-dot').classList.toggle('busy',!!state.busy);$('#cancel-button').hidden=!state.busy;
  $('#save-status').innerHTML=icon(state.busy?'curve':'check')+(state.busy?'处理中':bridge?'已就绪':'预览草稿');
  $('#runtime-badge').textContent=bridge?'桌面工作台':'网页预览';$('#status-right').textContent=bridge?'本地工作空间 · 原图保留':'交互预览 · 不执行新的科学计算';
  $$('[data-action="confirm"], [data-action="reanalyze"]').forEach(b=>b.disabled=state.busy||!row());
  renderSources();renderCanvas();renderInspector();if(mode==='results')renderResults();
  const first=state.rows.find(r=>r.preview&&r.roi)||state.rows.find(r=>r.preview);
  if(first){$('#home-image').src=state.montage||first.preview;$('#recent-image').src=first.preview;$('#recent-name').textContent=state.projectName;$('#recent-description').textContent=`${state.rows.length} 张原图 · ${state.rows.filter(r=>r.roi).length} 张已有自动裁剪 · 待复核记录`;}
}
function renderSources(){
  const filtered=state.rows.filter(r=>(filter!=='attention'||needsAttention(r))&&r.name.toLowerCase().includes(search.toLowerCase()));
  $('#source-list').innerHTML=filtered.map((r,index)=>`<button class="source-item ${r.id===state.selectedId?'active':''}" data-row="${escapeText(r.id)}" aria-pressed="${r.id===state.selectedId}" title="${escapeText(r.name)}"><img class="source-thumb" src="${r.preview||''}" alt="" ${r.preview?'':'hidden'}><span class="source-copy"><strong>${escapeText(r.fig||`图 ${index+1}`)} · ${escapeText(r.name)}</strong><small class="${r.reviewed?'reviewed':''}">${r.reviewed?'裁剪已确认':r.roi?'自动结果 · 待复核':'未检出 · 待定位'}</small></span></button>`).join('')||'<p class="empty-list">'+(state.rows.length?'没有符合条件的原图。':'导入原图后，所有来源会显示在这里。')+'</p>';
}
function renderCanvas(){
 const r=row();$('#image-stage').hidden=mode==='results';$('#result-stage').hidden=mode!=='results';
 $('#image-title').textContent=mode==='results'?'测量结果':mode==='layout'?'当前拼图':r?.name||'选择一张原图';
 $('#image-subtitle').textContent=mode==='results'?`${state.rows.length} 张原图 · 有效信号与待复核积分独立呈现`:mode==='layout'?'原图裁剪的组合预览 · 显示变换不进入定量':r?`${r.width} × ${r.height} px  ·  ${r.bitDepth||'原始'} 位  ·  ${r.lanes} 个泳道`:'查看自动识别结果，在图上完成调整';
 $('#stage-label').textContent=mode==='layout'?'拼图预览':focusCrop?'原图 · 聚焦裁剪区域':'原始图像';
 $('#canvas-hint').textContent=mode==='results'?'选择结果查看完整原因':mode==='layout'?'当前已生成拼图 · 修改版式请打开模板工具':'拖动边框调整裁剪 · 滚轮缩放 · 方向键微调';
 $('.image-actions').hidden=mode==='results';$('#overlay-toggle').hidden=mode!=='review';
 const src=mode==='layout'?state.montage:r?.preview;
 $('#empty-image').hidden=!!src;$('#image-transform').hidden=!src;
 if(!src){$('#crop-overlay').hidden=true;return;}
 if(imageKey!==src){imageKey=src;$('#source-image').src=src;}
 requestAnimationFrame(fitImage);
}
function fitImage(){
 const img=$('#source-image'),vp=$('#image-viewport'),r=row();if(!img.naturalWidth||!vp.clientWidth)return;
 const scale=Math.min(vp.clientWidth/img.naturalWidth,vp.clientHeight/img.naturalHeight),w=img.naturalWidth*scale,h=img.naturalHeight*scale;
 const target=$('#image-transform');target.style.width=w+'px';target.style.height=h+'px';let actualZoom=zoom,tx=0,ty=0;
 if(mode==='review'&&focusCrop&&r?.roi){const roi=r.roi;actualZoom=zoom*Math.min(6,Math.max(1,.76*vp.clientWidth/(roi.width/r.width*w)));tx=(.5-(roi.x+roi.width/2)/r.width)*w*actualZoom;ty=(.5-(roi.y+roi.height/2)/r.height)*h*actualZoom;}
 target.style.transform=`translate(${tx}px,${ty}px) scale(${actualZoom})`;$('#zoom-label').textContent=zoom===1?(focusCrop&&r?.roi?'聚焦泳道':'适应窗口'):Math.round(zoom*100)+'%';
 const crop=$('#crop-overlay');crop.hidden=mode!=='review'||!r?.roi||!overlay;
 if(!crop.hidden){const b=r.roi;crop.style.left=b.x/r.width*100+'%';crop.style.top=b.y/r.height*100+'%';crop.style.width=b.width/r.width*100+'%';crop.style.height=b.height/r.height*100+'%';crop.style.borderWidth=(1.5/actualZoom)+'px';$('.crop-tag').textContent=r.reviewed?'裁剪已确认':r.draft?'调整草稿':'自动建议';$('.crop-tag').style.transform=`scale(${1/actualZoom})`;$('.crop-tag').style.transformOrigin='left bottom';$$('.crop-handle').forEach(el=>el.style.transform=`scale(${1/actualZoom})`);$('#lane-lines').innerHTML=Array.from({length:r.lanes},(_,i)=>`<span class="lane-number" style="left:${(i+.5)/r.lanes*100}%;transform:translateX(-50%) scale(${1/actualZoom});transform-origin:top">${i+1}</span>${i?`<span class="lane-line" style="left:${i/r.lanes*100}%"></span>`:''}`).join('');}
}
function dataPair(label,value){return `<div class="data-pair"><span>${label}</span><strong>${escapeText(value)}</strong></div>`;}
function renderInspector(){
 const r=row();$('#inspector-title').textContent=mode==='results'?'输出结果':mode==='layout'?'拼图设置':'当前原图';$('#review-badge').textContent=r?.reviewed&&mode==='review'?'裁剪已确认':'待复核';$('#review-badge').className='status-badge '+(r?.reviewed&&mode==='review'?'ok':'pending');
 const valid=state.cells.filter(c=>c.value!=null).length;
 let content='';
 if(mode==='results'){
  content=`<section class="inspect-section"><h3>本项目的结果</h3>${dataPair('原图数量',state.rows.length+' 张')}${dataPair('已有裁剪',state.rows.filter(r=>r.roi).length+' 张')}${dataPair('有效信号',valid+' 项')}${dataPair('待复核 / 未完成',state.cells.length-valid+' 项')}<p>结果项包含待定位占位，不等于检出泳道数量。</p></section><section class="inspect-section"><h3>${selectedCell?escapeText(selectedCell.fig)+' · 泳道 '+selectedCell.lane:'结果依据'}</h3><p class="row-reason">${escapeText(selectedCell?.reason||'选择左侧表格中的一项，查看原始积分、有效性与完整质量原因。')}</p>${selectedCell?dataPair('原始积分',number(selectedCell.rawIntegral)):''}</section><section class="inspect-section"><h3>本次会话输出</h3><p>${escapeText(state.outputPath?state.outputPath.split(/[\\/]/).pop():'尚未在本次会话导出')}</p><button class="text-button" data-action="open_output">${icon('folder')}打开结果文件夹</button></section>`;
 }else if(mode==='layout'){
  content=`<section class="inspect-section"><h3>排版预览</h3><p>预览由已有裁剪生成。未定位的原图不会被虚构为拼图内容。</p>${dataPair('可用图像',state.rows.filter(r=>r.roi).length+' 张')}${dataPair('标签', '保留原始项目标签')}</section><section class="inspect-section"><h3>模板与样式</h3><button class="button subtle full" data-action="advanced" data-section="template">${icon('sliders')}调整模板与分段</button><p style="margin-top:13px">${bridge?'完整模板编辑器在原生高级窗口中打开。':'网页展示已生成的拼图记录，模板修改在桌面版执行。'}</p></section><section class="inspect-section"><div class="layout-note">原图用于定量，拼图用于展示。两者的处理始终分开。</div><button class="text-button" data-action="compose">${icon('layout')}更新拼图预览</button></section>`;
 }else if(r){
  const cells=r.results||state.cells.filter(c=>c.rowId===r.id);
  content=`<section class="inspect-section"><h3>识别概览</h3>${dataPair('泳道',r.lanes+' 个')}${dataPair('裁剪',r.roi?`${r.roi.width} × ${r.roi.height} px`:'待定位')}${dataPair('蛋白',r.protein&&r.protein!=='Unassigned'?r.protein:'未指定')}</section><section class="inspect-section"><div class="signal-note"><h3>${icon('warning')}${r.roi?'有一项需要你关注':'尚未找到可靠裁剪'}</h3><p>${escapeText(r.reason||cells[0]?.reason||(r.roi?'自动识别是建议，请核对原图和边界。':'可在原图上指定裁剪范围，或重新自动识别。'))}</p></div><h3>泳道结果</h3><table class="lane-summary"><thead><tr><th>泳道</th><th>有效信号</th><th>原始积分</th></tr></thead><tbody>${cells.slice(0,8).map((c,i)=>`<tr><td>${c.lane||i+1}</td><td>${number(c.value)}</td><td>${number(c.rawIntegral)}</td></tr>`).join('')||'<tr><td colspan="3">尚无可用结果</td></tr>'}</tbody></table><p style="margin-top:12px">待复核原始积分不是有效信号。</p><button class="disclosure" data-action="advanced" data-section="analysis"><span>查看曲线与积分边界</span>${icon('chevron')}</button></section><section class="inspect-section"><button class="disclosure" data-action="advanced" data-section="metadata"><span>实验信息与泳道设置</span>${icon('chevron')}</button><button class="disclosure" data-action="reanalyze"><span>重新自动识别</span>${icon('scan')}</button>${r.draft&&!bridge?'<p class="draft-label">网页草稿已修改，未重新计算；原记录不变。</p>':''}</section>`;
 }else{content='<section class="inspect-section"><h3>等待原图</h3><p>原图导入后，这里显示当前对象、自动建议与具体复核原因。</p></section>';}
 $('#inspector-content').innerHTML=content;$('#inspector-action').innerHTML=mode==='review'?`<button class="button primary full" data-action="confirm" ${!r?.roi||state.busy?'disabled':''}>${icon('check')}确认裁剪，查看下一张${icon('arrow')}</button><small>裁剪确认不会消除质量警告</small>`:`<button class="button primary full" data-action="export" ${!state.rows.length||state.busy?'disabled':''}>${icon('download')}导出结果包</button><small>缺失与无效值保持空白</small>`;
}
function renderResults(){
 $('#results-body').innerHTML=state.cells.map((c,i)=>`<tr tabindex="0" data-cell="${i}" aria-label="${escapeText(c.fig)} 泳道 ${c.lane}，${statusLabel(c.status)}" class="${selectedCell===c?'selected':''}"><td>${escapeText(c.fig)}<small>${escapeText(c.protein==='Unassigned'?'未指定蛋白':c.protein||'未指定蛋白')}</small></td><td>${c.lane}</td><td>${number(c.value)}</td><td>${number(c.rawIntegral)}</td><td><span class="status-badge ${c.value!=null?'ok':'pending'}">${statusLabel(c.status)}</span></td></tr>`).join('')||'<tr><td colspan="5">尚无测量结果。导入原图后由桌面后台处理。</td></tr>';
 $('#result-count').textContent=`${state.cells.length} 个结果项（含待定位占位）`;
}
function switchMode(next){mode=next;$('#home-view').hidden=true;$('#work-view').hidden=false;$$('.mode-tab').forEach(b=>{b.classList.toggle('active',b.dataset.mode===mode);b.setAttribute('aria-selected',String(b.dataset.mode===mode));});const tab=$('.mode-tab.active');$('.mode-indicator').style.transform=`translateX(${tab.offsetLeft}px)`;$('.mode-indicator').style.width=tab.offsetWidth+'px';if(mode==='layout'&&bridge&&!state.montage)send('compose');selectedCell=null;zoom=1;render();}
function select(id){if(state.busy){toast('正在处理，请稍候或取消当前处理');return;}state.selectedId=id;focusCrop=true;zoom=1;if(bridge)send('select',{id});render();}
function openDrawer(title,content){drawerTrigger=document.activeElement;$('#drawer-title').textContent=title;$('#drawer-content').innerHTML=content;$('#drawer').classList.remove('closing');$('#drawer').hidden=false;$('#drawer-backdrop').hidden=false;$('.app-shell').inert=true;$('.platform-rail').inert=true;$('#drawer [data-action="close-drawer"]').focus();}
function closeDrawer(){if($('#drawer').hidden)return;$('#drawer').classList.add('closing');setTimeout(()=>{$('#drawer').hidden=true;$('#drawer-backdrop').hidden=true;$('.app-shell').inert=false;$('.platform-rail').inert=false;drawerTrigger?.focus();},reduced?0:150);}
function advanced(section){if(bridge){send('advanced',{section});toast('已打开完整高级编辑器');return;}openDrawer(({analysis:'曲线与积分',metadata:'实验信息',ocr:'OCR 识别与写表',normalization:'样本对应与归一化',template:'模板与分段'})[section]||'项目工具',`<div class="drawer-copy"><p>当前网页是可交互的视觉预览。此操作需要本地计算与项目存储。</p><h3>桌面端保留完整能力</h3><p>同源桌面工作台可以打开现有${({analysis:'曲线编辑',metadata:'批量信息',ocr:'OCR',normalization:'归一化',template:'模板'})[section]||''}高级窗口，结果仍使用同一项目和原始像素。</p><p>高级窗口尚未网页化，不会把未执行的操作显示为成功。</p></div>`);}
async function loadDemo(){
 closeDrawer();
 if(bridge){send('open_project');return;}
 if(demoOriginal){setState(structuredClone(demoOriginal));switchMode('review');return;}
 try{const res=await fetch('demo.json',{cache:'no-store'});if(!res.ok)throw new Error();const data=await res.json();demoOriginal=structuredClone(data);setState(data);switchMode('review');toast('已打开真实历史记录的交互预览；修改仅保留在网页草稿。');}catch{openDrawer('打开界面预览','<div class="drawer-copy"><p>此网页尚未加载本地预览资料。</p><p>请使用项目提供的预览启动器，或在桌面工作台中选择 WB 原图并开始。</p></div>');}
}
function commitCrop(next,before){const r=row();if(!r)return;if(bridge){send('crop',{id:r.id,sourceId:r.sourceId,roi:next});return;}undoStack.push({id:r.id,roi:before,reviewed:r.reviewed});redoStack=[];r.roi=next;r.reviewed=false;r.draft=true;r.results=(r.results||[]).map(c=>({...c,value:null,status:'stale',reason:'网页草稿已调整，未执行新测量。'}));state.cells=state.cells.map(c=>c.rowId===r.id?{...c,value:null,status:'stale',reason:'网页草稿已调整，未执行新测量。'}:c);state.status='网页草稿已调整；等待桌面重新计算';render();}
function undoRedo(redo){if(bridge){send(redo?'redo':'undo');return;}const from=redo?redoStack:undoStack,to=redo?undoStack:redoStack;if(!from.length){toast(redo?'没有可重做的调整':'没有可撤销的调整');return;}const item=from.pop(),r=state.rows.find(r=>r.id===item.id);to.push({id:r.id,roi:structuredClone(r.roi),reviewed:r.reviewed});r.roi=item.roi;r.reviewed=item.reviewed;select(r.id);toast(redo?'已重做裁剪调整':'已撤销裁剪调整');}
function showTools(){openDrawer('项目工具',`<p class="drawer-copy">围绕当前实验项目，按需进入完整编辑。</p>${[['metadata','file','批量实验信息','填写蛋白、样本信息与泳道设置'],['analysis','curve','积分曲线与边界','核对曲线，调整积分边界与基线'],['template','layout','模板与分段','管理版式、字体与实验室模板'],['ocr','scan','OCR 识别与写表','识别标签，明确关联到实验来源'],['normalization','table','样本对应与归一化','选择目标、参照与明确的样本关系']].map(([s,i,title,description])=>`<button class="tool-link" data-action="advanced" data-section="${s}">${icon(i)}<span><h3>${title}</h3><p>${description}</p></span></button>`).join('')}`);}
function exportAction(){if(bridge){send('export');return;}openDrawer('导出与历史记录',`<div class="drawer-copy"><p>网页修改是交互草稿，不执行科学重算，也不生成新的实验结果。</p><h3>查看原始测量记录</h3><p>可下载预览项目原有的测量表。此文件不包含本次网页调整。</p><button class="button primary" data-action="download-record" ${demoOriginal?'':'disabled'}>${icon('download')}下载历史测量记录 CSV</button></div>`);}
function downloadRecord(){const esc=v=>{let s=String(v??'');if(/^[=+\-@]/.test(s))s="'"+s;return '"'+s.replace(/"/g,'""')+'"';};const records=[['图组','蛋白','泳道','有效信号','原始积分','状态','原因'],...demoOriginal.cells.map(c=>[c.fig,c.protein,c.lane,c.value,c.rawIntegral,c.status,c.reason])];const url=URL.createObjectURL(new Blob(['\ufeff'+records.map(r=>r.map(esc).join(',')).join('\r\n')],{type:'text/csv;charset=utf-8'}));const a=document.createElement('a');a.href=url;a.download='WB-历史记录-未含网页调整.csv';a.click();setTimeout(()=>URL.revokeObjectURL(url),1000);toast('已下载原始历史记录，未包含网页草稿调整');}
function action(name,element){
 switch(name){
 case 'home':$('#home-view').hidden=false;$('#work-view').hidden=true;render();break;
 case 'workbench':switchMode('review');break;
 case 'demo':loadDemo();break;
 case 'import':case 'import_folder':case 'open_project':if(bridge)send(name);else openDrawer('从原图开始',`<div class="drawer-copy"><p>网页可以预览与调整交互草稿。真实 TIFF 导入、自动建项目与定量计算在同源桌面版执行。</p><button class="button primary" data-action="demo">打开真实资料预览${icon('arrow')}</button><h3>桌面中的操作</h3><p>选择原图或原图文件夹后自动处理，无需先选择空目录。</p></div>`);break;
 case 'export':exportAction();break;
 case 'download-record':downloadRecord();break;
 case 'select':break;
 case 'cancel':send('cancel');break;
 case 'undo':undoRedo(false);break;case 'redo':undoRedo(true);break;
 case 'focus':focusCrop=!focusCrop;zoom=1;renderCanvas();break;
 case 'fit':focusCrop=false;zoom=1;renderCanvas();break;
 case 'zoom-in':zoom=Math.min(5,zoom*1.2);fitImage();break;case 'zoom-out':zoom=Math.max(.25,zoom/1.2);fitImage();break;
 case 'overlay':overlay=!overlay;$('#overlay-toggle').style.color=overlay?'var(--accent)':'';fitImage();break;
 case 'tools':showTools();break;
 case 'advanced':advanced(element.dataset.section);break;
 case 'inspect':openDrawer($('#inspector-title').textContent,$('#inspector-content').innerHTML+$('#inspector-action').innerHTML);break;
 case 'close-drawer':closeDrawer();break;
 case 'confirm':if(state.busy)return;closeDrawer();if(bridge){send('confirm',{id:row()?.id});}else{const r=row();if(!r?.roi)return;r.reviewed=true;state.status='已记录网页裁剪确认；科学质量状态保持不变';const next=state.rows.find(s=>!s.reviewed&&s.id!==r.id);if(next)select(next.id);else render();toast('裁剪已确认；质量警告仍需独立复核');}break;
 case 'reanalyze':if(bridge)send('reanalyze');else toast('网页不执行科学计算，请在桌面工作台重新识别。');break;
 case 'compose':if(bridge)send('compose');else toast('当前显示已生成的历史拼图，网页草稿未重新渲染。');break;
 case 'open_output':if(bridge)send('open_output');else exportAction();break;
 case 'settings':openDrawer('界面设置',`<label class="setting-row"><span>减少动效<small>保留状态反馈，减少移动与展开动画</small></span><input id="reduce-motion" type="checkbox" ${reduced?'checked':''}></label><div class="drawer-copy"><h3>同一界面，同一套细节</h3><p>网页与桌面工作台共用页面、字体规则、间距与动效。系统的减少动态效果设置也会被尊重。</p></div>`);break;
 case 'help':openDrawer('使用工作台',`<div class="drawer-copy"><h3>导入与自动处理</h3><p>桌面选择 WB 原图后，自动建立独立项目并识别泳道、裁剪和测量。</p><h3>图上复核</h3><p>拖动裁剪框或角点调整范围，方向键微调。滚轮缩放；“聚焦”切换原图与裁剪区域。调整后，旧结果不会冒充新的有效结果。</p><h3>结果与导出</h3><p>原始积分与有效信号独立展示。确认裁剪不会自动消除曝光或饱和质量警告。</p><h3>键盘</h3><p>Tab 移动焦点 · Esc 关闭面板<br>Ctrl+Z 撤销 · Ctrl+Shift+Z 重做</p></div>`);break;
 }
}
document.addEventListener('click',event=>{const button=event.target.closest('[data-action]');if(button&&!button.disabled){action(button.dataset.action,button);return;}const item=event.target.closest('[data-row]');if(item)select(item.dataset.row);const tab=event.target.closest('[data-mode]');if(tab)switchMode(tab.dataset.mode);const f=event.target.closest('[data-filter]');if(f){filter=f.dataset.filter;$$('[data-filter]').forEach(b=>b.classList.toggle('active',b===f));renderSources();}const cell=event.target.closest('[data-cell]');if(cell){selectedCell=state.cells[Number(cell.dataset.cell)];renderResults();renderInspector();if(matchMedia('(max-width:900px)').matches)openDrawer('结果依据',$('#inspector-content').innerHTML);}});
$('#source-search').addEventListener('input',event=>{search=event.target.value;renderSources();});
document.addEventListener('change',event=>{if(event.target.id==='reduce-motion'){reduced=event.target.checked;localStorage.setItem('bioimage-reduced-motion',String(reduced));document.body.classList.toggle('reduce-motion',reduced);}});
$('#drawer-backdrop').addEventListener('click',closeDrawer);
document.addEventListener('keydown',event=>{if(event.key==='Escape'){closeDrawer();return;}if((event.ctrlKey||event.metaKey)&&event.key.toLowerCase()==='z'&&!/INPUT|TEXTAREA/.test(event.target.tagName)){event.preventDefault();undoRedo(event.shiftKey);}if(event.key==='Enter'&&event.target.matches('[data-cell]'))event.target.click();if(event.key==='Tab'&&!$('#drawer').hidden){const focusables=$$('button:not(:disabled), input, a[href]', $('#drawer'));if(event.shiftKey&&document.activeElement===focusables[0]){event.preventDefault();focusables.at(-1).focus();}else if(!event.shiftKey&&document.activeElement===focusables.at(-1)){event.preventDefault();focusables[0].focus();}}});
$('#source-image').addEventListener('load',fitImage);
new ResizeObserver(()=>{fitImage();const tab=$('.mode-tab.active');if(tab){$('.mode-indicator').style.transform=`translateX(${tab.offsetLeft}px)`;$('.mode-indicator').style.width=tab.offsetWidth+'px';}}).observe($('.main-panel'));
$('#image-stage').addEventListener('wheel',event=>{if(!row()?.preview)return;event.preventDefault();zoom=Math.min(5,Math.max(.25,zoom*(event.deltaY<0?1.08:1/1.08)));fitImage();},{passive:false});
$('#crop-overlay').addEventListener('pointerdown',event=>{if(state.busy||mode!=='review')return;const r=row();if(!r?.roi)return;event.preventDefault();event.currentTarget.setPointerCapture(event.pointerId);const rect=$('#image-transform').getBoundingClientRect();drag={id:r.id,x:event.clientX,y:event.clientY,roi:structuredClone(r.roi),rect,handle:event.target.dataset.handle||'move'};});
$('#crop-overlay').addEventListener('pointermove',event=>{if(!drag)return;const r=row();if(r.id!==drag.id){drag=null;return;}let b={...drag.roi},dx=Math.round((event.clientX-drag.x)/drag.rect.width*r.width),dy=Math.round((event.clientY-drag.y)/drag.rect.height*r.height);if(drag.handle==='move'){b.x=Math.max(0,Math.min(r.width-b.width,b.x+dx));b.y=Math.max(0,Math.min(r.height-b.height,b.y+dy));}else{let right=b.x+b.width,bottom=b.y+b.height;if(drag.handle.includes('w'))b.x=Math.max(0,Math.min(right-4,b.x+dx));if(drag.handle.includes('e'))right=Math.max(b.x+4,Math.min(r.width,right+dx));if(drag.handle.includes('n'))b.y=Math.max(0,Math.min(bottom-4,b.y+dy));if(drag.handle.includes('s'))bottom=Math.max(b.y+4,Math.min(r.height,bottom+dy));b.width=right-b.x;b.height=bottom-b.y;}r.roi=b;const c=$('#crop-overlay');c.style.left=b.x/r.width*100+'%';c.style.top=b.y/r.height*100+'%';c.style.width=b.width/r.width*100+'%';c.style.height=b.height/r.height*100+'%';});
$('#crop-overlay').addEventListener('pointerup',()=>{if(!drag)return;const before=drag.roi,next={...row().roi};drag=null;if(JSON.stringify(before)!==JSON.stringify(next))commitCrop(next,before);});
$('#crop-overlay').addEventListener('pointercancel',()=>{if(drag){row().roi=drag.roi;drag=null;fitImage();}});
$('#crop-overlay').addEventListener('keydown',event=>{if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key)||state.busy)return;event.preventDefault();const r=row();if(!r?.roi)return;const before={...r.roi},next={...r.roi},step=event.shiftKey?10:1;const handle=event.target.dataset.handle;if(handle){const dx=event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0,dy=event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0;let right=next.x+next.width,bottom=next.y+next.height;if(handle.includes('w'))next.x=Math.max(0,Math.min(right-4,next.x+dx));if(handle.includes('e'))right=Math.max(next.x+4,Math.min(r.width,right+dx));if(handle.includes('n'))next.y=Math.max(0,Math.min(bottom-4,next.y+dy));if(handle.includes('s'))bottom=Math.max(next.y+4,Math.min(r.height,bottom+dy));next.width=right-next.x;next.height=bottom-next.y;commitCrop(next,before);return;}next.x=Math.max(0,Math.min(r.width-next.width,next.x+(event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0)));next.y=Math.max(0,Math.min(r.height-next.height,next.y+(event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0)));commitCrop(next,before);});
async function bootstrap(){icons();render();if(window.qt?.webChannelTransport){const script=document.createElement('script');script.src='qrc:///qtwebchannel/qwebchannel.js';script.onload=()=>new QWebChannel(qt.webChannelTransport,channel=>{bridge=channel.objects.workbench;bridge.stateChanged.connect(raw=>{try{const wasEmpty=!state.rows.length;setState(JSON.parse(raw));if(wasEmpty&&state.rows.length)switchMode('review');}catch{toast('项目状态无法读取，请重新打开项目。');}});$('#home-note').textContent='选择原图后自动创建独立项目，所有处理在本机执行。';send('refresh');});document.head.appendChild(script);}else{try{const response=await fetch('demo.json');if(response.ok){demoOriginal=await response.json();setState(structuredClone(demoOriginal));}}catch{} }if(new URLSearchParams(location.search).get('view')==='home'||!state.rows.length){$('#home-view').hidden=false;$('#work-view').hidden=true;}else switchMode('review');}
bootstrap();
