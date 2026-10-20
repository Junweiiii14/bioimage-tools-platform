'use strict';

// Identity and original-coordinate review drafts; pixels and results remain tool-owned.
window.intakeWorkspace = (() => {
  const root = document.createElement('section');
  root.id = 'intake-workspace';
  root.hidden = true;
  root.setAttribute('aria-label', '仪器原图导入与分配');
  $('.workspace').before(root);
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
  let discoveryKey = '', discoveryDirty = false;
  const discoveryChoices = new Map();
  const copyPlan = intake => ({
    figures: intake.figures.map(item => ({...item})),
    proteins: intake.proteins.map(item => ({...item}))
  });
  const planText = value => JSON.stringify(copyPlan(value));
  const planDirty = () => !!draft && planText(draft) !== basePlan;
  const hasDraft = () => window.intakeGroups.hasDraft() || discoveryDirty || planDirty() || batch.length > 0 || cropDrafts.size > 0;
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
    window.intakeGroups.reset();
    discoveryKey = ''; discoveryDirty = false; discoveryChoices.clear();
    cropDrafts.clear(); cropPending.clear();
    cropSavedRow = null;
    cropFocusAction = null; chosenFigureId = null; resultPage = 0; stagePage = 0;
    renderedWorkflow = null; focusAction = null; live.textContent = '';
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
      if (submitted && evidence?.reviewed && step?.status === 'pending' && submitted.digest !== state.intake.workflow.digest && JSON.stringify(cropBox(evidence.crop)) === JSON.stringify(submitted.roi)) {
        cropDrafts.delete(r.id); cropPending.delete(r.id);
        cropSavedRow = mode === 'review' ? r.id : null;
        live.textContent = '裁剪范围已保存，可继续生成原值裁剪。';
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
    const step = state.intake?.workflow?.steps.find(s=>s.stage==='crop'&&s.target_id===id);
    return !!step && ['needs_review','failed','cancelled','interrupted','done'].includes(step.status);
  }
  function stageCrop(next, before) {
    const r = row();
    if (!r || state.busy || !state.intake?.cropEnabled) return;
    if (!cropEditable(r.id)) { r.roi = before; render(); return; }
    let draft = cropDrafts.get(r.id);
    if (!draft) {
      draft = {roi:before, original:before, digest:state.intake.workflow.digest, history:[before], index:0, conflict:false};
      cropDrafts.set(r.id, draft);
    }
    draft.history = draft.history.slice(0,draft.index+1); draft.history.push({...next}); draft.index++;
    draft.roi = {...next}; r.roi = draft.roi; r.draft = true;
    live.textContent = '裁剪草稿已调整，确认后才保存；尚未生成原值裁剪。';
    render();
  }
  function undoCrop(redo) {
    const r = row(), draft = r && cropDrafts.get(r.id);
    if (!draft || state.busy) return;
    const index = draft.index + (redo ? 1 : -1);
    if (index < 0 || index >= draft.history.length) return;
    draft.index = index; draft.roi = draft.history[index]; r.roi = draft.roi;
    render();
  }
  function renderCropInspector(r) {
    const actionFocus = document.activeElement?.dataset.intakeCropAction;
    if (actionFocus) cropFocusAction = actionFocus;
    else if (!$('.inspector').contains(document.activeElement)) cropFocusAction = null;
    const evidence = state.intake.crops?.find(e => e.row_id === r?.id);
    const step = state.intake.workflow.steps.find(s => s.stage === 'crop' && s.target_id === r?.id);
    const draft = r && cropDrafts.get(r.id);
    const correcting = step?.status === 'done';
    const reviewable = r && cropEditable(r.id);
    $('#inspector-title').textContent = '原图裁剪复核';
    $('#review-badge').textContent = evidence?.raw_crop ? '原值已保存' : '待核对';
    $('#review-badge').className = 'status-badge '+(evidence?.raw_crop?'ok':'pending');
    $('#inspector-content').innerHTML = `<section class="inspect-section"><h3>${r?escapeText(targetName(r.id)):'请选择蛋白行'}</h3><p>${reviewable?'在原图上拖出范围，或调整建议框。':'本行用于原图回溯；已保存的原值裁剪与历史保持。'}${r?.lanes||0} 个槽位包含无信号空位，不含 Marker；本行独立定位。</p>${dataPair('固定槽位数',r?.lanes||0)}${dataPair('原值裁剪',evidence?.raw_crop?'已保存':'尚未生成')}<p class="row-reason">${escapeText(draft?.conflict?'后台输入已改变，草稿保留；放弃后重新核对。':evidence?.reason||'请先运行固定N定位，取得该行处理状态。')}</p><p>确认整行范围将按固定 N 等宽分割。无信号不等于未上样，也不作为零值。</p></section>`;
    if (correcting) $('#inspector-content').insertAdjacentHTML('beforeend','<p class="row-reason">保存修正会使本行裁剪、本 Fig 拼图与测量、当前输出过期；其他 Fig 和历史文件保留。</p>');
    $('#inspector-action').innerHTML = `<button class="button primary full" data-intake-crop-action="confirm" ${state.busy||!r?.roi||!evidence||!reviewable||draft?.conflict||correcting&&!draft?'disabled':''}>${correcting?'保存修正并重算本 Fig':'确认此范围与固定槽位'}</button><button class="button subtle full" data-intake-crop-action="run" ${state.busy||hasDraft()||!runnable()?'disabled':''}>继续处理批次</button><button class="text-button" data-intake-crop-action="discard" ${state.busy||!draft?'disabled':''}>放弃本行裁剪草稿</button><button class="text-button" data-intake-crop-action="back">返回清单与异常</button>`;
    const focus = cropSavedRow === r?.id ? 'run' : cropFocusAction;
    cropSavedRow = null;
    if (focus) {
      const target = $(`[data-intake-crop-action="${focus}"]:not(:disabled)`) || $('#inspector-title');
      if (!target.matches('button')) target.setAttribute('tabindex','-1');
      target.focus({preventScroll:true});
    }
    if (cropPending.size && state.status && live.textContent !== state.status) live.textContent = state.status;
  }
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

  const allowedModes = () => ['intake', ...(state.intake?.cropEnabled?['review']:[]), ...(state.intake?.figureEnabled?['layout','results']:[])];
  const runnable = () => (state.intake?.workflow?.pending_ready ?? state.intake?.workflow?.steps.filter(s=>s.stage==='crop'&&s.status==='pending').length ?? 0)>0;
  function requestFigure() {
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
    $('#inspector-content').innerHTML=mode==='layout'?`<section class="inspect-section"><h3>${escapeText(fig?.label||'选择已完成的 Fig')}</h3><p>图像来自已保存的完整 Fig。显示缩放与重采样不进入定量；点击图块或下方蛋白行可回到原图。</p><div class="intake-source-links">${members.map(p=>`<button class="text-button full" data-intake-crop-action="source" data-id="${escapeText(p.protein_id)}" ${state.busy?'disabled':''}>${escapeText(targetName(p.protein_id))}</button>`).join('')}</div></section><section class="inspect-section"><h3>其他已保存成图</h3><div class="intake-source-links">${(state.intake.figuresReady||[]).map(f=>`<button class="text-button full" data-intake-crop-action="figure" data-id="${escapeText(f.figure_id)}" ${state.busy?'disabled':''}>${escapeText(state.intake.figures.find(x=>x.figure_id===f.figure_id)?.label||f.figure_id)}</button>`).join('')||'<p>完整 Fig 原值裁剪完成后，继续处理即可成图。</p>'}</div></section>`:`<section class="inspect-section"><h3>结果与原图一一对应</h3><p>按 Fig、蛋白行身份和固定槽位显示。点击蛋白行返回原图；同名蛋白仍是独立行。</p><p>有效信号与待复核的原始积分分列。未检测、失败或未计算保留为空，不写为 0。</p><p>成图与运行完成不表示科学准确率已经验收。</p></section>`;
    $('#inspector-action').innerHTML=`${mode==='layout'?'<button class="button primary full" data-intake-crop-action="results">查看测量记录</button>':''}<button class="button subtle full" data-intake-crop-action="back">返回阶段与异常</button>`;
    $('#inspector-content').insertAdjacentHTML('beforeend',outputInfo());
    return true;
  }
  function outputInfo() {
    if(!state.intake?.outputEnabled)return '';
    const output=state.intake.output, latest=(state.intake.outputs||[]).find(item=>item.destination===output?.path);
    const status=output?.path?(output.committed?(output.current===false?'历史快照已保留；当前输入已变化，需要重新输出':latest?.complete?'完整快照已登记':'部分快照已登记，未完成项仍需处理'):(state.busy?'目录已发布，正在登记项目':'目录已发布，项目尚未登记；已生成文件保留')):'完整批次完成后自动输出；也可先保存含未完成项的快照。';
    return `<section class="inspect-section intake-output-info"><h3>结果快照</h3><p role="status">${escapeText(status)}</p>${output?.path?`<p class="intake-output-path">${escapeText(output.path)}</p>`:''}<p>每次使用新目录。CSV / Excel、原值与显示裁剪、Fig、状态和恢复归档分别保留；缺项见状态报告。</p>${latest?.errors?.length?`<details><summary>${latest.errors.length} 项缺口</summary><ul>${latest.errors.map(error=>`<li>${escapeText(error)}</li>`).join('')}</ul></details>`:''}<button class="button subtle full" data-intake-crop-action="export" ${state.busy||hasDraft()||!bridge?'disabled':''}>${output?.path?'重新导出到新目录':'保存当前结果快照'}</button></section>`;
  }
  function renderIntakeResults() {
    const pageSize=200, pages=Math.max(1,Math.ceil(state.cells.length/pageSize));
    resultPage=Math.max(0,Math.min(resultPage,pages-1));
    const start=resultPage*pageSize;
    const labels={valid:'有效',quality_review:'质量待复核',not_detected:'未检测到',invalid:'无效',excluded:'已排除',not_run:'待计算',unconfigured:'待配置',pending_review:'待复核',failed:'失败',cancelled:'已取消',interrupted:'未完整提交',result_unavailable:'结果不可用',missing_source:'缺少原图',stale:'输入已变化'};
    $('.result-intro h3').textContent='原像素测量记录';
    $('.result-intro p').textContent='完整 Fig 保存后计算 · 缺失和失败留空 · 原始积分不等于有效信号';
    $('.results-scroll thead').innerHTML='<tr><th>Fig / 蛋白行</th><th>固定槽位</th><th>有效信号</th><th>原始积分</th><th>状态</th></tr>';
    $('#results-body').innerHTML=state.cells.slice(start,start+pageSize).map(c=>`<tr><td><button class="text-button full" data-intake-crop-action="source" data-id="${escapeText(c.rowId)}" ${state.busy?'disabled':''}>${escapeText(targetName(c.rowId))}</button></td><td>${c.lane}</td><td>${number(c.value)}</td><td>${number(c.rawIntegral)}</td><td><span class="result-state">${escapeText(labels[c.status]||'待处理')}</span>${c.reason?`<small>${escapeText(c.reason)}</small>`:''}</td></tr>`).join('')||'<tr><td colspan="5">尚无测量记录；请先复核原图，再继续处理完整 Fig。</td></tr>';
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
      const frozen = workflow.steps.some(step => step.attempt > 0);
      const pageSize=50, pages=Math.max(1,Math.ceil(workflow.steps.length/pageSize));
      stagePage=Math.max(0,Math.min(stagePage,pages-1));
      const start=stagePage*pageSize;
      const navigation=pages>1?`<nav class="intake-stage-actions" aria-label="阶段列表分页"><button class="text-button" data-intake="previous-stages" ${stagePage===0?'disabled':''}>上一页阶段</button><span role="status">第 ${stagePage+1} / ${pages} 页 · ${start+1}–${Math.min(start+pageSize,workflow.steps.length)} / ${workflow.steps.length} 个阶段</span><button class="text-button" data-intake="next-stages" ${stagePage===pages-1?'disabled':''}>下一页阶段</button></nav>`:'';

      return `<section class="intake-summary"><div><h2>执行计划已准备</h2><p>${state.intake.figures.length} 个 Fig · ${total} 个蛋白行 · ${state.intake.proteins.reduce((sum, row) => sum + (state.intake.figures.find(fig => fig.figure_id === row.figure_id)?.lane_count || 0), 0)} 个独立槽位。</p><p>按原值裁剪、完整 Fig 拼图、原像素定量、结果输出的顺序处理。${state.intake.figureEnabled?'完整 Fig 保存后才计算原像素；数值和质量结论分别保留。':'先核对原图定位，再保存原值裁剪；尚未生成定量结果。'}</p></div><div class="intake-stage-actions"><button class="button primary" data-intake="run" ${disabled} ${hasDraft()||!runnable()?'disabled':''}>${state.intake.figureEnabled?'继续处理':'定位与裁剪'}</button><button class="button subtle" data-intake="edit" ${disabled} ${frozen ? 'disabled' : ''}>返回清单修改</button></div></section>${outputInfo()}<section class="intake-workflow" aria-label="执行阶段"><h2 id="intake-stages-heading" tabindex="-1">阶段与异常</h2><p class="intake-help">已记录 ${workflow.ready_count} / ${workflow.steps.length} 个阶段。${issues.length ? `${issues.length} 项需要处理，其他完整 Fig 可以继续。` : '暂无异常。裁剪完成不代表科学复核通过。'}</p>${navigation}<ol start="${start+1}">${workflow.steps.slice(start, start+pageSize).map(step => `<li><span>${escapeText(names[step.stage] || step.stage)}</span><strong>${escapeText(step.stage === 'crop' ? targetName(step.target_id) : state.intake.figures.find(fig => fig.figure_id === step.target_id)?.label || state.projectName)}</strong><span>${escapeText(statuses[step.status] || step.status)}</span>${cropActions(step)}${step.reason ? `<p>${escapeText(step.reason)}</p>` : ''}</li>`).join('')}</ol>${issues.length ? `<details><summary>查看全部异常原因</summary><ul>${issues.map(step => `<li>${escapeText(names[step.stage] || step.stage)} · ${escapeText(step.target_id)}：${escapeText(step.reason)}${cropActions(step)}</li>`).join('')}</ul></details>` : ''}</section>`;
    }
    if (state.intake.confirmed) return `<section class="intake-summary"><div><h2>清单与对应关系已确认</h2><p>${count} 个蛋白行已明确分配原图。准备执行计划，预建布局位置和待计算表格，原文件保持不变。</p></div><button class="button primary" data-intake="prepare" ${disabled}>准备执行计划</button></section>`;
    return `<section class="intake-summary"><div><h2>${state.intake.confirmed ? '清单与对应关系已确认' : '确认本次导入'}</h2><p>${count} / ${total} 个蛋白行已有原图。${state.intake.confirmed ? '当前完成导入分配阶段，后续裁剪流程尚未执行。' : '核对所有蛋白行的来源后确认；未使用的原图可留在图池。'}</p></div><button class="button primary" data-intake="confirm" ${disabled}>${icon('check')}确认清单与对应关系</button></section>`;
  }
  function controls() {
    if (!draft || root.hidden) return;
    const locked = !!state.busy || !bridge || conflict || !!state.intake.workflow;
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
    const active = mode === 'intake' && !!state.intake;
    root.hidden = !active;
    document.body.classList.toggle('intake-active', active);
    document.body.classList.toggle('grouped-intake-active', active && !!state.intake?.grouped_draft && !state.intake.workflow);
    $$('.mode-tab').forEach(item => item.hidden = state.intake ? !allowedModes().includes(item.dataset.mode) : item.dataset.mode === 'intake');
    document.body.classList.toggle('intake-crop-active', !!state.intake?.cropEnabled && mode === 'review');
    if (!active) return false;
    if (!state.intake.workflow && state.intake.grouped_draft) return window.intakeGroups.render(root);
    const focused = root.contains(document.activeElement) ? document.activeElement : null;
    const action = focused?.dataset.intake;
    const stageHeadingFocus = focused?.id === 'intake-stages-heading';
    const workflow = !!state.intake.workflow;
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
    if (state.intake?.grouped_draft && !state.intake.workflow) return;
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
    if (state.intake?.grouped_draft && !state.intake.workflow) return;
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
    else if (action === 'run') { if(!hasDraft())send('intake_run', cropGuard()); }
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
      cropPending.set(r.id,{roi:{...r.roi},digest:state.intake.workflow.digest});
      const completed=state.intake.workflow.steps.some(s=>s.stage==='crop'&&s.target_id===r.id&&s.status==='done');
      if (completed && !cropDrafts.has(r.id)) return;
      send(completed?'intake_crop_revise':'intake_crop_review',{...cropGuard(),rowId:r.id,roi:{...r.roi}});
    } else if (action === 'run' && !hasDraft()) send('intake_run',cropGuard());
    else if (action === 'discard') {
      const draft = cropDrafts.get(r.id); r.roi = draft?.original || null; r.draft = false;
      cropDrafts.delete(r.id); cropPending.delete(r.id); syncCrops(); render();
    }
  });
  return {sync, renderActive, hasDraft, reset, stageCrop, undoCrop, renderCropInspector, cropEditable, allowedModes, requestFigure, renderFigureInspector, renderIntakeResults};
})();
