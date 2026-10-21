'use strict';

window.intakeGrid = (() => {
  let draft=null, binding='', saved='';
  const guard=()=>({projectId:state.projectId,sessionEpoch:state.sessionEpoch,workflowDigest:state.intake?.workflow?.digest});
  function config() {
    const id=[state.projectId,state.sessionEpoch].join(':'),actual=JSON.stringify(state.intake?.grid);
    if(id!==binding||actual!==saved){draft=null;binding=id;saved=actual;}
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
    return `<section class="inspect-section"><h3>全部 Fig 网格</h3><label class="quant-field">每行 Fig 数<input type="number" data-ig-field="columns" min="1" max="12" value="${grid.columns}" ${disabled}></label><label class="quant-field">Fig 间距（输出像素）<input type="number" data-ig-field="gap" min="2" max="1000" value="${grid.gap}" ${disabled}></label><ol class="intake-grid-order">${grid.order.map((id,i)=>`<li><span>${escapeText(state.intake.figures.find(f=>f.figure_id===id)?.label||id)}</span><button class="icon-button" data-ig-up="${i}" aria-label="上移 Fig ${i+1}" ${i===0||state.busy?'disabled':''}>${icon('chevron-up')}</button><button class="icon-button" data-ig-down="${i}" aria-label="下移 Fig ${i+1}" ${i===grid.order.length-1||state.busy?'disabled':''}>${icon('chevron-down')}</button></li>`).join('')}</ol><button class="button primary full" data-ig-save ${disabled||!draft?'disabled':''}>保存布局并预览总图</button>${draft?'<p>布局草稿未保存；导出仍使用已保存布局。</p>':''}<p>同行顶边、同列左边界对齐，空余留白；不拉伸条带。</p>${missing.length?`<div role="status"><strong>尚缺 ${missing.length} 个完整 Fig</strong><ul>${missing.map(f=>`<li>${escapeText(f.label)}：等待完整成图</li>`).join('')}</ul></div>`:''}<button class="button subtle full" data-ig-view="__all__" ${disabled||missing.length||draft?'disabled':''}>查看全部 Fig 总图</button><button class="button subtle full" data-ig-export="all" ${disabled||missing.length||draft?'disabled':''}>导出总图 PNG / TIFF</button><button class="button subtle full" data-ig-export="single" ${disabled||!ready.has(state.intake.displayFigureId)?'disabled':''}>导出当前 Fig</button></section>`;
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
    if((up||down)&&!state.busy){draft=config();const i=Number(up?.dataset.igUp??down.dataset.igDown),j=i+(up?-1:1);if(j>=0&&j<draft.order.length)[draft.order[i],draft.order[j]]=[draft.order[j],draft.order[i]];window.intakeWorkspace.renderFigureInspector();}
    if(event.target.closest('[data-ig-save]')&&!state.busy&&draft){window.intakeWorkspace.expectFigure('__all__');send('intake_grid_save',{...guard(),grid:draft});}
    const exp=event.target.closest('[data-ig-export]');
    if(exp&&!exp.disabled&&!state.busy)send(exp.dataset.igExport==='all'?'intake_grid_export':'intake_single_export',{...guard(),figureId:exp.dataset.igExport==='single'?state.intake.displayFigureId:undefined});
  });
  return {sidebar,inspector,hasDraft:()=>{config();return !!draft;},reset:()=>{draft=null;binding='';saved='';}};
})();
