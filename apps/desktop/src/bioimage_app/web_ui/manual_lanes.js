'use strict';

// Lane geometry is a local draft. Only the durable original-pixel worker measures.
const manualLanes = {
  method: 'lanes', selected: 0, dragging: null, key: null, boxes: [], measurementMode: 'peaks',
  identity() {
    return {projectId:state.projectId,id:row()?.id,sourceId:row()?.sourceId,revision:quantData()?.revision};
  },
  warnings() {
    const notes=row()?.notes||'',warnings=[];
    if(notes.includes('fig_partition@1'))warnings.push('Fig 分组、标签和泳道为自动建议，可在当前组直接修正。');
    if(notes.includes('ambiguous_fig_suffix'))warnings.push('Fig 标签存在 I / L 歧义，请对照图中文字修改名称。');
    if(notes.includes('missing_protein_label'))warnings.push('这排蛋白名称未识别，请补充名称并核对积分方式。');
    if(notes.includes('quant_planning_failed'))warnings.push('这排自动规划失败，请手动框选泳道。');
    return warnings.map(text=>`<p class="manual-warning">${escapeText(text)}</p>`).join('');
  },
  sync() {
    const key = [state.projectId,row()?.id,row()?.sourceId,quantData()?.revision].join(':');
    if (this.key === key) return;
    this.key = key; this.dragging = null; this.selected = 0;
    this.boxes = (quantData()?.lanes || []).map(lane => ({...(lane.targetRoi || lane.roi)}));
    this.measurementMode = quantData()?.measurementMode || 'peaks';
  },
  render() {
    this.sync();
    const disabled = state.busy || !bridge ? 'disabled' : '';
    let tools = $('#manual-lane-tools');
    if (!tools) {
      tools = document.createElement('section'); tools.id = 'manual-lane-tools'; tools.className = 'manual-lane-tools';
      $('.source-panel').insertBefore(tools, $('.source-panel .source-filters'));
    }
    tools.hidden = mode !== 'quant';
    if (tools.hidden) return;
    tools.innerHTML = `<button class="button primary full" data-lane-action="automatic" ${disabled}>按 Fig 自动分组并定量</button>${this.warnings()}<h3>手动泳道</h3><p>框选第一条完整泳道，再复制并移动。已完成的其他组保持。</p>
      <div class="manual-action-grid"><button class="button subtle" data-lane-action="draw" ${disabled}>框选泳道</button><button class="button subtle" data-lane-action="copy" ${disabled || !this.boxes.length?'disabled':''}>复制泳道</button><button class="button subtle" data-lane-action="delete" ${disabled || !this.boxes.length?'disabled':''}>删除选中</button><button class="button subtle" data-lane-action="clear" ${disabled}>清空本轮</button></div>
      <button class="text-button" data-lane-action="reselect" ${disabled}>重新框选当前组</button>
      <label class="quant-field">选择泳道<select data-manual-lane-select ${disabled}>${this.boxes.map((box,index)=>`<option value="${index}" ${index===this.selected?'selected':''}>泳道 ${index+1} · ${box.width}×${box.height}px</option>`).join('') || '<option>尚未框选</option>'}</select></label>
      <div class="manual-action-grid"><button class="button subtle" data-lane-action="new" ${disabled}>添加分组</button><button class="button subtle" data-lane-action="rename" ${disabled}>修改名称</button><button class="button subtle" data-lane-action="move" ${disabled}>调整这排分组</button><button class="button subtle" data-lane-action="merge" ${disabled}>合并分组</button></div><button class="text-button" data-lane-action="next" ${disabled}>保留结果，切换下一组</button>`;
  },
  setup() { return mode === 'quant' && quantDetail && manualQuant.isSetup() && this.method === 'lanes'; },
  activate() { manualQuant.active = true; this.method = 'lanes'; quantDetail = true; focusCrop = false; },
  action(action) {
    if(state.busy || !bridge) return;
    this.sync();
    if(action==='next'){
      const groups=[...new Set(state.rows.map(r=>r.fig))],index=groups.indexOf(row()?.fig),next=state.rows.find(r=>r.fig===groups[index+1]);
      if(!next)return toast('已到最后一组，可添加分组或导出结果。');
      manualQuant.active=false;quantDetail=true;send('quant_select',{id:next.id});return;
    }
    if(action==='automatic'){manualQuant.active=false;quantDetail=true;send('quant_fig',this.identity());return;}
    if(['new','rename','move','merge'].includes(action)) {
      const title = ({new:'添加分组',rename:'修改分组与条带名称',move:'调整这排条带的分组',merge:'合并当前 Fig 的全部条带'})[action];
      openDrawer(title, `<div class="drawer-copy">${action==='move'?'<p>输入已有 Fig 可并入，输入新名称可将这一排拆为新组。测量结果保留。</p>':action==='merge'?'<p>将当前 Fig 的全部条带并入所填组名，保留各排测量结果。</p>':''}<label class="quant-field">Fig 分组名称<input id="manual-group-name" maxlength="120" value="${action==='new'||action==='merge'?'':escapeText(row()?.fig)}"></label><label class="quant-field">当前条带名称<input id="manual-protein-name" maxlength="120" value="${escapeText(row()?.protein||'条带')}"></label><button class="button primary" data-manual-group-save="${action}">保存修改</button></div>`);
      return;
    }
    this.activate();
    if(action === 'clear' || action === 'reselect') this.boxes = [];
    if(action === 'delete') {this.boxes.splice(this.selected,1);this.selected=Math.max(0,this.selected-1);}
    if(action === 'copy') {
      const source=this.boxes[this.selected]; if(!source)return;
      if(this.boxes.length>=96)return toast('每组最多96条泳道。');
      const candidates=[source.x+source.width+3,source.x-source.width-3];
      const x=candidates.find(x=>x>=0 && x+source.width<=row().width && this.boxes.every(b=>x+source.width<=b.x||b.x+b.width<=x));
      if(x===undefined)return toast('相邻位置没有空位，请先移动现有框。');
      this.boxes.push({...source,x});this.selected=this.boxes.length-1;
    }
    render();
  },
  submit(resetBounds=false) {
    if(this.method!=='lanes')return this.legacySubmit(resetBounds);
    if(state.busy || !bridge)return;
    this.sync();
    const boxes=this.boxes.map(box=>({...box})).sort((a,b)=>a.x-b.x);
    if(!boxes.length)return toast('请先框选完整泳道。');
    if(boxes.some((b,i)=>b.width<1||b.height<2||b.height>4096||b.x<0||b.y<0||b.x+b.width>row().width||b.y+b.height>row().height||(i&&boxes[i-1].x+boxes[i-1].width>b.x)))return toast('泳道须在原图内且不重叠，高度2–4096像素。');
    const x=Math.min(...boxes.map(b=>b.x)),y=Math.min(...boxes.map(b=>b.y));
    const roi={x,y,width:Math.max(...boxes.map(b=>b.x+b.width))-x,height:Math.max(...boxes.map(b=>b.y+b.height))-y};
    const draft=manualQuant.current();
    const emptyLanes=draft.empty.trim()?draft.empty.split(/[,，]/).map(value=>Number(value.trim())):[];
    if(emptyLanes.some(n=>!Number.isInteger(n)||n<1||n>boxes.length)||new Set(emptyLanes).size!==emptyLanes.length)return toast('排除泳道须为不重复的有效编号。');
    manualQuant.submittedRevision=quantData()?.revision;
    send('quant_target',{...this.identity(),roi,n:boxes.length,laneRois:boxes,polarity:draft.polarity,emptyLanes,resetBounds,measurementMode:this.measurementMode});
  },
  overlay(actualZoom) {
    const layer=$('#quant-lanes'),source=row();
    layer.hidden=mode!=='quant';
    layer.innerHTML=!source?'':this.boxes.map((box,index)=>`<div class="quant-lane ${index===this.selected?'selected':''}" data-manual-lane="${index}" tabindex="0" role="button" aria-label="泳道 ${index+1}，方向键移动" style="left:${box.x/source.width*100}%;top:${box.y/source.height*100}%;width:${box.width/source.width*100}%;height:${box.height/source.height*100}%;border-width:0"><svg class="manual-lane-shape"><rect x="0" y="0" width="100%" height="100%" vector-effect="non-scaling-stroke"/></svg><span class="quant-lane-tag" style="transform:scale(${1/actualZoom})">${index+1}</span></div>`).join('');
  }
};
manualLanes.legacySubmit=manualQuant.submit.bind(manualQuant);
manualQuant.submit=(reset=false)=>manualLanes.submit(reset);
const manualRender=manualQuant.render.bind(manualQuant), manualOverlay=manualQuant.overlay.bind(manualQuant);
manualQuant.render=function(){
  manualLanes.sync();manualRender();manualLanes.render();
  const disabled=state.busy||!bridge?'disabled':'';
  $('#inspector-content').insertAdjacentHTML('afterbegin',`<section class="inspect-section"><h3>完整泳道定量</h3><label class="quant-field">框选方式<select data-manual-method ${disabled}><option value="lanes" ${manualLanes.method==='lanes'?'selected':''}>独立泳道 · WBQuant</option><option value="grid" ${manualLanes.method==='grid'?'selected':''}>规则网格 · 指定 N</option></select></label><label class="quant-field">积分方式<select data-manual-measurement ${disabled}><option value="peaks" ${manualLanes.measurementMode==='peaks'?'selected':''}>条带峰 · 保留多个峰</option><option value="smear" ${manualLanes.measurementMode==='smear'?'selected':''}>整段拖尾 · UB 总灰度</option></select></label><p>${manualLanes.method==='lanes'?`已框选 ${manualLanes.boxes.length} 条泳道。复制后拖动框体，方向键微调。`:'按测量区域与 N 生成规则泳道。'}${manualLanes.measurementMode==='smear'?' 整段模式用所选高度与端点直线封底，可在计算后修改范围。':''}</p></section>`);
  if(manualLanes.method==='lanes'){
    const sections=$$('#inspector-content > .inspect-section');
    if(sections[1]){const details=document.createElement('details');details.className='inspect-section';details.innerHTML='<summary>规则网格与精确区域（高级）</summary>';sections[1].replaceWith(details);details.appendChild(sections[1]);}
    $('[data-manual-quant-run]').disabled=!!disabled||!manualLanes.boxes.length;
    $('#quant-profile').innerHTML='<div class="quant-empty"><h3>选择完整泳道</h3><p>一条泳道可包含多排蛋白条带。计算后检查全部泳道曲线，或进入单泳道调整。</p></div>';
    const selected=manualLanes.boxes[manualLanes.selected];
    if(selected)$('#inspector-content').insertAdjacentHTML('afterbegin',`<section class="inspect-section"><h3>泳道 ${manualLanes.selected+1} · 原图坐标</h3><div class="quant-fields">${[['x','左边 x'],['y','上边 y'],['width','统一宽度'],['height','统一高度']].map(([key,label])=>`<label class="quant-field">${label}<input type="number" step="1" data-manual-lane-field="${key}" value="${selected[key]}" ${disabled}></label>`).join('')}</div><p>宽高修改应用到本轮全部泳道，保持同尺寸。</p></section>`);
  }
  $('#inspector-content').insertAdjacentHTML('beforeend','<section class="manual-compact-controls">'+$('#manual-lane-tools').innerHTML+'</section>');
};
manualQuant.overlay=function(z){if(manualLanes.method==='lanes')manualLanes.overlay(z);else manualOverlay(z);};
const oldSources=renderSources;
renderSources=function(){oldSources();manualLanes.render();};
const oldProfileRefresh=manualQuant.refreshProfiles.bind(manualQuant);
manualQuant.refreshProfiles=function(force=false){
  oldProfileRefresh(force);
  const dialog=$('#quant-profiles-dialog');if(!dialog.open)return;
  let actions=$('#manual-profile-actions');
  if(!actions){actions=document.createElement('div');actions.id='manual-profile-actions';actions.className='manual-profile-actions';$('.quant-profiles-toolbar').after(actions);}
  const disabled=state.busy||!bridge?'disabled':'';
  actions.innerHTML=`<button class="button subtle" data-quant-history="undo" ${disabled}>撤销</button><button class="button subtle" data-quant-history="redo" ${disabled}>重做</button>${manualQuant.profileView==='single'?`<label class="quant-field">补峰起点<input id="manual-peak-start" type="number" min="0" step="1"></label><label class="quant-field">补峰终点<input id="manual-peak-end" type="number" min="1" step="1"></label><button class="button subtle" data-manual-band="add" ${disabled}>添加条带峰</button><button class="button subtle" data-manual-band="exclude" ${disabled}>包含 / 排除此峰</button>`:''}`;
};
document.addEventListener('click',event=>{
  if(!(event.target instanceof Element))return;
  const action=event.target.closest('[data-lane-action]');if(action)manualLanes.action(action.dataset.laneAction);
  const save=event.target.closest('[data-manual-group-save]');if(save&&!state.busy){
    const name=$('#manual-group-name').value.trim();if(!name)return toast('请输入分组名称。');
    const action=({new:'quant_new_group',rename:'quant_rename',move:'quant_move_row',merge:'quant_merge_group'})[save.dataset.manualGroupSave];send(action,{...manualLanes.identity(),name,figure:name,protein:$('#manual-protein-name')?.value||'条带'});closeDrawer();
  }
  const history=event.target.closest('[data-quant-history]');if(history)send('quant_history',{...manualLanes.identity(),direction:history.dataset.quantHistory});
  const band=event.target.closest('[data-manual-band]');if(band){
    const selected=quantSelection(),operation=band.dataset.manualBand;
    const startText=$('#manual-peak-start')?.value,endText=$('#manual-peak-end')?.value;
    if(operation==='add'&&(!startText||!endText))return toast('请填写补峰的起点与终点。');
    send('quant_band',{...manualLanes.identity(),operation,lane:selected.lane?.lane,bandId:selected.band?.id,start:Number(startText),end:Number(endText)});
  }
},true);
document.addEventListener('change',event=>{
  const el=event.target;
  if(el.matches('[data-manual-method]')){manualLanes.method=el.value;renderQuant();}
  if(el.matches('[data-manual-measurement]')){manualLanes.measurementMode=el.value;if(el.value==='smear')manualLanes.method='lanes';renderQuant();}
  if(el.matches('[data-manual-lane-select]')){manualLanes.selected=Number(el.value);manualLanes.activate();renderQuant();}
  if(el.matches('[data-manual-lane-field]')){
    const key=el.dataset.manualLaneField,value=Number(el.value),boxes=manualLanes.boxes.map(b=>({...b}));
    if(!Number.isInteger(value))return toast('泳道坐标须为整数。');
    boxes.forEach((b,i)=>{if(i===manualLanes.selected||key==='width'||key==='height')b[key]=value;});
    if(boxes.some(b=>b.x<0||b.y<0||b.width<1||b.height<2||b.x+b.width>row().width||b.y+b.height>row().height))return toast('泳道坐标超出原图。');
    manualLanes.boxes=boxes;renderQuant();
  }
});
// Existing precise-grid controls remain an explicit alternate workflow.
document.addEventListener('click',event=>{if(event.target.closest('[data-manual-quant-whole]'))manualLanes.method='grid';},true);
document.addEventListener('input',event=>{if(event.target.matches('[data-manual-quant-coordinate],[data-manual-quant-field="n"]'))manualLanes.method='grid';},true);
const laneViewport=$('#image-viewport');
laneViewport.addEventListener('pointerdown',event=>{
  if(!manualLanes.setup()||state.busy||!bridge||event.button!==0)return;
  const source=row(),rect=$('#image-transform').getBoundingClientRect();
  if(!source?.preview||event.clientX<rect.left||event.clientX>=rect.right||event.clientY<rect.top||event.clientY>=rect.bottom)return;
  event.preventDefault();event.stopImmediatePropagation();
  const chosen=event.target.closest('[data-manual-lane]');if(chosen)manualLanes.selected=Number(chosen.dataset.manualLane);
  const start=manualQuant.point(event,rect,source);
  manualLanes.dragging={key:manualLanes.key,rect,start,index:chosen?manualLanes.selected:null,original:chosen?{...manualLanes.boxes[manualLanes.selected]}:null};
  laneViewport.setPointerCapture(event.pointerId);
},true);
laneViewport.addEventListener('pointermove',event=>{
  const d=manualLanes.dragging;if(!d||d.key!==manualLanes.key||state.busy)return;
  event.stopImmediatePropagation();const end=manualQuant.point(event,d.rect,row());
  if(d.original){const b=d.original;manualLanes.boxes[d.index]={...b,x:Math.max(0,Math.min(row().width-b.width,b.x+end.x-d.start.x)),y:Math.max(0,Math.min(row().height-b.height,b.y+end.y-d.start.y))};}
  else {const first=manualLanes.boxes[0];d.next=first?{x:Math.min(d.start.x,row().width-first.width),y:Math.min(d.start.y,row().height-first.height),width:first.width,height:first.height}:{x:Math.min(d.start.x,end.x),y:Math.min(d.start.y,end.y),width:Math.abs(end.x-d.start.x),height:Math.abs(end.y-d.start.y)};
    const layer=$('#quant-lanes');manualLanes.overlay(1);layer.insertAdjacentHTML('beforeend',`<div class="quant-target-draft" style="left:${d.next.x/row().width*100}%;top:${d.next.y/row().height*100}%;width:${d.next.width/row().width*100}%;height:${d.next.height/row().height*100}%"></div>`);return;}
  fitImage();
},true);
laneViewport.addEventListener('pointerup',event=>{
  const d=manualLanes.dragging;if(!d)return;event.stopImmediatePropagation();manualLanes.dragging=null;
  if(d.next&&d.next.width>=1&&d.next.height>=2&&manualLanes.boxes.length<96){manualLanes.boxes.push(d.next);manualLanes.selected=manualLanes.boxes.length-1;}
  renderQuant();manualLanes.render();
},true);
laneViewport.addEventListener('pointercancel',()=>{const d=manualLanes.dragging;if(d?.original)manualLanes.boxes[d.index]=d.original;manualLanes.dragging=null;renderQuant();},true);
$('#quant-lanes').addEventListener('keydown',event=>{
  const el=event.target.closest('[data-manual-lane]');if(!el||state.busy||!manualLanes.setup())return;
  const b=manualLanes.boxes[Number(el.dataset.manualLane)],step=event.shiftKey?10:1;
  if(!['ArrowLeft','ArrowRight','ArrowUp','ArrowDown'].includes(event.key))return;
  event.preventDefault();event.stopImmediatePropagation();b.x=Math.max(0,Math.min(row().width-b.width,b.x+(event.key==='ArrowLeft'?-step:event.key==='ArrowRight'?step:0)));b.y=Math.max(0,Math.min(row().height-b.height,b.y+(event.key==='ArrowUp'?-step:event.key==='ArrowDown'?step:0)));manualLanes.overlay(1);$(`[data-manual-lane="${el.dataset.manualLane}"]`)?.focus();
},true);
