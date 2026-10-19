'use strict';

// Navigation and lifecycle messages never contain scientific results or file contents.
const desktopSession = (() => {
  let channel=null, session={}, token=null, lastPosition='', timer=null, locked=false,epoch=0;
  const modal=()=>document.querySelector('#session-dialog');
  const button=(choice,label,primary=false)=>`<button class="button ${primary?'primary':'subtle'}" data-session-reply="${choice}">${label}</button>`;
  function hasDraft(){
    if(window.groupReview?.hasDraft())return true;
    if(manualQuant.submittedRevision!==null||state.busy)return false;
    const d=manualQuant.draft,r=row();
    if(!r)return false;
    if(manualQuant.active&&d&&(JSON.stringify(d.roi)!==JSON.stringify(r.roi)||Number(d.n)!==Number(r.lanes)))return true;
    if(typeof manualLanes!=='undefined'&&manualLanes.toolsOpen){
      const current=(quantData()?.lanes||[]).map(l=>l.targetRoi||l.roi);
      return JSON.stringify(current)!==JSON.stringify(manualLanes.boxes);
    }
    return false;
  }
  function send(action,data={}){if(channel)channel.session(action,JSON.stringify(data));}
  function position(){
    if(!channel||!state.projectId||!state.rows.length||token===null||locked)return;
    const r=row(),data={projectId:state.projectId,mode,rowId:r?.id||'',figure:r?.fig||'',lane:quantLane,name:state.projectName,draft:hasDraft()};
    const encoded=JSON.stringify(data);if(encoded!==lastPosition){lastPosition=encoded;send('position',data);}
  }
  function route(){
    renderChrome();
    const r=session.route;if(!r||r.token===undefined||r.token===token)return;
    if(r.mode==='home'){
      token=r.token;lastPosition='';manualQuant.active=false;manualQuant.pendingImport=false;manualQuant.draft=null;manualLanes.key=null;
      state={projectName:'新建实验项目',rows:[],cells:[],selectedId:null,busy:false,status:'就绪',outputPath:'',montage:null,quant:null,projectId:''};
      completedKey=null;mode='review';$('#home-view').hidden=false;$('#work-view').hidden=true;render();return;
    }
    if(!state.rows.length||state.busy||r.projectId!==state.projectId)return;
    token=r.token;lastPosition='';manualQuant.pendingImport=false;
    const selected=state.rows.find(item=>item.id===r.rowId)||state.rows[0];state.selectedId=selected.id;
    quantLane=Number.isInteger(r.lane)&&r.lane>0&&r.lane<=selected.lanes?r.lane:1;
    quantBand=null;quantDetail=true;switchMode(['review','layout','quant','results'].includes(r.mode)?r.mode:'quant');
    if(mode!=='quant')sendSelection(selected.id);
    position();
  }
  function sendSelection(id){if(bridge)bridge.request('select',JSON.stringify({id}));}
  function renderChrome(){
    if(!channel)return;const active=!!session.workspace&&state.rows.length>0;
    $('#project-name').textContent=active?state.projectName:'项目首页';
    $$('.header-actions>[data-action]').forEach(el=>el.hidden=!active);
    $('#save-status').textContent=session.saveState||'就绪';
  }
  function renderSession(){
    renderChrome();
    $('#session-project-parent').textContent='新项目保存到：'+(session.projectParent||'文档 / BioImage / Projects');
    const recents=session.recents||[];
    $('#session-recents').innerHTML=recents.length?recents.map((p,i)=>`<button class="session-recent" data-session="recent" data-index="${i}"><i data-icon="folder"></i><div><strong>${escapeText(p.name||'WB 项目')}</strong><p>上次停留：${({quant:'灰度定量',results:'结果',layout:'拼图排版',review:'原图裁剪'})[p.mode]||'灰度定量'}${p.figure?' · '+escapeText(p.figure):''}</p><small>${escapeText(p.path)}</small></div><span>继续工作</span><i data-icon="arrow"></i></button>`).join(''):'<p class="session-hint">打开或创建项目后，会在这里显示。</p>';
    icons($('#session-recents'));
    const stage=session.stage||'idle';locked=['confirm_busy','confirm_dirty','confirm_draft','cancel','shutdown'].includes(stage);
    if(stage==='idle'||stage==='opening'){
      if(modal().open)modal().close();
      if(stage==='opening'&&state.rows.length){$('#home-view').hidden=true;$('#work-view').hidden=false;}
      if(channel)$('#save-status').textContent=session.saveState||'就绪';return;
    }
    const exiting=session.intent==='exit';let title='',actions='';
    if(stage==='confirm_busy'){title='先停止当前任务？';actions=button('return','继续工作')+button('cancel',exiting?'取消任务并退出':'取消任务并继续',true);}
    else if(stage==='confirm_dirty'){title=exiting?'保存修改后退出？':'保存修改后继续？';actions=button('return','返回工作')+button('discard',exiting?'放弃修改并退出':'放弃修改')+button('save',exiting?'保存并退出':'保存并继续',true);}
    else if(stage==='confirm_draft'){title='还有未应用的调整';actions=button('return','返回应用调整',true)+button('discard',exiting?'放弃草稿并退出':'放弃草稿并继续');}
    else if(stage==='cancel'||stage==='shutdown'){title=stage==='cancel'?'正在取消任务':exiting?'正在退出 BioImage WB':'正在关闭当前项目';}
    else{title=stage==='failed'?'退出尚未完成':'未能打开项目';actions=button('return','返回窗口')+(stage==='failed'?button('retry','重试退出',true):'<button class="button subtle" data-session="open">重新选择项目</button>'+(session.canImportFailedFolder?'<button class="button primary" data-session="new_from_folder">按原图文件夹新建</button>':''));}
    $('#session-dialog-body').innerHTML=`<h2 id="session-dialog-title">${title}</h2><p>${escapeText(session.message||'请稍候。')}</p>${stage==='shutdown'||stage==='cancel'?'<progress aria-label="等待后台任务完成"></progress><p class="session-hint">完成前窗口会保持可见；已提交结果会保留。</p>':''}<div class="session-dialog-actions">${actions}</div>`;
    if(!modal().open)modal().showModal();
  }
  function connect(bridgeObject){
    if(channel)return;channel=bridgeObject;
    channel.sessionStateChanged.connect(raw=>{try{const next=JSON.parse(raw);if((next.epoch??0)<epoch)return;epoch=next.epoch??0;session=next;renderSession();route();}catch{toast('项目会话状态读取失败，请重试。');}});
    send('refresh');timer=setInterval(position,500);
  }
  document.addEventListener('click',event=>{
    const reply=event.target.closest('[data-session-reply]');if(reply){send('reply',{choice:reply.dataset.sessionReply});return;}
    let el=event.target.closest('[data-session]');
    if(!el&&event.target.closest('[data-action=home]'))el=event.target.closest('[data-action=home]');
    if(!el||!channel)return;
    event.preventDefault();event.stopImmediatePropagation();position();$('#session-menu').open=false;
    const action=el.dataset.session||'home';
    const workflow=document.querySelector('[name=session-workflow]:checked')?.value||'quant';
    if(action==='images'){manualQuant.pendingImport=workflow==='quant';bridge.request(workflow==='quant'?'quant_import':'import','{}');}
    else if(action==='folder'&&workflow!=='quant')bridge.request('import_folder','{}');
    else send(action,action==='recent'?{index:Number(el.dataset.index)}:{});
  },true);
  modal().addEventListener('cancel',event=>{event.preventDefault();if(!['shutdown','cancel'].includes(session.stage))send('reply',{choice:'return'});});
  document.addEventListener('input',()=>queueMicrotask(position));
  document.addEventListener('pointerup',()=>queueMicrotask(position));
  window.addEventListener('pagehide',()=>{if(timer)clearInterval(timer);});
  function acceptState(next){const value=next.sessionEpoch??0;if(value<epoch)return false;epoch=value;return true;}
  return {connect,route,hasDraft,acceptState};
})();
window.desktopSession=desktopSession;
if(bridge)desktopSession.connect(bridge);
