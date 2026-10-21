'use strict';

// Identity and original-coordinate review drafts; pixels and results remain tool-owned.
window.intakeWorkspace = (() => {
  const root = document.createElement('section');
  root.id = 'intake-workspace';
  root.hidden = true;
  root.setAttribute('aria-label', '仪器原图导入与分配');
  $('.workspace').before(root);
  const progress = document.createElement('section');
  const resultStage = $('#result-stage'), resultParent = resultStage.parentElement;
  const paintedMarkup = new WeakMap();
  function updateMarkup(container, markup) {
    if(paintedMarkup.get(container)===markup)return;
    const focused=container.contains(document.activeElement)?document.activeElement:null;
    const attributes=focused?[...focused.attributes].filter(a=>a.name==='id'||a.name.startsWith('data-')):[];
    const selector=attributes.map(a=>`[${a.name}="${CSS.escape(a.value)}"]`).join('');
    const occurrence=selector?$$(selector,container).indexOf(focused):-1;
    const opened=$$('details',container).map(el=>[el.querySelector('summary')?.textContent,el.open]);
    const top=container.scrollTop,left=container.scrollLeft;
    container.innerHTML=markup;paintedMarkup.set(container,markup);
    $$('details',container).forEach((el,index)=>{if(opened[index]?.[0]===el.querySelector('summary')?.textContent)el.open=opened[index][1];});
    if(selector)$$(selector,container)[occurrence]?.focus({preventScroll:true});
    container.scrollTop=top;container.scrollLeft=left;
  }
  progress.id = 'intake-batch-progress';progress.hidden = true;
  progress.setAttribute('aria-label','整批处理进度');root.before(progress);
  let followed = '', browsing = false, composing = false, navigating = false;
  const batchPolicy = () => state.intake?.workflow?.policy === 'intake_workflow@3';
  const batchReason = value => /source_width_estimate_conflicts_with_support|fixed_grid_clips_target_support/.test(value||'')?'当前槽宽无法容纳完整信号，请核对条带与标记的分界后保存范围。':/additional_signal_at_target_row/.test(value||'')?'目标附近还有未能排除的信号，请核对完整范围后继续。':/group_signal_coordinates_unverified/.test(value||'')?'同组图片的位置证据不一致，请在所选原图核对范围。':/target_frame_exceeds_membrane/.test(value||'')?'范围超出可确认的膜内区域，请调整裁剪框。':/lane_spacing_ambiguous|lane_shape_ambiguous/.test(value||'')?'泳道结构尚不明确，请核对全部 N 个槽位。':/signal_orientation_insufficient/.test(value||'')?'条带方向证据不足，请核对原图范围和角度后继续。':/signal_orientation_ambiguous/.test(value||'')?'条带方向不一致，请核对本次目标和角度后继续。':/signal_rows_ambiguous|signal_target_overlap|guide_multiple_membranes/.test(value||'')?'当前范围包含多个可能目标，请明确本次条带范围后继续。':/guided_target_ambiguous/.test(value||'')?'检测到多个条带区域，请在原图明确本次目标范围后继续。':/explicit_lane_count_conflicts|guided_target_not_supported/.test(value||'')?'尚未取得与 N 一致的完整条带，请核对 N 或在原图明确范围后继续。':/crop_policy|automatic_geometry|membrane_not_found|no_reliable_membrane/.test(value||'') ? '未能确定完整裁剪范围，请在对应原图框选包含全部样本槽位的整行范围，保存后继续。' : value || '';
  function noteBrowse(){if(batchPolicy()&&state.intake?.automation?.follow&&!navigating){browsing=true;renderProgress();}}
  const phaseNames = {crop:'原图裁剪',compose:'完整 Fig 拼图',measure:'原像素定量',export:'结果输出',complete:'统一结果'};
  const live = document.createElement('div');
  live.className = 'sr-only';
  live.id = 'intake-live-status';
  Object.assign(live.style, {position: 'absolute', width: '1px', height: '1px', padding: '0', overflow: 'hidden', clipPath: 'inset(50%)', whiteSpace: 'nowrap'});
  live.setAttribute('role', 'status');
  live.setAttribute('aria-live', 'polite');
  live.setAttribute('aria-atomic', 'true');
  root.after(live);
  let renderedWorkflow = null, focusAction = null;
  let key = '', baseDigest = '', basePlan = '', draft = null, batch = [], selected = new Set();
  let conflict = false, pending = null, replace = false, allowReuse = false, filter = '';
  const cropDrafts = new Map(), cropPending = new Map();
  let cropSavedRow = null, cropFocusAction = null, chosenFigureId = null;
  let resultPage = 0, stagePage = 0;
  let previewRequested = '';
  let cropInspectorRow = null;
  const originalTabs = new Map($$('.mode-tab').map(tab=>[tab,tab.innerHTML]));
  let discoveryKey = '', discoveryDirty = false;
  const discoveryChoices = new Map();
  const copyPlan = intake => ({
    figures: intake.figures.map(item => ({...item})),
    proteins: intake.proteins.map(item => ({...item}))
  });
  const planText = value => JSON.stringify(copyPlan(value));
  const planDirty = () => !!draft && planText(draft) !== basePlan;
  const hasDraft = () => window.intakeGrid.hasDraft() || window.intakeQuant.hasDraft() || window.intakeGroups.hasDraft() || discoveryDirty || planDirty() || batch.length > 0 || cropDrafts.size > 0;
  const guard = () => ({projectId: state.projectId, sessionEpoch: state.sessionEpoch, digest: baseDigest});
  const uid = () => crypto.randomUUID();
  const source = id => state.intake?.sources.find(item => item.source_id === id);
  const assigned = id => state.intake?.assignments.filter(item => item.source_id === id) || [];
  const targetName = id => {
    const protein = draft?.proteins.find(item => item.protein_id === id);
    const fig = draft?.figures.find(item => item.figure_id === protein?.figure_id);
    const peers = draft?.proteins.filter(item => item.figure_id === protein?.figure_id) || [];
    return protein ? `${fig?.label || 'Fig'} / ${protein.label || '未命名蛋白'} · 第 ${peers.indexOf(protein) + 1} 行` : '未分配';
  };

  function reset() {
    if(root.contains(resultStage))resultParent.append(resultStage);
    previewRequested='';
    followed = '';browsing = false;composing = false;progress.hidden = true;
    window.intakeGroups.reset();window.intakeQuant.reset();window.intakeGrid.reset();
    discoveryKey = ''; discoveryDirty = false; discoveryChoices.clear();
    cropDrafts.clear(); cropPending.clear();
    cropSavedRow = null;
    cropFocusAction = null; chosenFigureId = null; resultPage = 0; stagePage = 0;
    renderedWorkflow = null; focusAction = null; live.textContent = '';navigating=false;
    key = ''; baseDigest = ''; basePlan = ''; draft = null; batch = []; selected.clear();
    conflict = false; pending = null; replace = false; allowReuse = false; filter = '';
  }
  function sync() {
    const intake = state.intake;
    if (!intake) { reset(); return; }
    const nextKey = `${state.sessionEpoch}:${state.projectId}`;
    if (nextKey !== key) {
      reset(); key = nextKey; baseDigest = intake.digest; draft = copyPlan(intake); basePlan = planText(intake);
      window.intakeGroups.sync();
      syncCrops();
      return;
    }
    window.intakeGroups.sync();
    // Only acknowledge the exact submitted draft, never an unrelated later snapshot.
    if (pending?.kind === 'plan' && planText(intake) === pending.value) {
      if (draft && planText(draft) === pending.value) draft = copyPlan(intake);
      pending = null; baseDigest = intake.digest; basePlan = planText(intake); conflict = false;
    } else if (pending?.kind === 'assign' && pending.value.every(binding =>
      intake.assignments.some(item => item.protein_id === binding.protein_id && item.source_id === binding.source_id))) {
      if (JSON.stringify(batch) === JSON.stringify(pending.value)) batch = [];
      selected.clear(); pending = null; baseDigest = intake.digest; basePlan = planText(intake);
      conflict = false; replace = false; allowReuse = false;
    }
    if (pending?.kind === 'discovery' && intake.discovery?.selections &&
        JSON.stringify(intake.discovery.selections) === JSON.stringify(pending.value)) {
      if (JSON.stringify([...discoveryChoices.values()]) === pending.draftValue) {
        discoveryDirty=false; discoveryChoices.clear();
      }
      pending=null;
    }
    if (intake.digest !== baseDigest) {
      if (hasDraft()) conflict = true;
      else { draft = copyPlan(intake); basePlan = planText(intake); baseDigest = intake.digest; conflict = false; }
    }
    syncCrops();
  }

  const cropBox = roi => roi ? {x:roi.x0,y:roi.y0,width:roi.x1-roi.x0,height:roi.y1-roi.y0} : null;
  const cropGuard = () => ({...guard(), workflowDigest:state.intake.workflow.digest});
  function syncCrops() {
    if (!state.intake?.cropEnabled) return;
    for (const r of state.rows) {
      const evidence = state.intake.crops?.find(e => e.row_id === r.id);
      const submitted = cropPending.get(r.id);
      const step = state.intake.workflow.steps.find(s=>s.stage==='crop'&&s.target_id===r.id);
      if (submitted && evidence?.reviewed && (submitted.displayAngle==null||Math.abs((evidence.displayFrame?.angle_degrees||0)-submitted.displayAngle)<1e-7) && (step?.status === 'pending' || batchPolicy() && ['running','done'].includes(step?.status)) && submitted.digest !== state.intake.workflow.digest && JSON.stringify(cropBox(evidence.crop)) === JSON.stringify(submitted.roi)) {
        const newer=cropDrafts.get(r.id);
        if(newer && (JSON.stringify(newer.roi)!==JSON.stringify(submitted.roi)||(newer.displayAngle??null)!==(submitted.displayAngle??null))) {
          newer.original={...submitted.roi};newer.digest=state.intake.workflow.digest;newer.conflict=false;
          newer.history=[{...submitted.roi},{...newer.roi}];newer.angleHistory=[submitted.displayAngle,newer.displayAngle];newer.index=1;
          live.textContent='已保存提交的范围；之后的新调整仍保留为草稿。';
        } else {
          cropDrafts.delete(r.id);
          cropSavedRow = mode === 'review' ? r.id : null;
          live.textContent = '裁剪范围已保存，可继续生成原值裁剪。';
        }
        cropPending.delete(r.id);
      }
      const draft = cropDrafts.get(r.id);
      if (draft) {
        draft.conflict = draft.digest !== state.intake.workflow.digest;
        r.roi = draft.roi; r.draft = true;
        r.reason = draft.conflict ? '后台输入已改变；裁剪草稿保留，请放弃后重新核对。' : '原图裁剪草稿，尚未确认保存。';
      } else if (!r.roi && evidence?.crop) {
        r.roi = cropBox(evidence.crop); r.cropStatus = 'pending';
        r.reason = evidence.reason;
      }
    }
  }
  function cropEditable(id) {
    if (state.intake?.workflow?.editing) return false;
    const step = state.intake?.workflow?.steps.find(s=>s.stage==='crop'&&s.target_id===id);
    const evidence=state.intake?.crops?.find(e=>e.row_id===id);
    return !!step && (['needs_review','failed','cancelled','interrupted','done'].includes(step.status) || step.status==='pending'&&evidence?.reviewed&&!evidence.raw_crop);
  }
  function stageCrop(next, before, paint = true) {
    const r = row();
    if (!r || state.busy || !state.intake?.cropEnabled) return;
    if (!cropEditable(r.id)) { r.roi = before; render(); return; }
    let draft = cropDrafts.get(r.id);
    if (!draft) {
      draft = {roi:before, original:before, digest:state.intake.workflow.digest, history:[before], angleHistory:[undefined], index:0, conflict:false};
      cropDrafts.set(r.id, draft);
    }
    draft.history = draft.history.slice(0,draft.index+1); draft.history.push({...next}); draft.index++;
    draft.angleHistory=(draft.angleHistory||[]).slice(0,draft.index);draft.angleHistory.push(draft.displayAngle);
    draft.roi = {...next}; r.roi = draft.roi; r.draft = true;
    live.textContent = '裁剪草稿已调整，确认后才保存；尚未生成原值裁剪。';
    if (paint) render();
  }
  function undoCrop(redo) {
    const r = row(), draft = r && cropDrafts.get(r.id);
    if (!draft || state.busy || state.intake?.workflow?.editing) return;
    const index = draft.index + (redo ? 1 : -1);
    if (index < 0 || index >= draft.history.length) return;
    draft.index = index; draft.roi = draft.history[index]; r.roi = draft.roi;
    draft.displayAngle=draft.angleHistory?.[index];
    render();
  }
  function syncCropControls(r) {
    const evidence=state.intake.crops?.find(e=>e.row_id===r?.id);
    const step=state.intake.workflow.steps.find(s=>s.stage==='crop'&&s.target_id===r?.id);
    const draft=r&&cropDrafts.get(r.id),correcting=step?.status==='done';
    // Legacy cropPending tracks the saved-snapshot acknowledgement, not an
    // active request; failed saves must retain the original retry action.
    const locked=!!state.busy||!r?.roi||!evidence||!cropEditable(r.id)||!!draft?.conflict||(batchPolicy()&&!!cropPending.size);
    const saved=batchPolicy()&&correcting&&!draft;
    $$('[data-intake-crop-action="confirm"]').forEach(button=>{
      button.disabled=locked||((correcting||step?.status==='pending')&&!draft);button.hidden=saved;
    });
    $$('[data-intake-crop-action="run"]').forEach(button=>{
      button.disabled=batchPolicy()?locked:!!state.busy||hasDraft()||!runnable();button.hidden=saved;
    });
    $$('[data-intake-crop-action="discard"]').forEach(button=>button.disabled=!!state.busy||!draft);
    const notice=draft?.conflict?'后台输入已改变，草稿保留；放弃后重新核对。':
      ['needs_review','failed'].includes(step?.status)?batchReason(evidence?.reason):'';
    $$('[data-intake-crop-notice]').forEach(node=>{node.textContent=notice;node.hidden=!notice;});
    if(!saved)$$('.intake-saved-note').forEach(note=>note.remove());
  }
  function renderCropInspector(r) {
    const focused = document.activeElement;
    // A progress snapshot must not replace the input under a user's caret/IME.
    // The change handler commits its draft without replacing a pressed action.
    if(cropInspectorRow===r?.id&&focused?.matches('[data-intake-rotation]')){
      focused.disabled=!!state.busy||!cropEditable(r.id);
      syncCropControls(r);
      drawRotationPreview(r,state.intake.crops?.find(e=>e.row_id===r.id),cropDrafts.get(r.id));
      return;
    }
    cropInspectorRow=r?.id;
    const actionFocus = document.activeElement?.dataset.intakeCropAction;
    if (actionFocus) cropFocusAction = actionFocus;
    else if (!$('.inspector').contains(document.activeElement)) cropFocusAction = null;
    const evidence = state.intake.crops?.find(e => e.row_id === r?.id);
    const step = state.intake.workflow.steps.find(s => s.stage === 'crop' && s.target_id === r?.id);
    const draft = r && cropDrafts.get(r.id);
    const correcting = step?.status === 'done';
    const reviewable = r && cropEditable(r.id);
    $('#inspector-title').textContent = '裁剪信息';
    $('#review-badge').textContent = draft ? '未保存' : evidence?.raw_crop ? '原值已保存' : step?.status==='needs_review' ? '需调整' : '待处理';
    $('#review-badge').className = 'status-badge '+(evidence?.raw_crop?'ok':'pending');
    $('#inspector-content').innerHTML = `<section class="inspect-section"><h3>${r?escapeText(targetName(r.id)):'请选择蛋白行'}</h3>${dataPair('固定槽位数',r?.lanes||0)}${dataPair('裁图',evidence?.raw_crop?(['intake_crop@2','intake_crop@3'].includes(evidence.policy)?'自动定位已保存':'已保存'):'待处理')}<p class="row-reason" data-intake-crop-notice role="status" hidden></p><details><summary>范围与槽位说明</summary><p>在原图调整整行范围。手动确认按固定 N 等宽分割；无信号槽位保留。</p><p>${escapeText(evidence?.reason||'尚未定位')}</p></details></section>`;
    if(r?.roi){
      const angle=draft?.displayAngle??evidence?.displayFrame?.angle_degrees??0;
      $('#inspector-content').insertAdjacentHTML('beforeend',`<section class="inspect-section"><h3>裁图纠偏</h3><canvas class="intake-rotation-preview" aria-label="纠偏后的裁图预览"></canvas><label>角度（度）<input data-intake-rotation type="number" min="-10" max="10" step="0.1" value="${Number(angle).toFixed(2)}" ${state.busy||!reviewable?'disabled':''}></label><button class="text-button" data-intake-reset-rotation ${state.busy||!reviewable?'disabled':''}>恢复不旋转</button><small>纠偏用于显示与拼图；定量范围保持原图坐标。</small></section>`);
      drawRotationPreview(r,evidence,draft);
    }
    if(batchPolicy()&&evidence?.reason&&batchReason(evidence.reason)!==evidence.reason)$('#inspector-content').insertAdjacentHTML('beforeend',`<details class="inspect-section"><summary>处理详情</summary><p class="row-reason">${escapeText(evidence.reason)}</p></details>`);
    if (correcting&&draft) $('#inspector-content').insertAdjacentHTML('beforeend','<p class="row-reason">保存后重算本 Fig；其他 Fig 和历史文件保留。</p>');
    $('#inspector-action').innerHTML = `<button class="button primary full" data-intake-crop-action="confirm" disabled>${correcting?'保存修正，标记本 Fig 待重算':'确认此范围与固定槽位'}</button><button class="button subtle full" data-intake-crop-action="run" disabled>继续处理批次</button><button class="text-button" data-intake-crop-action="discard" disabled>放弃本行裁剪草稿</button><button class="text-button" data-intake-crop-action="back">返回清单与异常</button>`;
    if (batchPolicy()) {
      const saveOnly=$('[data-intake-crop-action="confirm"]');saveOnly.textContent='仅保存范围';saveOnly.className='text-button';
      const resume=$('[data-intake-crop-action="run"]');
      resume.textContent='保存范围并继续自动处理';resume.className='button primary full';
      if(correcting&&!draft){saveOnly.hidden=true;resume.hidden=true;$('#inspector-action').insertAdjacentHTML('afterbegin','<p class="intake-saved-note">此图已保存，无需确认。</p>');}
    }
    syncCropControls(r);
    const focus = cropSavedRow === r?.id ? 'run' : cropFocusAction;
    cropSavedRow = null;
    if (focus) {
      const target = $(`[data-intake-crop-action="${focus}"]:not(:disabled)`) || $('#inspector-title');
      if (!target.matches('button')) target.setAttribute('tabindex','-1');
      target.focus({preventScroll:true});
    }
    if (cropPending.size && state.status && live.textContent !== state.status) live.textContent = state.status;
  }
  function drawRotationPreview(r,evidence,draft){
    const canvases=$$('.intake-rotation-preview');if(!canvases.length||!r?.preview||!r.roi)return;
    const roi=r.roi,angle=draft?.displayAngle??evidence?.displayFrame?.angle_degrees??0;
    const rad=angle*Math.PI/180,c=Math.cos(rad),s=Math.sin(rad);
    const factor=Math.min(roi.width/(roi.width*Math.abs(c)+roi.height*Math.abs(s)),roi.height/(roi.width*Math.abs(s)+roi.height*Math.abs(c)));
    const frame=draft?.displayAngle==null&&evidence?.displayFrame&&JSON.stringify(roi)===JSON.stringify(cropBox(evidence.crop))?evidence.displayFrame:{center_x:roi.x+roi.width/2,center_y:roi.y+roi.height/2,width:roi.width*factor,height:roi.height*factor};
    const width=Math.min(420,Math.round(frame.width)),height=Math.max(1,Math.round(width*frame.height/frame.width));
    for(const canvas of canvases){
      const paint=Symbol();rotationPaints.set(canvas,paint);
      canvas.width=width;canvas.height=height;
      const image=new Image();image.onload=()=>{
        if(!canvas.isConnected||rotationPaints.get(canvas)!==paint)return;
        const ctx=canvas.getContext('2d'),sx=width/frame.width,sy=height/frame.height;
        ctx.setTransform(sx*c,-sy*s,sx*s,sy*c,width/2-sx*(c*frame.center_x+s*frame.center_y),height/2+sy*(s*frame.center_x-c*frame.center_y));
        ctx.drawImage(image,0,0,r.width,r.height);
      };image.src=r.preview;
    }
  }
  const rotationPaints=new WeakMap();
  function syncInspectorDrawer() {
    if(!state.intake?.cropEnabled||mode!=='review')return false;
    const focused=document.activeElement;
    if(!focused?.matches('[data-intake-rotation]'))updateMarkup($('#drawer-content'),$('#inspector-content').innerHTML+$('#inspector-action').innerHTML);
    const r=row();
    drawRotationPreview(r,state.intake.crops?.find(e=>e.row_id===r?.id),cropDrafts.get(r?.id));
    return true;
  }
  function stageRotation(value, paint = true){
    const r=row(),angle=Number(value);
    if(value===''||!r?.roi||state.busy||!cropEditable(r.id)||!Number.isFinite(angle)||Math.abs(angle)>10)return;
    stageCrop({...r.roi},r.roi,false);const draft=cropDrafts.get(r.id);draft.displayAngle=angle;draft.angleHistory[draft.index]=angle;
    if(paint){render();return;}
    // Number inputs emit change between a button's mousedown and mouseup.
    // Keep those DOM nodes alive so that the same press can finish its click.
    $('#review-badge').textContent='未保存';
    syncCropControls(r);
    drawRotationPreview(r,state.intake.crops?.find(e=>e.row_id===r.id),draft);
    updateChrome();renderSourceList();
  }
  document.addEventListener('change',event=>{if(event.target.matches('[data-intake-rotation]'))stageRotation(event.target.value,false);});
  document.addEventListener('click',event=>{if(event.target.closest('[data-intake-reset-rotation]'))stageRotation(0);});
  function cropActions(step) {
    if (!state.intake.cropEnabled) return '';
    if(step.stage==='export'&&state.intake.outputEnabled){
      const retry=['failed','cancelled','interrupted'].includes(step.status);
      return `<span class="intake-stage-actions"><button class="text-button" data-intake-crop-action="export" ${state.busy||hasDraft()||!bridge?'disabled':''}>保存当前快照到新目录</button>${retry?`<button class="text-button" data-intake="retry-stage" data-stage="export" data-id="${escapeText(step.target_id)}" ${state.busy||hasDraft()?'disabled':''}>重试完整输出</button>`:''}</span>`;
    }
    if(step.stage!=='crop'){
      if(!state.intake.figureEnabled||!['compose','measure'].includes(step.stage))return '';
      const saved=state.intake.figuresReady?.some(f=>f.figure_id===step.target_id);
      const retry=['needs_review','failed','cancelled','interrupted'].includes(step.status);
      return `<span class="intake-stage-actions">${saved?`<button class="text-button" data-intake="view-figure" data-id="${escapeText(step.target_id)}" ${state.busy||hasDraft()?'disabled':''}>查看本 Fig</button>`:''}${step.stage==='measure'&&step.status==='done'?'<button class="text-button" data-intake="view-results">查看测量记录</button>':''}${retry?`<button class="text-button" data-intake="retry-stage" data-stage="${step.stage}" data-id="${escapeText(step.target_id)}" ${state.busy||hasDraft()?'disabled':''}>重试本 Fig</button>`:''}</span>`;
    }
    const reviewable = ['needs_review','failed','cancelled','interrupted'].includes(step.status);
    return `<span class="intake-stage-actions"><button class="text-button" data-intake="review-crop" data-id="${escapeText(step.target_id)}" ${state.busy?'disabled':''}>查看原图${reviewable?'并复核':''}</button>${reviewable?`<button class="text-button" data-intake="retry-crop" data-id="${escapeText(step.target_id)}" ${state.busy||hasDraft()?'disabled':''}>重试本行</button>`:''}</span>`;
  }

  const allowedModes = () => state.intake?.workflow?.editing ? ['intake'] : ['intake', ...(state.intake?.cropEnabled?['review']:[]), ...(state.intake?.figureEnabled?['layout',...(batchPolicy()?['quant']:[]),'results']:[])];
  function resumeBatch() {
    if(state.busy||!bridge||!batchPolicy())return;
    const r=row(),step=state.intake.workflow.steps.find(s=>s.stage==='crop'&&s.target_id===r?.id);
    const correcting=mode==='review'&&r?.roi&&cropEditable(r.id)&&(step?.status!=='done'||cropDrafts.has(r.id));
    if(hasDraft()&&(!correcting||[...cropDrafts.keys()].some(id=>id!==r.id)||window.intakeGroups.hasDraft()||planDirty()||discoveryDirty||batch.length)){toast('请先保存或放弃其他草稿。');return;}
    const blocked=state.intake.workflow.steps.find(s=>s.stage==='crop'&&s.status==='needs_review');
    if(!correcting&&blocked){select(blocked.target_id);switchMode('review');toast('请在此原图确认裁剪范围后继续。');return;}
    const payload=cropGuard();
    if(correcting){
      if(cropDrafts.get(r.id)?.conflict)return;
      payload.rowId=r.id;payload.roi={...r.roi};payload.displayAngle=cropDrafts.get(r.id)?.displayAngle;
      cropPending.set(r.id,{roi:{...r.roi},displayAngle:payload.displayAngle,digest:state.intake.workflow.digest});
    }
    browsing=false;followed='';send('intake_sequence_continue',payload);
  }
  const topAction=document.createElement('button');
  topAction.id='intake-primary';topAction.className='button primary';topAction.hidden=true;
  $('.mode-bar').append(topAction);
  const topSummary=document.createElement('span');topSummary.className='intake-top-summary';topSummary.hidden=true;topAction.before(topSummary);
  const newFigure=document.createElement('button');newFigure.className='text-button';newFigure.id='intake-new-figure';newFigure.textContent='新建 Fig';newFigure.hidden=true;
  $('.header-actions').prepend(newFigure);
  newFigure.addEventListener('click',()=>window.intakeGroups.activate('add-fig'));
  topAction.addEventListener('click',()=>{
    if(topAction.disabled)return;
    if(!batchPolicy()||state.intake.workflow.editing){window.intakeGroups.activate('start');return;}
    if(state.busy){action('cancel');return;}
    if(state.intake.automation?.complete){if(!hasDraft())send('intake_export_table',guard());return;}
    resumeBatch();
  });
  function updateChrome(){
    const active=!!state.intake;
    $('.compact-inspect').hidden=active&&['intake','results'].includes(mode);
    document.body.classList.toggle('intake-project',active);
    $('.intake-brand').hidden=!active;
    const configuration=active&&(!state.intake.workflow||state.intake.workflow.editing);
    const setup=configuration?window.intakeGroups.startState():null;
    const batch=active&&batchPolicy()&&!state.intake.workflow.editing;
    topAction.hidden=topSummary.hidden=!(setup?.available||batch);
    newFigure.hidden=!setup?.available;newFigure.disabled=!!setup?.locked;
    if(setup?.available){
      topAction.textContent='开始自动处理';topAction.disabled=setup.disabled;
      topSummary.textContent=`${setup.count} 个蛋白 · ${setup.figures} 个 Fig`;
    }else if(batch){
      const a=state.intake.automation;
      const current=state.intake.workflow.steps.find(s=>s.stage==='crop'&&s.target_id===row()?.id);
      const reviewing=mode==='review'&&(current?.status==='needs_review'||cropDrafts.has(row()?.id));
      topAction.textContent=state.busy?'暂停处理':a?.complete?'导出结果表':reviewing?'保存范围并继续':'继续自动处理';
      topAction.disabled=!bridge||!!cropPending.size||!!(a?.complete&&hasDraft())||!!(state.busy&&!a?.phase);
      topSummary.textContent=`${state.intake.proteins.length} 个蛋白 · ${state.intake.figures.length} 个 Fig`;
    }
    const keys=['intake','review','layout','quant','results'];
    const labels=['配置原图','自动裁图','拼图排版','灰度定量','结果表'];
    $$('.mode-tab').forEach(tab=>{
      if(!active){if(tab.querySelector('.mode-step'))tab.innerHTML=originalTabs.get(tab);tab.classList.remove('stage-complete');return;}
      const index=keys.indexOf(tab.dataset.mode);if(index<0)return;
      if(!tab.querySelector('.mode-step'))tab.innerHTML=`<span class="mode-step"></span><span>${labels[index]}</span>`;
      const stage=['','crop','compose','measure','export'][index];
      const steps=state.intake.workflow?.steps.filter(s=>s.stage===stage)||[];
      const done=index===0?!!state.intake.workflow&&!state.intake.workflow.editing:steps.length>0&&steps.every(s=>s.status==='done');
      tab.querySelector('.mode-step').textContent=done?'✓':index+1;
      tab.classList.toggle('stage-complete',done);
    });
  }
  function renderProgress() {
    updateChrome();
    const a=state.intake?.automation;
    progress.hidden=!batchPolicy()||!!state.intake.workflow.editing;
    if(progress.hidden)return;
    if(!progress.firstElementChild)progress.innerHTML='<span class="process-dot"></span><p role="status"></p><details><summary>处理详情</summary><div></div></details><button class="text-button" data-batch-action="follow"></button>';
    progress.classList.toggle('needs-attention',!!a?.paused&&!a?.complete);
    const target=a?.phase==='crop'?targetName(a.targetId):state.intake.figures.find(f=>f.figure_id===a?.targetId)?.label||'';
    const message=batchReason(a?.reason)||(a?.complete?'全部阶段与结果目录已保存':state.busy?'正在处理并保存':'已暂停，已保存步骤保留');
    progress.querySelector('p').textContent=[phaseNames[a?.phase]||'等待继续',target,message].filter(Boolean).join(' · ');
    progress.querySelector('details>div').textContent=[...['crop','compose','measure','export'].map(stage=>{const steps=state.intake.workflow.steps.filter(s=>s.stage===stage);return `${phaseNames[stage]} ${steps.filter(s=>s.status==='done').length}/${steps.length}`;}),a?.reason||''].filter(Boolean).join('；');
    progress.querySelector('[data-batch-action="follow"]').textContent=browsing?'跟随当前阶段':'暂停自动切页';
  }
  function renderSourceList() {
    if(!state.intake?.cropEnabled)return false;
    if(mode==='layout'){
      const list=$('#source-list'),focused=list.contains(document.activeElement)?document.activeElement:null;
      const attr=focused?.hasAttribute('data-ig-row')?'data-ig-row':'data-ig-view',id=focused?.getAttribute(attr);
      updateMarkup(list,window.intakeGrid.sidebar());$('#source-count').textContent=state.intake.figures.length;
      if(id)list.querySelector(`[${attr}="${CSS.escape(id)}"]`)?.focus({preventScroll:true});return true;
    }
    const list=$('#source-list'),focused=list.contains(document.activeElement)?document.activeElement.dataset.row:null;
    const query=$('#source-search').value.trim().toLocaleLowerCase();
    $('.source-panel').classList.remove('quant-sources');
    $('.source-panel .panel-heading h2').firstChild.nodeValue='Fig 与蛋白 ';
    $('#source-search').placeholder='查找蛋白或 Fig…';
    $('#source-search').setAttribute('aria-label','查找蛋白或 Fig');
    const attention=$('[data-filter="attention"]').classList.contains('active');
    list.innerHTML=state.intake.figures.map(fig=>{
      const proteins=state.intake.proteins.filter(p=>p.figure_id===fig.figure_id).filter(p=>{
        const r=state.rows.find(r=>r.id===p.protein_id);
        return r&&(!attention||needsAttention(r))&&`${fig.label} ${p.label} ${r.name}`.toLocaleLowerCase().includes(query);
      });
      if(!proteins.length)return '';
      return `<section class="intake-object-group"><h3>${escapeText(fig.label)}</h3>${proteins.map(p=>{
        const r=state.rows.find(r=>r.id===p.protein_id),s=state.intake.workflow?.steps.find(s=>s.stage==='crop'&&s.target_id===r.id);
        const label=r.draft?'未保存':s?.status==='done'?'已保存':s?.status==='running'?'处理中':s?.status==='needs_review'?'需调整':'待处理';
        return `<button class="source-item intake-object ${r.id===row()?.id?'active':''}" data-row="${escapeText(r.id)}" aria-pressed="${r.id===row()?.id}" title="${escapeText(r.name)}">${r.preview?`<img class="source-thumb" src="${escapeText(r.preview)}" alt="">`:''}<span class="source-copy"><strong>${escapeText(p.label)}</strong><small class="${s?.status==='done'&&!r.draft?'reviewed':''}">${label}</small></span></button>`;
      }).join('')}</section>`;
    }).join('')||'<p class="empty-list">没有符合条件的蛋白。</p>';
    if(focused)$$('[data-row]',list).find(b=>b.dataset.row===focused)?.focus({preventScroll:true});
    return true;
  }
  function followBatch() {
    const a=state.intake?.automation;
    if(!a?.follow||!a.key||browsing||!batchPolicy()||hasDraft()||composing||drag||drawing||!$('#drawer').hidden||document.querySelector('dialog[open]')||document.activeElement?.matches('input,textarea,select,[contenteditable=true]'))return;
    const event=JSON.stringify([key,a.key,a.phase,a.targetId,a.paused,a.complete]);
    if(event===followed)return;
    const next=a.complete?'results':a.phase==='crop'?'review':a.phase==='compose'?'layout':a.phase==='measure'?'quant':null;
    if(!next)return;
    followed=event;
    navigating=true;
    try{
      if(a.phase==='crop'&&state.rows.some(r=>r.id===a.targetId)&&state.selectedId!==a.targetId)select(a.targetId);
      if(['compose','measure'].includes(a.phase))chosenFigureId=a.targetId;
      if(mode!==next)switchMode(next);
    }finally{navigating=false;}
  }
  progress.addEventListener('click',event=>{
    const action=event.target.closest('[data-batch-action]')?.dataset.batchAction;
    if(action==='resume')resumeBatch();
    if(action==='follow'){browsing=!browsing;followed='';renderProgress();followBatch();}
  });
  document.addEventListener('compositionstart',()=>{composing=true;});
  document.addEventListener('compositionend',()=>{composing=false;});
  document.addEventListener('focusout',()=>{queueMicrotask(followBatch);});
  let measureZoom=1,measureFigure=null,measurementMarkup='';
  function fitMeasurement(){
    const viewport=$('.intake-measure-viewport'),raster=$('.intake-measure-raster');
    if(!viewport||!raster)return;
    const image=raster.querySelector('img');
    if(!image.naturalWidth){image.onload=fitMeasurement;return;}
    const fit=Math.min((viewport.clientWidth-48)/image.naturalWidth,(viewport.clientHeight-48)/image.naturalHeight);
    const width=Math.max(1,image.naturalWidth*fit*measureZoom);
    raster.style.width=width+'px';raster.style.marginTop=Math.max(0,(viewport.clientHeight-48-width*image.naturalHeight/image.naturalWidth)/2)+'px';
    $('[data-intake-measure-zoom="fit"]').textContent=measureZoom===1?'适应窗口':Math.round(measureZoom*100)+'%';
  }
  window.addEventListener('resize',()=>requestAnimationFrame(fitMeasurement));
  function renderBatchMeasurement() {
    const figures=state.intake.figuresReady||[];
    const selected=figures.find(f=>f.figure_id===chosenFigureId)||figures[0];
    const preview=state.intake.measurementPreview;
    const current=preview?.figureId===selected?.figure_id?preview:null;
    const request=selected?`${key}:${selected.figure_id}:${selected.image?.sha256||selected.input_digest}`:'';
    if(bridge&&request&&request!==previewRequested){
      previewRequested=request;
      send('intake_measurement_preview',{...guard(),figureId:selected.figure_id});
    }
    const members=state.intake.proteins.filter(p=>p.figure_id===selected?.figure_id);
    const regions=current?.regions||[];
    const outlines=regions.flatMap(region=>{
      const evidence=state.intake.crops.find(c=>c.row_id===region.row_id);
      const matrix=region.preview_source_to_output||region.source_to_output;
      if(!matrix||!evidence)return [];
      return evidence.slots.filter(s=>s.roi).map(s=>{
        const r=s.roi,points=[[r.x0,r.y0],[r.x1,r.y0],[r.x1,r.y1],[r.x0,r.y1]].map(([x,y])=>
          `${matrix[0][0]*x+matrix[0][1]*y+matrix[0][2]},${matrix[1][0]*x+matrix[1][1]*y+matrix[1][2]}`).join(' ');
        return `<polygon points="${points}" data-row-id="${escapeText(evidence.row_id)}"><title>${escapeText(targetName(evidence.row_id))} · 泳道 ${s.position}</title></polygon>`;
      });
    }).join('');
    const markup=window.intakeViews.measurement({intake:state.intake,selected,current,members,outlines,cells:state.cells,busy:state.busy,selectedRowId:row()?.id,quant:state.quant});
    if(markup!==measurementMarkup||!$('.intake-measure-workspace',root)){
      const focused=root.contains(document.activeElement)?document.activeElement:null;
      const attributes=['data-intake-measure-select','data-intake-measure-protein','data-intake-measure-zoom','data-intake-measure-figure','data-intake-preview-retry','data-intake-crop-action','data-id'];
      const selector=focused?attributes.filter(name=>focused.hasAttribute(name)).map(name=>`[${name}="${CSS.escape(focused.getAttribute(name))}"]`).join(''):'';
      root.innerHTML=markup;measurementMarkup=markup;
      if(selector)$(selector,root)?.focus({preventScroll:true});
    }
    if(!$('#drawer').hidden&&$('#drawer').dataset.intakeView==='measurement')updateMarkup($('#drawer-content'),$('.intake-measure-inspector').innerHTML);
    if(measureFigure!==selected?.figure_id){measureZoom=1;measureFigure=selected?.figure_id;}
    requestAnimationFrame(fitMeasurement);

  }
  root.addEventListener('change',event=>{
    if(event.target.matches('[data-intake-measure-figure]')){
      chosenFigureId=event.target.value;noteBrowse();
      const member=state.intake.proteins.find(p=>p.figure_id===chosenFigureId);
      if(member)select(member.protein_id);else renderBatchMeasurement();
    }
  });
  root.addEventListener('click',event=>{
    const figure=event.target.closest('[data-intake-measure-select]');
    if(figure){chosenFigureId=figure.dataset.intakeMeasureSelect;noteBrowse();select(figure.dataset.intakeMeasureProtein);}
    const zoomControl=event.target.closest('[data-intake-measure-zoom]');
    if(zoomControl){const action=zoomControl.dataset.intakeMeasureZoom;measureZoom=action==='fit'?1:Math.max(.25,Math.min(8,measureZoom*(action==='in'?1.25:.8)));fitMeasurement();}
    if(event.target.closest('[data-intake-preview-retry]')){previewRequested='';renderBatchMeasurement();}
    if(event.target.closest('[data-intake-table-export]')&&!state.busy&&!hasDraft())send('intake_export_table',guard());
  });
  const runnable = () => (state.intake?.workflow?.pending_ready ?? state.intake?.workflow?.steps.filter(s=>s.stage==='crop'&&s.status==='pending').length ?? 0)>0;
  function inspectMeasurement(){
    $('#drawer').dataset.intakeView='';
    if(!batchPolicy()||mode!=='quant')return false;
    openDrawer('测量记录',$('.intake-measure-inspector').innerHTML);
    paintedMarkup.set($('#drawer-content'),$('.intake-measure-inspector').innerHTML);
    $('#drawer').dataset.intakeView='measurement';return true;
  }
  function chooseFigure(id) {
    chosenFigureId=id;noteBrowse();
    if(mode!=='layout')switchMode('layout');else requestFigure();
  }
  function requestFigure() {
    if(chosenFigureId==='__all__'){
      if(!state.busy)send('intake_grid_preview',cropGuard());
      return;
    }
    const figures=state.intake?.figuresReady||[];
    const selected=figures.find(f=>f.figure_id===chosenFigureId)||figures.find(f=>f.row_ids.includes(row()?.id))||figures[0];
    if(selected&&!state.busy)send('intake_view_figure',{...cropGuard(),figureId:selected.figure_id});
  }
  function renderFigureInspector() {
    if(!state.intake?.figureEnabled||!['layout','results'].includes(mode))return false;
    const figureId=state.intake.displayFigureId||chosenFigureId;
    const fig=state.intake.figures.find(f=>f.figure_id===figureId);
    const members=state.intake.proteins.filter(p=>p.figure_id===figureId);
    $('#inspector-title').textContent=mode==='layout'?'已保存的 Fig':'原像素测量记录';
    $('#review-badge').textContent=mode==='layout'?(state.montage?'显示成图':'等待成图'):'数值与状态分列';
    $('#review-badge').className='status-badge';
    $('#inspector-content').innerHTML=mode==='layout'?`<section class="inspect-section"><h3>${escapeText(state.intake.displayFigureId==='__all__'?'全部 Fig 总图':fig?.label||'选择已完成的 Fig')}</h3><p>完整 Fig 已保存；选择蛋白行可定位；修改裁剪使用下方明确入口。</p><div class="intake-source-links">${members.map(p=>`<button class="text-button full" data-intake-crop-action="source" data-id="${escapeText(p.protein_id)}" ${state.busy?'disabled':''}>修改裁剪：${escapeText(targetName(p.protein_id))}</button>`).join('')}</div></section><section class="inspect-section"><h3>其他已保存成图</h3><div class="intake-source-links">${(state.intake.figuresReady||[]).map(f=>`<button class="text-button full" data-intake-crop-action="figure" data-id="${escapeText(f.figure_id)}" ${state.busy?'disabled':''}>${escapeText(state.intake.figures.find(x=>x.figure_id===f.figure_id)?.label||f.figure_id)}</button>`).join('')||'<p>完整 Fig 原值裁剪完成后，继续处理即可成图。</p>'}</div></section>`:`<section class="inspect-section"><h3>结果与原图一一对应</h3><p>按 Fig、蛋白和泳道查看数值与状态。</p><details><summary>数值与状态说明</summary><p>未检测、失败或未计算保留为空；待复核积分与有效信号分列。运行完成不表示科学准确率已验收。</p></details></section>`;
    $('#inspector-action').innerHTML=`${mode==='layout'?'<button class="button primary full" data-intake-crop-action="results">查看测量记录</button>':''}<button class="button subtle full" data-intake-crop-action="back">返回阶段与异常</button>`;
    if(mode==='layout')$('#inspector-content').insertAdjacentHTML('beforeend',window.intakeGrid.inspector());
    $('#inspector-content').insertAdjacentHTML('beforeend',outputInfo());
    return true;
  }
  function outputInfo() {
    if(!state.intake?.outputEnabled)return '';
    const output=state.intake.output, latest=(state.intake.outputs||[]).find(item=>item.destination===output?.path);
    const status=output?.path?(output.committed?(output.current===false?'历史快照已保留；当前输入已变化，需要重新输出':latest?.complete?'完整快照已登记':'部分快照已登记，未完成项仍需处理'):(state.busy?'目录已发布，正在登记项目':'目录已发布，项目尚未登记；已生成文件保留')):'完整批次完成后自动输出；也可先保存含未完成项的快照。';
    return `<section class="inspect-section intake-output-info"><h3>结果快照</h3><p role="status">${escapeText(status)}</p>${output?.path?`<p class="intake-output-path">${escapeText(output.path)}</p>`:''}<details><summary>快照包含什么</summary><p>每次保存到新目录，包含 CSV / Excel、裁图、Fig、状态报告和恢复归档。</p></details>${latest?.errors?.length?`<details><summary>${latest.errors.length} 项缺口</summary><ul>${latest.errors.map(error=>`<li>${escapeText(error)}</li>`).join('')}</ul></details>`:''}<button class="button subtle full" data-intake-crop-action="export" ${state.busy||hasDraft()||!bridge?'disabled':''}>${output?.path?'重新导出到新目录':'保存当前结果快照'}</button></section>`;
  }
  function renderIntakeResults() {
    const pageSize=200, pages=Math.max(1,Math.ceil(state.cells.length/pageSize));
    resultPage=Math.max(0,Math.min(resultPage,pages-1));
    const start=resultPage*pageSize;
    const labels={valid:'有效',quality_review:'质量待复核',not_detected:'未检测到',invalid:'无效',excluded:'已排除',not_run:'待计算',unconfigured:'待配置',pending_review:'待复核',failed:'失败',cancelled:'已取消',interrupted:'未完整提交',result_unavailable:'结果不可用',missing_source:'缺少原图',stale:'输入已变化'};
    $('.result-intro h3').textContent='原像素测量记录';
    $('.result-intro p').textContent='完整 Fig 保存后计算 · 缺失和失败留空 · 原始积分不等于有效信号';
    $('.results-scroll thead',resultStage).innerHTML='<tr><th>Fig / 蛋白行</th><th>固定槽位</th><th>有效信号</th><th>原始积分</th><th>状态</th></tr>';
    updateMarkup($('#results-body'),state.cells.slice(start,start+pageSize).map(c=>`<tr><td><button class="text-button full" data-intake-crop-action="source" data-id="${escapeText(c.rowId)}" data-record-lane="${c.lane}" ${state.busy?'disabled':''}>${escapeText(targetName(c.rowId))}</button></td><td>${c.lane}</td><td>${number(c.value)}</td><td>${number(c.rawIntegral)}</td><td><span class="result-state">${escapeText(labels[c.status]||'待处理')}</span>${c.reason?(c.status==='valid'?`<details><summary>计算说明</summary><p>${escapeText(c.reason)}</p></details>`:`<small>${escapeText(c.reason)}</small>`):''}</td></tr>`).join('')||'<tr><td colspan="5">尚无测量记录；请先复核原图，再继续处理完整 Fig。</td></tr>');
    $('#result-count').textContent=`${state.cells.length} 个固定槽位记录${pages>1?` · 第 ${start+1}–${Math.min(start+pageSize,state.cells.length)} 项`:''}`;
    $('.table-footer>span:last-child').innerHTML=pages>1?`<button class="text-button" data-intake-crop-action="previous-results" ${resultPage===0||state.busy?'disabled':''}>上一页</button><span role="status">第 ${resultPage+1} / ${pages} 页</span><button class="text-button" data-intake-crop-action="next-results" ${resultPage===pages-1||state.busy?'disabled':''}>下一页</button>`:'输出包在结果输出阶段生成';
  }
  function renderDiscovery(disabled) {
    if (state.intake.workflow) return '';
    const report = state.intake.discovery;
    if (discoveryKey !== baseDigest) {
      discoveryKey = baseDigest; discoveryDirty = false; discoveryChoices.clear();
    }
    const button = `<button class="button subtle" data-intake="discover" ${disabled} ${hasDraft()||!state.intake.sources.length?'disabled':''}>识别导出组与条带</button>`;
    if (!report) return `<section class="intake-summary"><div><h2>自动整理原图</h2><p>导入文件夹后识别信号、白光与合并图，并提出条带和 N 候选。未知信息集中核对。</p></div>${button}</section>`;
    const labels = {signal:'信号图候选',merge:'合并图候选',white:'白光图候选',reference:'处理结果候选',unknown:'角色待确认'};
    const grouped = new Map();
    report.observations.forEach(o=>{if(!grouped.has(o.group_id))grouped.set(o.group_id,[]);grouped.get(o.group_id).push(o);});
    const rows = [...grouped.entries()].filter(([,items])=>items.some(o=>o.role!=='reference')).map(([id,items])=>{
      let choice = discoveryChoices.get(id);
      if (!choice) {
        const suggestion=items.find(o=>o.role==='signal')||items[0], src=source(suggestion.source_id);
        const parts=src.relative_path.split('/');
        choice={include:false,source_id:suggestion.source_id,figure_label:parts.length>1?parts.at(-2):'',protein_label:src.original_name.split(/_\d{6}/)[0].replace(/\.tiff?$/i,''),lane_count:'',region_index:''};
        discoveryChoices.set(id,choice);
      }
      const observation=items.find(o=>o.source_id===choice.source_id),src=source(choice.source_id);
      const field=(name,label,value,type='text')=>`<label>${label}<input data-intake-field="discovery-${name}" data-id="${id}" type="${type}" value="${escapeText(String(value))}" ${disabled} ${type==='number'?'min="1" max="96"':''}></label>`;
      return `<li><label><input type="checkbox" data-discovery-include="${id}" ${choice.include?'checked':''} ${disabled}>纳入本次清单</label><p>${escapeText(src.relative_path)}</p><div class="intake-stage-actions">${items.map(o=>{const s=source(o.source_id);return `<figure>${s.preview?`<img src="${escapeText(s.preview)}" width="128" alt="${escapeText(labels[o.role])}">`:''}<figcaption>${escapeText(labels[o.role])}</figcaption></figure>`;}).join('')}</div><label>原图来源<select data-intake-field="discovery-source_id" data-id="${id}" ${disabled}>${items.map(o=>`<option value="${escapeText(o.source_id)}" ${choice.source_id===o.source_id?'selected':''}>${escapeText(source(o.source_id).original_name)} · ${labels[o.role]}</option>`).join('')}</select></label><div class="intake-stage-actions">${field('figure_label','Fig',choice.figure_label)}${field('protein_label','蛋白',choice.protein_label)}${field('lane_count','确认 N',choice.lane_count,'number')}</div><label>目标条带<select data-intake-field="discovery-region_index" data-id="${id}" ${disabled}><option value="">稍后在原图明确框选</option>${observation.regions.map((r,i)=>`<option value="${i}" ${String(choice.region_index)===String(i)?'selected':''}>候选 ${i+1} · N 建议 ${r.lane_counts.join(' / ')||'未知'} · 倾斜 ${r.angle_degrees.toFixed(1)}° · 原图范围 ${r.x0},${r.y0}–${r.x1},${r.y1}</option>`).join('')}</select></label><p>${escapeText(observation.error||observation.reasons.join('；'))}。候选不是确认结果，后续仍在原图核对裁剪框。</p></li>`;
    }).join('');
    const references=report.observations.filter(o=>o.role==='reference');
    const editable=!state.intake.figures.length&&!state.intake.assignments.length;
    return `<section class="intake-workflow" aria-label="原图集中复核"><h2>导出组与条带建议</h2><p>${grouped.size-references.length} 组原图候选 · ${references.length} 张处理结果候选。填写 N、选择来源和目标；留空的组不会执行。建议不代表科学真值。</p>${button}${editable?`<ol>${rows}</ol><button class="button primary" data-intake="accept-discovery" ${disabled}>将勾选且核对的组建立为清单</button>`:'<p>清单已建立，识别证据随项目保留；请在下方修改清单与分配。</p>'}<details><summary>处理结果参考（逐图待核验）</summary><div class="intake-stage-actions">${references.map(o=>{const s=source(o.source_id);return `<figure>${s.preview?`<img src="${escapeText(s.preview)}" width="200" alt="人工结果候选">`:''}<figcaption>${escapeText(s.relative_path)} · 未作为训练真值</figcaption></figure>`;}).join('')}</div></details><p id="intake-discovery-message" role="status"></p></section>`;
  }

  function planError() {
    if (!draft?.figures.length) return '先添加一个 Fig。';
    if (draft.figures.some(fig => !fig.label.trim())) return '请填写每个 Fig 的名称。';
    if (new Set(draft.figures.map(fig => fig.label.trim())).size !== draft.figures.length) return 'Fig 名称不能重复。';
    if (draft.figures.some(fig => !Number.isInteger(fig.lane_count) || fig.lane_count < 1 || fig.lane_count > 96)) return '每个 Fig 的样本槽位数必须为 1–96 的整数。';
    if (draft.figures.some(fig => !draft.proteins.some(protein => protein.figure_id === fig.figure_id))) return '每个 Fig 至少添加一个蛋白。';
    if (draft.proteins.some(protein => !protein.label.trim())) return '请填写每一行的蛋白名称。';
    return '';
  }
  function batchError() {
    if (!batch.length) return '';
    if (batch.some(binding => !binding.protein_id)) return '请为分配表中的每张原图选择目标蛋白行。';
    if (new Set(batch.map(binding => binding.protein_id)).size !== batch.length) return '同一个蛋白行不能接收多张原图，请分别选择目标。';
    if (!replace && batch.some(binding => state.intake.assignments.some(item => item.protein_id === binding.protein_id && item.source_id !== binding.source_id))) return '目标已有原图；核对后勾选“替换目标已有分配”。';
    if (!allowReuse) {
      const final = new Map(state.intake.assignments.map(item => [item.protein_id, item]));
      batch.forEach(item => {
        const previous = final.get(item.protein_id);
        final.set(item.protein_id, {...item, reuse_confirmed: previous?.source_id === item.source_id && previous.reuse_confirmed});
      });
      const content = id => source(id)?.asset?.sha256 || id;
      const counts = new Map();
      final.forEach(item => counts.set(content(item.source_id), (counts.get(content(item.source_id)) || 0) + 1));
      if ([...final.values()].some(item => counts.get(content(item.source_id)) > 1 && !item.reuse_confirmed)) return '同一原图用于多个蛋白行；核对后勾选“允许原图复用”。';
    }
    return '';
  }

  function renderPlan(disabled) {
    return `<section class="intake-plan" aria-labelledby="intake-plan-title">
      <div class="intake-section-heading"><h2 id="intake-plan-title">Fig 与蛋白清单</h2><button class="text-button" data-intake="add-fig" ${disabled}>${icon('plus')}添加 Fig</button></div>
      <p class="intake-help">槽位数包含没有信号的空位，不含 Marker。同 Fig 仅共享数量，不默认样本顺序相同。</p>
      <div class="intake-fig-list">${draft.figures.map((fig, index) => `<fieldset class="intake-fig"><legend>Fig ${index + 1}${state.intake.figures.some(item => item.figure_id === fig.figure_id) ? '' : `<button class="text-button" data-intake="remove-new-fig" data-id="${escapeText(fig.figure_id)}" ${disabled}>撤销新增 Fig</button>`}</legend>
        <div class="intake-fig-fields"><label>Fig 名称<input data-intake-field="fig-label" data-id="${escapeText(fig.figure_id)}" maxlength="120" value="${escapeText(fig.label)}" ${disabled}></label><label>样本槽位数<input data-intake-field="lanes" data-id="${escapeText(fig.figure_id)}" type="number" min="1" max="96" step="1" value="${escapeText(fig.lane_count)}" ${disabled}></label></div>
        <div class="intake-protein-label">蛋白名称</div>${draft.proteins.filter(protein => protein.figure_id === fig.figure_id).map((protein, proteinIndex) => `<div class="intake-protein"><span>${proteinIndex + 1}</span><input aria-label="${escapeText(fig.label || 'Fig')} 第 ${proteinIndex + 1} 行蛋白名称" data-intake-field="protein" data-id="${escapeText(protein.protein_id)}" maxlength="120" value="${escapeText(protein.label)}" ${disabled}><span class="intake-binding-state">${state.intake.assignments.some(item => item.protein_id === protein.protein_id) ? '已分配' : '待分配'}</span>${state.intake.proteins.some(item => item.protein_id === protein.protein_id) ? '' : `<button class="icon-button" data-intake="remove-new-protein" data-id="${escapeText(protein.protein_id)}" aria-label="撤销 ${escapeText(fig.label || 'Fig')} 第 ${proteinIndex + 1} 行新增蛋白" ${disabled}>${icon('close')}</button>`}</div>`).join('')}
        <button class="text-button" data-intake="add-protein" data-id="${escapeText(fig.figure_id)}" ${disabled}>${icon('plus')}添加蛋白行</button>
      </fieldset>`).join('') || '<p class="intake-empty">添加 Fig，填写蛋白名称和每张图的样本槽位数。</p>'}</div>
      <p id="intake-plan-error" class="intake-error" role="status"></p>
      <div class="intake-plan-actions"><button class="button primary" data-intake="save-plan">保存清单</button><button class="text-button" data-intake="reload">放弃草稿并重新载入</button></div>
    </section>`;
  }
  function renderSources(disabled) {
    const sources = state.intake.sources.filter(item => `${item.original_name} ${item.relative_path}`.toLowerCase().includes(filter.toLowerCase()));
    return `<section class="intake-pool" aria-labelledby="intake-pool-title"><div class="intake-section-heading"><div><h2 id="intake-pool-title">仪器原图</h2><p>${state.intake.sources.length} 张原图 · ${state.intake.sources.filter(item => !assigned(item.source_id).length).length} 张尚未分配</p></div><button class="button subtle" data-intake="import" ${disabled}>${icon('folder')}添加文件夹</button></div>
      ${state.intake.issues?.length ? `<details class="intake-import-issues"><summary>${state.intake.issues.length} 个文件未能导入 · 查看原因</summary><ul>${state.intake.issues.map(issue => `<li>${escapeText(issue)}</li>`).join('')}</ul><p>成功读取的原图仍可继续分配。</p></details>` : ''}<div class="intake-pool-toolbar"><label class="search-field">${icon('search')}<input type="search" data-intake-search value="${escapeText(filter)}" aria-label="查找仪器原文件名或相对路径" placeholder="查找原文件名或相对路径"></label><button class="button subtle" data-intake="stage" ${disabled}>加入分配表<span id="intake-selection-count"></span></button></div>
      <div class="intake-source-grid">${sources.map(item => `<label class="intake-source ${selected.has(item.source_id) ? 'selected' : ''}"><div class="intake-source-image">${item.preview ? `<img src="${escapeText(item.preview)}" alt="${escapeText(item.original_name)} 的原图缩略图">` : '<span>缩略图尚未载入</span>'}<input type="checkbox" data-intake-source="${escapeText(item.source_id)}" aria-label="选择 ${escapeText(item.relative_path || item.original_name)}" ${selected.has(item.source_id) ? 'checked' : ''} ${disabled}></div><strong>${escapeText(item.original_name)}</strong><small title="${escapeText(item.relative_path)}">${escapeText(item.relative_path || item.original_name)}</small><span class="intake-source-size">${item.width} × ${item.height} · ${item.bit_depth} 位${item.source_id ? ' · 来源 ' + escapeText(item.source_id.slice(-8)) : ''}</span><span class="intake-source-binding">${assigned(item.source_id).map(binding => escapeText(targetName(binding.protein_id))).join('；') || '待分配'}</span></label>`).join('') || `<p class="intake-empty">${state.intake.sources.length ? '没有匹配的原文件名。' : state.busy ? '正在读取仪器文件夹，已读取的原图会陆续显示。' : '添加仪器直接导出的 TIFF 文件夹，原文件名与原图保持不变。'}</p>`}</div>
    </section>`;
  }
  function renderBatch(disabled) {
    return `<section class="intake-batch" aria-labelledby="intake-batch-title"><div class="intake-section-heading"><h2 id="intake-batch-title">待提交的对应关系</h2><span>${batch.length} 条</span></div>
      ${batch.length ? `<p class="intake-help">逐条选择目标蛋白行，再提交本批。列表顺序不代表样本对应关系。</p><div class="intake-bindings">${batch.map((binding, index) => `<div class="intake-binding"><div class="intake-binding-source">${source(binding.source_id)?.preview ? `<img src="${escapeText(source(binding.source_id).preview)}" alt="">` : ''}<span><strong>${escapeText(source(binding.source_id)?.original_name || '原图不可用')}</strong><small>${escapeText(source(binding.source_id)?.relative_path || '')}</small></span></div><label><span>分配到</span><select data-intake-target="${index}" ${disabled}><option value="">选择 Fig / 蛋白行</option>${draft.proteins.map(protein => `<option value="${escapeText(protein.protein_id)}" ${protein.protein_id === binding.protein_id ? 'selected' : ''}>${escapeText(targetName(protein.protein_id))}</option>`).join('')}</select></label><div class="intake-binding-actions"><button class="text-button" data-intake="duplicate" data-index="${index}" ${disabled}>再分配</button><button class="icon-button" data-intake="remove-binding" data-index="${index}" aria-label="移除第 ${index + 1} 条待分配关系" ${disabled}>${icon('close')}</button></div></div>`).join('')}</div><div class="intake-permissions"><label><input type="checkbox" data-intake-permission="replace" ${replace ? 'checked' : ''} ${disabled}>替换目标已有分配</label><label><input type="checkbox" data-intake-permission="reuse" ${allowReuse ? 'checked' : ''} ${disabled}>允许原图复用到多个蛋白行</label></div><p id="intake-batch-error" class="intake-error" role="status"></p><button class="button primary" data-intake="assign">提交本批对应关系</button>` : '<p class="intake-empty">勾选上方缩略图并加入分配表，为每张原图指定 Fig 和蛋白。</p>'}
    </section>`;
  }
  function renderSummary(disabled) {
    const count = state.intake.assignments.length, total = state.intake.proteins.length;
    const workflow = state.intake.workflow;
    if (workflow) {
      const names = {crop: '原值裁剪', compose: 'Fig 拼图', measure: '原像素定量', export: '结果输出'};
      const statuses = {pending: '待处理', running: '正在处理', done: '阶段已记录', needs_review: '需要复核', failed: '失败', cancelled: '已取消', interrupted: '未完整提交'};
      const issues = workflow.steps.filter(step => ['needs_review', 'failed', 'cancelled', 'interrupted'].includes(step.status));
      const frozen = workflow.steps.some(step => step.attempt > 0) && !state.intake.grouped_draft;
      const pageSize=50, pages=Math.max(1,Math.ceil(workflow.steps.length/pageSize));
      stagePage=Math.max(0,Math.min(stagePage,pages-1));
      const start=stagePage*pageSize;
      const navigation=pages>1?`<nav class="intake-stage-actions" aria-label="阶段列表分页"><button class="text-button" data-intake="previous-stages" ${stagePage===0?'disabled':''}>上一页阶段</button><span role="status">第 ${stagePage+1} / ${pages} 页 · ${start+1}–${Math.min(start+pageSize,workflow.steps.length)} / ${workflow.steps.length} 个阶段</span><button class="text-button" data-intake="next-stages" ${stagePage===pages-1?'disabled':''}>下一页阶段</button></nav>`:'';

      return `<section class="intake-summary"><div><h2>执行计划已准备</h2><p>${state.intake.figures.length} 个 Fig · ${total} 个蛋白行 · ${state.intake.proteins.reduce((sum, row) => sum + (state.intake.figures.find(fig => fig.figure_id === row.figure_id)?.lane_count || 0), 0)} 个独立槽位。</p><p>按原值裁剪、完整 Fig 拼图、原像素定量、结果输出的顺序处理。${state.intake.figureEnabled?'完整 Fig 保存后才计算原像素；数值和质量结论分别保留。':'先核对原图定位，再保存原值裁剪；尚未生成定量结果。'}</p></div><div class="intake-stage-actions"><button class="button primary" data-intake="run" ${disabled} ${hasDraft()||!runnable()?'disabled':''}>${state.intake.figureEnabled?'继续处理':'定位与裁剪'}</button><button class="button subtle" data-intake="edit" ${disabled} ${frozen||hasDraft() ? 'disabled' : ''}>${state.intake.grouped_draft?'修改分组与对应关系':'返回清单修改'}</button></div></section>${outputInfo()}<section class="intake-workflow" aria-label="执行阶段"><h2 id="intake-stages-heading" tabindex="-1">阶段与异常</h2><p class="intake-help">已记录 ${workflow.ready_count} / ${workflow.steps.length} 个阶段。${issues.length ? `${issues.length} 项需要处理${batchPolicy()?'；整批暂停，修正后继续':'，其他完整 Fig 可以继续'}。` : '暂无异常。裁剪完成不代表科学复核通过。'}</p>${navigation}<ol start="${start+1}">${workflow.steps.slice(start, start+pageSize).map(step => `<li><span>${escapeText(names[step.stage] || step.stage)}</span><strong>${escapeText(step.stage === 'crop' ? targetName(step.target_id) : state.intake.figures.find(fig => fig.figure_id === step.target_id)?.label || state.projectName)}</strong><span>${escapeText(statuses[step.status] || step.status)}</span>${cropActions(step)}${step.reason ? `<p>${escapeText(step.reason)}</p>` : ''}</li>`).join('')}</ol>${issues.length ? `<details><summary>查看全部异常原因</summary><ul>${issues.map(step => `<li>${escapeText(names[step.stage] || step.stage)} · ${escapeText(step.target_id)}：${escapeText(step.reason)}${cropActions(step)}</li>`).join('')}</ul></details>` : ''}</section>`;
    }
    if (state.intake.confirmed) return `<section class="intake-summary"><div><h2>清单与对应关系已确认</h2><p>${count} 个蛋白行已明确分配原图。准备执行计划，预建布局位置和待计算表格，原文件保持不变。</p></div><button class="button primary" data-intake="prepare" ${disabled}>准备执行计划</button></section>`;
    return `<section class="intake-summary"><div><h2>${state.intake.confirmed ? '清单与对应关系已确认' : '确认本次导入'}</h2><p>${count} / ${total} 个蛋白行已有原图。${state.intake.confirmed ? '当前完成导入分配阶段，后续裁剪流程尚未执行。' : '核对所有蛋白行的来源后确认；未使用的原图可留在图池。'}</p></div><button class="button primary" data-intake="confirm" ${disabled}>${icon('check')}确认清单与对应关系</button></section>`;
  }
  function controls() {
    if (!draft || root.hidden) return;
    const locked = !!state.busy || !bridge || conflict || (!!state.intake.workflow && !state.intake.workflow.editing);
    const error = planError(), assignmentError = batchError();
    $('#intake-plan-error', root).textContent = batch.length ? '提交或移除待分配关系后，可继续修改清单。' : error;
    $('[data-intake="save-plan"]', root).disabled = locked || !planDirty() || !!error || batch.length > 0;
    $('[data-intake="reload"]', root).disabled = !!state.busy || !hasDraft() && !conflict;
    $('[data-intake="stage"]', root).disabled = locked || planDirty() || !draft.proteins.length || !selected.size;
    $('#intake-selection-count', root).textContent = selected.size ? `（${selected.size}）` : '';
    const submit = $('[data-intake="assign"]', root);
    if (submit) submit.disabled = locked || planDirty() || !!assignmentError;
    const batchMessage = $('#intake-batch-error', root);
    if (batchMessage) batchMessage.textContent = assignmentError;
    const confirm = $('[data-intake="confirm"]', root);
    if (confirm) confirm.disabled = locked || hasDraft() || !state.intake.proteins.length || state.intake.proteins.some(protein => !state.intake.assignments.some(binding => binding.protein_id === protein.protein_id)) || !!state.intake.confirmed;
    const prepare = $('[data-intake="prepare"]', root);
    if (prepare) prepare.disabled = locked || hasDraft() || !state.intake.confirmed;
  }
  function renderActive() {
    renderProgress();
    const measuring=batchPolicy()&&mode==='quant';
    const showingResults=batchPolicy()&&mode==='results';
    if(!showingResults&&root.contains(resultStage))resultParent.append(resultStage);
    const active = (mode === 'intake'||measuring||showingResults) && !!state.intake;
    root.hidden = !active;
    document.body.classList.toggle('intake-active', active);
    document.body.classList.toggle('grouped-intake-active', active && !!state.intake?.grouped_draft && (!state.intake.workflow || state.intake.workflow.editing));
    $$('.mode-tab').forEach(item => {item.hidden=!state.intake&&item.dataset.mode==='intake';item.disabled=!!state.intake&&!allowedModes().includes(item.dataset.mode);});
    document.body.classList.toggle('intake-crop-active', !!state.intake?.cropEnabled && mode === 'review');
    root.classList.toggle('intake-results-active',showingResults);
    root.classList.toggle('intake-measure-active',measuring);
    if (!active) return false;
    if(measuring){renderBatchMeasurement();return true;}
    if(showingResults){
      if(!$('.intake-full-records',root)){
        root.innerHTML='<div class="intake-heading"><div><h1>本次结果</h1><p>选择蛋白可返回对应原图与范围。</p></div><button class="button subtle" data-intake-table-export>导出 Excel / CSV</button></div><div data-intake-result-grid></div><details class="intake-full-records"><summary>完整测量记录 · 有效信号与状态</summary></details><div data-intake-result-output></div>';
        $('.intake-full-records',root).append(resultStage);
      }
      $('[data-intake-table-export]',root).disabled=state.busy||hasDraft();
      updateMarkup($('[data-intake-result-grid]',root),window.intakeViews.results({intake:state.intake,cells:state.cells,busy:state.busy}));
      resultStage.hidden=false;renderIntakeResults();
      updateMarkup($('[data-intake-result-output]',root),outputInfo());return true;
    }
    if ((!state.intake.workflow || state.intake.workflow.editing) && state.intake.grouped_draft) {
      const returned = renderedWorkflow === true;
      renderedWorkflow = false;
      const rendered = window.intakeGroups.render(root);
      if (returned) {
        root.scrollTop = 0;
        const heading = root.querySelector('h1');
        heading?.setAttribute('tabindex','-1');heading?.focus({preventScroll:true});
        live.textContent = '已进入分组修改。保存草稿并重新确认后才能继续处理。';
      }
      return rendered;
    }
    const focused = root.contains(document.activeElement) ? document.activeElement : null;
    const action = focused?.dataset.intake;
    const stageHeadingFocus = focused?.id === 'intake-stages-heading';
    const workflow = !!state.intake.workflow && !state.intake.workflow.editing;
    const transitioned = renderedWorkflow !== null && workflow !== renderedWorkflow;
    renderedWorkflow = workflow;
    const field = focused?.dataset.intakeField, id = focused?.dataset.id;
    const searchFocus = focused?.hasAttribute('data-intake-search');
    const caret = focused?.type === 'text' || focused?.type === 'search' ? [focused.selectionStart, focused.selectionEnd] : null;
    const scroll = root.scrollTop;
    const disabled = state.busy || !bridge || conflict ? 'disabled' : '';
    const editingDisabled = disabled || state.intake.workflow ? 'disabled' : '';
    root.innerHTML = `<div class="intake-heading"><div><h1>仪器导入与分配</h1><p>先识别导出组并集中核对，或手工填写清单与分配。原始文件保持原名。</p></div><span class="status-badge ${state.intake.confirmed ? 'ok' : 'pending'}">${state.intake.confirmed ? '已确认' : '待确认'}</span></div>${conflict ? '<div class="intake-conflict" role="alert">项目清单已在后台变化。本地草稿已保留，请核对后使用“放弃草稿并重新载入”获取最新清单。</div>' : ''}${renderDiscovery(editingDisabled)}<div class="intake-columns">${renderPlan(batch.length ? 'disabled' : editingDisabled)}<div class="intake-allocation">${renderSources(editingDisabled)}${renderBatch(editingDisabled)}</div></div>${renderSummary(disabled)}`;
    controls(); root.scrollTop = scroll;
    const summary = $('.intake-summary h2', root);
    summary?.setAttribute('tabindex', '-1');
    if (transitioned) {
      live.textContent = workflow ? '执行计划已保存并准备。' : '已返回清单修改。';
      const target = workflow ? summary : $('[data-intake-field]', root);
      target?.focus();
      focusAction = null;
      return true;
    }
    if (action) focusAction = {action, id};
    const button = focusAction ? $$('[data-intake]', root).find(item => item.dataset.intake === focusAction.action && item.dataset.id === focusAction.id && !item.disabled) : null;
    const replacement = stageHeadingFocus ? $('#intake-stages-heading',root) : searchFocus ? $('[data-intake-search]', root) : field ? $$('[data-intake-field]', root).find(item => item.dataset.intakeField === field && item.dataset.id === id) : button;
    if (replacement) { replacement.focus({preventScroll: true}); if (caret) replacement.setSelectionRange(...caret); }
    else if (focused || focusAction) summary?.focus({preventScroll: true});
    if (focusAction && state.status && live.textContent !== state.status) live.textContent = state.status;
    return true;
  }

  window.intakeGroups.bind(root);
  root.addEventListener('input', event => {
    if (state.intake?.grouped_draft && (!state.intake.workflow || state.intake.workflow.editing)) return;
    const field = event.target.dataset.intakeField, id = event.target.dataset.id;
    if (field?.startsWith('discovery-')) {
      const c=discoveryChoices.get(id); if(!c)return;
      c[field.slice(10)]=event.target.value; discoveryDirty=true;
      if(field==='discovery-source_id'){c.region_index='';renderActive();}
      return;
    }
    if (field === 'fig-label') draft.figures.find(item => item.figure_id === id).label = event.target.value;
    if (field === 'lanes') draft.figures.find(item => item.figure_id === id).lane_count = event.target.value === '' ? null : Number(event.target.value);
    if (field === 'protein') draft.proteins.find(item => item.protein_id === id).label = event.target.value;
    if (event.target.hasAttribute('data-intake-search')) { filter = event.target.value; renderActive(); }
    controls();
  });
  root.addEventListener('change', event => {
    if (state.intake?.grouped_draft && (!state.intake.workflow || state.intake.workflow.editing)) return;
    const item = event.target;
    if (item.dataset.discoveryInclude) { discoveryChoices.get(item.dataset.discoveryInclude).include=item.checked; discoveryDirty=true; }
    if (item.dataset.intakeSource) { if (item.checked) selected.add(item.dataset.intakeSource); else selected.delete(item.dataset.intakeSource); item.closest('.intake-source').classList.toggle('selected', item.checked); }
    if (item.hasAttribute('data-intake-target')) batch[Number(item.dataset.intakeTarget)].protein_id = item.value;
    if (item.dataset.intakePermission === 'replace') replace = item.checked;
    if (item.dataset.intakePermission === 'reuse') allowReuse = item.checked;
    controls();
  });
  root.addEventListener('click', event => {
    const item = event.target.closest('[data-intake]');
    if (!item || item.disabled) return;
    const action = item.dataset.intake;
    let focusFigure = null, focusAddFigure = false;
    if (action === 'discover') { if(!hasDraft())send('intake_discover',guard()); return; }
    if (action === 'accept-discovery') {
      const choices=[...discoveryChoices.values()].filter(c=>c.include);
      const message=$('#intake-discovery-message',root);
      if(!choices.length||choices.some(c=>!c.figure_label.trim()||!c.protein_label.trim()||!Number.isInteger(Number(c.lane_count))||Number(c.lane_count)<1||Number(c.lane_count)>96)){
        message.textContent='请勾选需要的组并填写 Fig、蛋白与确认 N。';return;
      }
      const selections=choices.map(({include,...c})=>({...c,lane_count:Number(c.lane_count),region_index:c.region_index===''?null:Number(c.region_index)}));
      pending={kind:'discovery',value:selections,draftValue:JSON.stringify([...discoveryChoices.values()])};
      send('intake_accept_discovery',{...guard(),selections});return;
    }
    if (action === 'add-fig') {
      const figure_id = uid(); draft.figures.push({figure_id, label: '', lane_count: null});
      draft.proteins.push({protein_id: uid(), figure_id, label: ''});
    } else if (action === 'add-protein') draft.proteins.push({protein_id: uid(), figure_id: item.dataset.id, label: ''});
    else if (action === 'remove-new-fig' && !state.intake.figures.some(fig => fig.figure_id === item.dataset.id)) {
      draft.figures = draft.figures.filter(fig => fig.figure_id !== item.dataset.id);
      draft.proteins = draft.proteins.filter(protein => protein.figure_id !== item.dataset.id);
      focusAddFigure = true;
    } else if (action === 'remove-new-protein' && !state.intake.proteins.some(protein => protein.protein_id === item.dataset.id)) {
      focusFigure = draft.proteins.find(protein => protein.protein_id === item.dataset.id)?.figure_id;
      draft.proteins = draft.proteins.filter(protein => protein.protein_id !== item.dataset.id);
    } else if (action === 'reload') { discoveryChoices.clear(); discoveryDirty=false; for (const r of state.rows) { const local=cropDrafts.get(r.id); if(local){r.roi=local.original;r.draft=false;} } cropDrafts.clear(); cropPending.clear(); syncCrops(); draft = copyPlan(state.intake); basePlan = planText(state.intake); baseDigest = state.intake.digest; batch = []; selected.clear(); conflict = false; pending = null; }
    else if (action === 'stage') { for (const source_id of selected) if (!batch.some(binding => binding.source_id === source_id)) batch.push({source_id, protein_id: ''}); selected.clear(); }
    else if (action === 'duplicate') batch.splice(Number(item.dataset.index) + 1, 0, {source_id: batch[Number(item.dataset.index)].source_id, protein_id: ''});
    else if (action === 'remove-binding') batch.splice(Number(item.dataset.index), 1);
    else if (action === 'save-plan') { pending = {kind: 'plan', value: planText(draft)}; send('intake_plan', {...guard(), ...copyPlan(draft)}); }
    else if (action === 'assign') { pending = {kind: 'assign', value: batch.map(binding => ({...binding}))}; send('intake_assign', {...guard(), bindings: batch, replace, allowReuse}); }
    else if (action === 'confirm') send('intake_confirm', guard());
    else if (action === 'run') { if(batchPolicy())resumeBatch();else if(!hasDraft())send('intake_run', cropGuard()); }
    else if (action==='previous-stages'||action==='next-stages') {
      stagePage+=action==='next-stages'?1:-1;
      renderActive();
      focusAction=null;
      $('#intake-stages-heading',root)?.focus();
      live.textContent=$('nav[aria-label="阶段列表分页"] [role="status"]',root)?.textContent||'阶段列表';
      return;
    }

    else if (action === 'review-crop') { select(item.dataset.id); switchMode('review'); const target=$('#crop-overlay').hidden?$('#image-viewport'):$('#crop-overlay'); if(target.id==='image-viewport')target.setAttribute('tabindex','-1'); target.focus(); live.textContent='已打开本行原图，请核对固定槽位范围。'; }
    else if(action==='view-figure'){chosenFigureId=item.dataset.id;switchMode('layout');}
    else if(action==='view-results')switchMode('results');
    else if(action==='retry-stage')send('intake_stage_retry',{...cropGuard(),stage:item.dataset.stage,targetId:item.dataset.id});
    else if (action === 'retry-crop') send('intake_crop_retry', {...cropGuard(), rowId:item.dataset.id});
    else if (action === 'prepare') send('intake_prepare', guard());
    else if (action === 'edit') send('intake_edit', guard());
    else if (action === 'import') { if (hasDraft()) { toast('请先保存清单、提交对应关系，或放弃草稿，再添加文件夹。'); return; } send('intake_import_folder', guard()); }
    renderActive();
    if (focusAddFigure) $('[data-intake=add-fig]', root)?.focus();
    if (focusFigure) $$('[data-intake=add-protein]', root).find(button => button.dataset.id === focusFigure)?.focus();
  });
  document.addEventListener('click', event => {
    const button = event.target.closest('[data-intake-crop-action]');
    if (!button || button.disabled || !state.intake?.cropEnabled) return;
    const action = button.dataset.intakeCropAction, r = row();
    if (action === 'back') { switchMode('intake'); return; }
    if(action==='results'){switchMode('results');return;}
    if(action==='export'&&!state.busy&&!hasDraft()&&state.intake.outputEnabled){send('intake_export',cropGuard());return;}
    if(['previous-results','next-results'].includes(action)&&!state.busy){resultPage+=action==='next-results'?1:-1;renderIntakeResults();$('.results-scroll').scrollTop=0;const next=$(`[data-intake-crop-action="${action}"]:not(:disabled)`)||$('#result-count');if(next.id==='result-count')next.setAttribute('tabindex','-1');next.focus();return;}
    if(action==='source'&&!state.busy){select(button.dataset.id);switchMode('review');return;}
    if(action==='figure'&&!state.busy){chosenFigureId=button.dataset.id;switchMode('layout');return;}
    if (!r || state.busy) return;
    if (action === 'confirm' && r.roi && !cropDrafts.get(r.id)?.conflict) {
      const completed=state.intake.workflow.steps.some(s=>s.stage==='crop'&&s.target_id===r.id&&s.status==='done');
      if (completed && !cropDrafts.has(r.id)) return;
      const displayAngle=cropDrafts.get(r.id)?.displayAngle;
      cropPending.set(r.id,{roi:{...r.roi},displayAngle,digest:state.intake.workflow.digest});
      send(completed?'intake_crop_revise':'intake_crop_review',{...cropGuard(),rowId:r.id,roi:{...r.roi},displayAngle});
    } else if (action === 'run' && batchPolicy()) resumeBatch();
    else if (action === 'run' && !hasDraft()) send('intake_run',cropGuard());
    else if (action === 'discard') {
      const draft = cropDrafts.get(r.id); r.roi = draft?.original || null; r.draft = false;
      cropDrafts.delete(r.id); cropPending.delete(r.id); syncCrops(); render();
    }
  });
  return {chooseFigure, sync, updateChrome, renderActive, hasDraft, reset, stageCrop, undoCrop, renderCropInspector, cropEditable, allowedModes, requestFigure, renderFigureInspector, renderIntakeResults, followBatch, noteBrowse, renderSourceList, inspectMeasurement, syncInspectorDrawer};
})();
