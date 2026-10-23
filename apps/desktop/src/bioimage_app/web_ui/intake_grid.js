'use strict';

window.intakeGrid = (() => {
  let draft=null, binding='', saved='', conflict=false;
  const guard=()=>({projectId:state.projectId,sessionEpoch:state.sessionEpoch,workflowDigest:state.intake?.workflow?.digest});
  function config() {
    const id=[state.projectId,state.sessionEpoch].join(':'),actual=JSON.stringify(state.intake?.grid);
    if(id!==binding){draft=null;binding=id;saved=actual;conflict=false;}else if(actual!==saved){if(draft&&JSON.stringify(draft)!==actual)conflict=true;else{draft=null;saved=actual;conflict=false;}}
    const grid=draft||state.intake?.grid||{columns:Math.min(3,state.intake?.figures?.length||1),gap:40,order:[]};
    return {...grid,order:grid.order?.length?[...grid.order]:(state.intake?.figures||[]).map(f=>f.figure_id)};
  }
  function sidebar() {
    const active=state.intake.displayFigureId;
    const ready=new Set((state.intake.figuresReady||[]).map(f=>f.figure_id));
    return `<button class="source-item" data-ig-view="__all__" aria-pressed="${active==='__all__'}">全部 Fig · 网格总图</button>`+state.intake.figures.map(f=>`<section class="intake-object-group"><button class="source-item ${active===f.figure_id?'active':''}" data-ig-view="${escapeText(f.figure_id)}" aria-pressed="${active===f.figure_id}"><strong>${escapeText(f.label)}</strong><small>${ready.has(f.figure_id)?'已保存':'等待完整成图'}</small></button>${state.intake.proteins.filter(p=>p.figure_id===f.figure_id).map(p=>`<button class="text-button full" data-ig-row="${escapeText(p.protein_id)}" data-ig-figure="${escapeText(f.figure_id)}">${escapeText(p.label)}</button>`).join('')}</section>`).join('');
  }
  function inspector() {
    const grid=config(), disabled=state.busy?'disabled':'';
    const ready=new Set((state.intake.figuresReady||[]).map(f=>f.figure_id));
    const missing=state.intake.figures.filter(f=>!ready.has(f.figure_id));
    return `<section class="inspect-section"><h3>全部 Fig 网格</h3><label class="quant-field">每行 Fig 数<input type="number" data-ig-field="columns" min="1" max="12" value="${grid.columns}" ${disabled}></label><label class="quant-field">Fig 间距（输出像素）<input type="number" data-ig-field="gap" min="2" max="1000" value="${grid.gap}" ${disabled}></label><ol class="intake-grid-order">${grid.order.map((id,i)=>`<li data-ig-order="${i}" data-ig-id="${escapeText(id)}" draggable="${!state.busy}"><span>${escapeText(state.intake.figures.find(f=>f.figure_id===id)?.label||id)}</span><button class="icon-button" data-ig-up="${i}" aria-label="上移 Fig ${i+1}" ${i===0||state.busy?'disabled':''}>${icon('chevron-up')}</button><button class="icon-button" data-ig-down="${i}" aria-label="下移 Fig ${i+1}" ${i===grid.order.length-1||state.busy?'disabled':''}>${icon('chevron-down')}</button></li>`).join('')}</ol><button class="button primary full" data-ig-save ${disabled||!draft||conflict?'disabled':''}>保存布局并预览总图</button>${conflict?'<p role="alert">布局已被更新；当前排序草稿保留。</p><button class="text-button" data-ig-reset>采用已保存布局</button>':draft?'<p>布局草稿未保存；导出仍使用已保存布局。</p>':''}<p>同行顶边、同列左边界对齐，空余留白；不拉伸条带。</p>${missing.length?`<div role="status"><strong>尚缺 ${missing.length} 个完整 Fig</strong><ul>${missing.map(f=>`<li>${escapeText(f.label)}：等待完整成图</li>`).join('')}</ul></div>`:''}<button class="button subtle full" data-ig-view="__all__" ${disabled||missing.length||draft?'disabled':''}>查看全部 Fig 总图</button><button class="button subtle full" data-ig-export="all" ${disabled||missing.length||draft?'disabled':''}>导出完整拼图 PNG / TIFF</button><button class="button subtle full" data-ig-export="single" ${disabled||!ready.has(state.intake.displayFigureId)?'disabled':''}>导出当前 Fig</button></section>`;
  }
  document.addEventListener('change',event=>{
    const field=event.target.dataset.igField;if(!field)return;
    const value=Number(event.target.value);
    if(!Number.isInteger(value)||value<(field==='columns'?1:2)||value>(field==='columns'?12:1000))return toast('请输入范围内的整数');
    draft={...config(),[field]:value};window.intakeWorkspace.renderFigureInspector();
  });
  document.addEventListener('click',event=>{
    const view=event.target.closest('[data-ig-view]');
    if(view&&!view.disabled){window.intakeWorkspace.chooseFigure(view.dataset.igView);return;}
    const protein=event.target.closest('[data-ig-row]');
    if(protein){select(protein.dataset.igRow);window.intakeWorkspace.chooseFigure(protein.dataset.igFigure);return;}
    const up=event.target.closest('[data-ig-up]'),down=event.target.closest('[data-ig-down]');
    if((up||down)&&!state.busy){const i=Number(up?.dataset.igUp??down.dataset.igDown);reorder(i,i+(up?-1:1));}
    if(event.target.closest('[data-ig-reset]')){draft=null;saved=JSON.stringify(state.intake?.grid);conflict=false;window.intakeWorkspace.renderFigureInspector();}
    if(event.target.closest('[data-ig-save]')&&!state.busy&&draft&&!conflict){window.intakeWorkspace.expectFigure('__all__');send('intake_grid_save',{...guard(),grid:draft});}
    const exp=event.target.closest('[data-ig-export]');
    if(exp&&!exp.disabled&&!state.busy)send(exp.dataset.igExport==='all'?'intake_grid_export':'intake_single_export',{...guard(),figureId:exp.dataset.igExport==='single'?state.intake.displayFigureId:undefined});
  });
  function reorder(from,to){
    const current=config();if(state.busy||from===to||to<0||to>=current.order.length)return;
    const positions=new Map([...document.querySelectorAll('[data-ig-id]')].map(el=>[el.dataset.igId,el.getBoundingClientRect().top]));
    draft=current;draft.order.splice(to,0,draft.order.splice(from,1)[0]);window.intakeWorkspace.renderFigureInspector();
    if(uiMotion.preference()==='expressive')document.querySelectorAll('[data-ig-id]').forEach(el=>{const delta=(positions.get(el.dataset.igId)??el.getBoundingClientRect().top)-el.getBoundingClientRect().top;if(delta)uiMotion.run(el,[{transform:`translateY(${delta}px)`},{transform:'none'}],220);});
  }
  let dragging=null;
  document.addEventListener('dragstart',event=>{const item=event.target.closest('[data-ig-order]');if(!item||state.busy)return;dragging=Number(item.dataset.igOrder);event.dataTransfer.effectAllowed='move';event.dataTransfer.setData('text/plain',String(dragging));item.classList.add('reordering');});
  document.addEventListener('dragover',event=>{const item=event.target.closest('[data-ig-order]');if(item&&dragging!==null){event.preventDefault();document.querySelectorAll('[data-ig-order].drop-target').forEach(el=>el.classList.remove('drop-target'));item.classList.add('drop-target');}});
  document.addEventListener('drop',event=>{const item=event.target.closest('[data-ig-order]');if(item&&dragging!==null){event.preventDefault();reorder(dragging,Number(item.dataset.igOrder));}dragging=null;});
  document.addEventListener('dragend',()=>{dragging=null;document.querySelectorAll('[data-ig-order].reordering,[data-ig-order].drop-target').forEach(el=>el.classList.remove('reordering','drop-target'));});
  return {sidebar,inspector,hasDraft:()=>{config();return !!draft;},reset:()=>{draft=null;binding='';saved='';conflict=false;}};
})();
