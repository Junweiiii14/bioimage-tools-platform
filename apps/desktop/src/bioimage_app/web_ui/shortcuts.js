'use strict';

// A key invokes the same guarded button/action path. No scientific input is synthesized.
window.workbenchActions = (() => {
  let catalog=null, bindings={}, groupId=null, identity='', composing=false, focused=true;
  let preferences=null, preferenceBase='', pending=null, message='', settingsFocus=null;
  const handlers=new Map(), scopes={global:'全局',project:'项目',intake:'采集组',workflow:'执行阶段',image:'图像调整'};
  const dialog=document.createElement('dialog');dialog.id='shortcuts-dialog';dialog.setAttribute('aria-labelledby','shortcuts-title');document.body.append(dialog);
  const editable=target=>target instanceof Element&&!!target.closest('input,textarea,select,[contenteditable]:not([contenteditable=false])');
  const visible=el=>!!el&&el.getClientRects().length>0&&!el.closest('[inert]');
  const available=el=>visible(el)&&!el.disabled;
  const click=el=>{if(!available(el))return false;el.click();return true;};
  const button=selector=>[...document.querySelectorAll(selector)].find(available);
  const project=()=>!!state.projectId&&(state.rows.length>0||!!state.intake)&&!$('#work-view').hidden;
  const grouped=()=>project()&&mode==='intake'&&!state.intake?.workflow&&!!state.intake?.grouped_draft;
  function syncIdentity(){const next=`${state.sessionEpoch}:${state.projectId}`;if(identity!==next){identity=next;groupId=null;}}
  function rememberGroup(event){syncIdentity();const el=event.target.closest?.('[data-group-id]');if(grouped()&&el)groupId=el.dataset.groupId;}
  for(const name of ['focusin','pointerdown','click'])document.addEventListener(name,rememberGroup,true);
  function card(){
    syncIdentity();
    const active=document.activeElement?.closest?.('[data-group-id]');
    if(active)groupId=active.dataset.groupId;
    return [...document.querySelectorAll('[data-group-id]')].find(el=>el.dataset.groupId===groupId&&visible(el))||button('[data-group-id]');
  }
  function focusCard(id){const el=[...document.querySelectorAll('[data-group-id]')].find(e=>e.dataset.groupId===id);if(el){groupId=id;el.tabIndex=-1;el.focus();el.scrollIntoView({block:'nearest'});}}
  function groupClick(selector){const el=card(),id=el?.dataset.groupId;if(!el||!click(el.querySelector(selector)))return false;focusCard(id);return true;}
  function move(delta){
    if(grouped()){
      const cards=[...document.querySelectorAll('[data-group-id]')].filter(visible),current=card();
      const index=cards.indexOf(current),target=cards[Math.max(0,Math.min(cards.length-1,index+delta))];
      if(!target)return false;focusCard(target.dataset.groupId);return true;
    }
    if(!project()||!state.rows.length)return false;
    const index=state.rows.findIndex(r=>r.id===row()?.id),target=state.rows[Math.max(0,Math.min(state.rows.length-1,index+delta))];
    select(target.id);return true;
  }
  function save(){
    if(!project())return false;
    if(window.desktopSession.hasDraft()){
      const selector=grouped()?'[data-group-action=save]':mode==='review'&&state.intake?.cropEnabled?'[data-intake-crop-action=confirm]':mode==='intake'?'[data-intake=save-plan], [data-intake=assign], [data-intake=accept-discovery]':null;
      if(selector&&click(button(selector)))return true;
      toast('请先应用当前调整，或明确放弃草稿，再保存项目。');return false;
    }
    return window.desktopSession.request('save');
  }
  handlers.set('project.save',save);
  handlers.set('project.open',()=>window.desktopSession.request('open'));
  for(const target of ['intake','review','layout','quant','results'])handlers.set(`view.${target}`,()=>{
    if(!project()||state.intake&&!window.intakeWorkspace.allowedModes().includes(target)||target==='intake'&&!state.intake)return false;
    return click(button(`[data-mode="${target}"]`));
  });
  handlers.set('group.previous',()=>move(-1));handlers.set('group.next',()=>move(1));
  handlers.set('group.toggle',()=>grouped()&&groupClick('[data-group-select]'));
  handlers.set('group.all',()=>grouped()&&click(button('[data-group-action=select-visible]')));
  handlers.set('group.assign',()=>grouped()&&click(button('[data-group-action=assign]')));
  handlers.set('source.zoom',()=>{
    if(!grouped())return false;const el=card(),chosen=el?.querySelector('input[data-group-source]:checked');
    return click((chosen?.closest('.grouped-image')||el)?.querySelector('[data-group-action=zoom]'));
  });
  ['first','second','third'].forEach((name,index)=>handlers.set(`source.${name}`,()=>{
    if(!grouped())return false;const el=card(),id=el?.dataset.groupId;
    if(!click(el?.querySelectorAll('[data-group-source]')[index]))return false;focusCard(id);return true;
  }));
  handlers.set('source.clear',()=>grouped()&&groupClick('[data-group-action=unpick]'));
  handlers.set('workflow.continue',()=>project()&&!window.desktopSession.hasDraft()&&click(button('[data-intake=run], [data-intake-crop-action=run]')));
  handlers.set('edit.undo',()=>project()&&['review','layout','results'].includes(mode)&&!$('[data-action=undo]').disabled&&(action('undo'),true));
  handlers.set('edit.redo',()=>project()&&['review','layout','results'].includes(mode)&&!$('[data-action=redo]').disabled&&(action('redo'),true));
  handlers.set('shortcuts.settings',()=>{open();return true;});
  function invoke(id,options={}){
    if(!catalog||state.busy||!focused||!document.hasFocus())return false;
    const explicitOpen=id==='project.open'&&options.button instanceof HTMLElement&&options.button.dataset.session==='open'&&options.button.closest('#session-dialog[open]');
    if((document.querySelector('dialog[open]')||!$('#drawer').hidden)&&!explicitOpen)return false;
    return handlers.get(id)?.()===true;
  }
  function key(event){
    if(event.metaKey||event.getModifierState?.('AltGraph'))return null;
    const code=event.code||'',letter=code.match(/^Key([A-Z])$/),digit=code.match(/^(?:Digit|Numpad)([0-9])$/);
    let value=letter?.[1]||digit?.[1]||({' ':'Space',Spacebar:'Space'}[event.key])||event.key;
    if(value?.length===1)value=value.toUpperCase();
    if(!/^(?:[A-Z0-9]|F[1-9]|F1[0-2]|ArrowUp|ArrowDown|ArrowLeft|ArrowRight|Space|Enter)$/.test(value||''))return null;
    if(!event.ctrlKey&&!event.altKey&&!event.shiftKey)return null;
    return `${event.ctrlKey?'Ctrl+':''}${event.altKey?'Alt+':''}${event.shiftKey?'Shift+':''}${value}`;
  }
  function validate(value){
    const used=new Map();
    for(const entry of catalog.actions){const binding=value[entry.id]||'';
      if(catalog.reserved.includes(binding)||binding==='Ctrl+Z'&&entry.id!=='edit.undo')return '此组合键保留给系统或文本编辑。';
      if(binding&&used.has(binding))return `${binding} 同时用于“${used.get(binding)}”和“${entry.label}”。`;
      if(binding)used.set(binding,entry.label);
    }return '';
  }
  function renderSettings(){
    const active=document.activeElement;
    for(const kind of ['record','clear','command']){
      const id=active?.getAttribute?.(`data-shortcut-${kind}`);
      if(id)settingsFocus={kind,id};
    }
    const scroll=dialog.querySelector('.shortcut-list')?.scrollTop||0;
    dialog.innerHTML=`<header><h2 id="shortcuts-title">快捷键</h2><button class="button subtle" data-shortcut-command="close">关闭</button></header><p>点击一个组合键，再按新的按键。作用域内使用同一按钮操作；输入文字、中文输入法组合、弹窗和忙碌时不触发。</p><div class="shortcut-list">${catalog.actions.map(entry=>`<label class="shortcut-row"><span>${escapeText(entry.label)}<small>${scopes[entry.scope]||entry.scope}</small></span><input readonly data-shortcut-record="${entry.id}" value="${escapeText(preferences[entry.id])}" placeholder="未绑定" aria-label="${escapeText(entry.label)} 的快捷键"><button type="button" class="text-button" data-shortcut-clear="${entry.id}" aria-label="禁用${escapeText(entry.label)}快捷键">禁用</button></label>`).join('')}</div><p data-shortcut-status role="status">${escapeText(message||validate(preferences)||(JSON.stringify(preferences)===preferenceBase?'当前设置已保存。':'有修改，保存后生效。'))}</p><footer><button class="text-button" data-shortcut-command="restore">恢复默认草稿</button><button class="button primary" data-shortcut-command="save" ${pending||validate(preferences)?'disabled':''}>保存快捷键</button></footer>`;
    dialog.querySelector('.shortcut-list').scrollTop=scroll;
    if(settingsFocus){
      const target=dialog.querySelector(`[data-shortcut-${settingsFocus.kind}="${settingsFocus.id}"]`);
      if(target&&!target.disabled)target.focus({preventScroll:true});
      else{const status=dialog.querySelector('[data-shortcut-status]');status.tabIndex=-1;status.focus({preventScroll:true});}
    }
  }
  function open(){
    if(!catalog){toast('快捷键目录尚未载入，请稍候。');return;}
    $('#session-menu').open=false;preferences={...bindings};preferenceBase=JSON.stringify(bindings);message='';pending=null;settingsFocus=null;renderSettings();if(!dialog.open)dialog.showModal();
  }
  function receive(next){
    if(!next?.actions||next.schema_version!==1)return;
    catalog=next;bindings={...next.bindings};
    if(pending&&next.receipt===pending.id){
      if(next.error)message=next.error;
      else{const newer=JSON.stringify(preferences)!==pending.submitted;if(!newer)preferences={...bindings};preferenceBase=JSON.stringify(bindings);message=newer?'提交的快捷键已保存；之后的新修改仍未保存。':'快捷键已保存。';}
      pending=null;if(dialog.open)renderSettings();
    } else if(dialog.open&&!pending&&JSON.stringify(preferences)===preferenceBase){preferences={...bindings};preferenceBase=JSON.stringify(bindings);message=next.error||'';renderSettings();}
    else if(next.error&&dialog.open){message=next.error;renderSettings();}
    decorate();
  }
  const targets={ 'project.save':'[data-session=save]','project.open':'[data-session=open]', 'group.all':'[data-group-action=select-visible]','group.assign':'[data-group-action=assign]','workflow.continue':'[data-intake=run], [data-intake-crop-action=run]','edit.undo':'[data-action=undo]','edit.redo':'[data-action=redo]','shortcuts.settings':'[data-action=shortcut-settings]'};
  function decorate(){
    if(!catalog)return;
    syncIdentity();
    for(const entry of catalog.actions){
      const selector=targets[entry.id]||(entry.id.startsWith('view.')?`[data-mode="${entry.id.slice(5)}"]`:null);
      if(!selector)continue;
      for(const el of document.querySelectorAll(selector)){
        const binding=bindings[entry.id];el.setAttribute('aria-keyshortcuts',(binding||'').replace('Ctrl+','Control+'));el.title=entry.label+(binding?` · ${binding}`:'');
        if(['project.save','shortcuts.settings'].includes(entry.id))el.disabled=!!state.busy||entry.id==='project.save'&&!project();
      }
    }
  }
  dialog.addEventListener('click',event=>{
    const clear=event.target.closest('[data-shortcut-clear]');if(clear){preferences[clear.dataset.shortcutClear]='';message='';renderSettings();return;}
    const command=event.target.closest('[data-shortcut-command]');if(!command||command.disabled)return;
    if(command.dataset.shortcutCommand==='close')dialog.close();
    if(command.dataset.shortcutCommand==='restore'){preferences=Object.fromEntries(catalog.actions.map(a=>[a.id,a.default]));message='默认草稿已恢复，保存后生效。';renderSettings();}
    if(command.dataset.shortcutCommand==='save'){
      const id=crypto.randomUUID();pending={id,submitted:JSON.stringify(preferences)};message='正在保存快捷键…';
      if(!window.desktopSession.request('shortcuts',{requestId:id,bindings:preferences})){message='请在桌面工作台保存快捷键。';pending=null;}renderSettings();
    }
  });
  document.addEventListener('compositionstart',()=>{composing=true;},true);
  document.addEventListener('compositionend',()=>{composing=false;},true);
  window.addEventListener('blur',()=>{focused=false;composing=false;});window.addEventListener('focus',()=>{focused=true;});
  document.addEventListener('keydown',event=>{
    if(event.isComposing||event.keyCode===229||composing||event.repeat)return;
    if(dialog.open&&event.target.matches?.('[data-shortcut-record]')){
      if(['Tab','Escape'].includes(event.key))return;
      event.preventDefault();event.stopImmediatePropagation();
      const binding=['Backspace','Delete'].includes(event.key)?'':key(event);
      if(binding!==null){preferences[event.target.dataset.shortcutRecord]=binding;message='';renderSettings();}return;
    }
    if(!catalog||event.defaultPrevented||editable(event.target)||document.querySelector('dialog[open]')||!$('#drawer').hidden)return;
    const binding=key(event),entry=catalog.actions.find(a=>binding&&bindings[a.id]===binding);
    if(!entry)return;
    event.preventDefault();event.stopImmediatePropagation();invoke(entry.id);
  },true);
  let queued=false;new MutationObserver(()=>{if(!queued){queued=true;requestAnimationFrame(()=>{queued=false;decorate();});}}).observe(document.body,{childList:true,subtree:true});
  return {invoke,receive,open,decorate,loaded:()=>!!catalog,isComposing:()=>composing};
})();
if(window.desktopSession.shortcutState())window.workbenchActions.receive(window.desktopSession.shortcutState());
else fetch('shortcut_actions.json').then(response=>{if(!response.ok)throw new Error();return response.json();}).then(catalog=>{
  if(!window.workbenchActions.loaded())window.workbenchActions.receive({...catalog,bindings:Object.fromEntries(catalog.actions.map(a=>[a.id,a.default]))});
}).catch(()=>{});
