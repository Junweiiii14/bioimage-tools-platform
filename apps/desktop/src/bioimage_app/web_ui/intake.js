'use strict';

// This page edits identity and assignment drafts only. It never derives pixels or results.
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
  const copyPlan = intake => ({
    figures: intake.figures.map(item => ({...item})),
    proteins: intake.proteins.map(item => ({...item}))
  });
  const planText = value => JSON.stringify(copyPlan(value));
  const planDirty = () => !!draft && planText(draft) !== basePlan;
  const hasDraft = () => planDirty() || batch.length > 0;
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
      return;
    }
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
    if (intake.digest !== baseDigest) {
      if (hasDraft()) conflict = true;
      else { draft = copyPlan(intake); basePlan = planText(intake); baseDigest = intake.digest; conflict = false; }
    }
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
      return `<section class="intake-summary"><div><h2>执行计划已准备</h2><p>${state.intake.figures.length} 个 Fig · ${total} 个蛋白行 · ${state.intake.proteins.reduce((sum, row) => sum + (state.intake.figures.find(fig => fig.figure_id === row.figure_id)?.lane_count || 0), 0)} 个独立槽位。</p><p>按原值裁剪、完整 Fig 拼图、原像素定量、结果输出的顺序处理。当前尚未接入裁剪执行器，没有生成定量结果。</p></div><button class="button subtle" data-intake="edit" ${disabled} ${frozen ? 'disabled' : ''}>返回清单修改</button></section><section class="intake-workflow" aria-label="执行阶段"><h2>阶段与异常</h2><p class="intake-help">已记录 ${workflow.ready_count} / ${workflow.steps.length} 个阶段。${issues.length ? `${issues.length} 项需要处理，其他完整 Fig 可以继续。` : '暂无异常。裁剪完成不代表科学复核通过。'}</p><ol>${workflow.steps.slice(0, 50).map(step => `<li><span>${escapeText(names[step.stage] || step.stage)}</span><strong>${escapeText(step.stage === 'crop' ? targetName(step.target_id) : state.intake.figures.find(fig => fig.figure_id === step.target_id)?.label || state.projectName)}</strong><span>${escapeText(statuses[step.status] || step.status)}</span>${step.reason ? `<p>${escapeText(step.reason)}</p>` : ''}</li>`).join('')}</ol>${workflow.steps.length > 50 ? `<p class="intake-help">显示前 50 项，全部 ${workflow.steps.length} 项随项目保存。</p>` : ''}${issues.length ? `<details><summary>查看全部异常原因</summary><ul>${issues.map(step => `<li>${escapeText(names[step.stage] || step.stage)} · ${escapeText(step.target_id)}：${escapeText(step.reason)}</li>`).join('')}</ul></details>` : ''}</section>`;
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
    $$('.mode-tab').forEach(item => item.hidden = item.dataset.mode === 'intake' ? !state.intake : !!state.intake);
    if (!active) return false;
    const focused = root.contains(document.activeElement) ? document.activeElement : null;
    const action = focused?.dataset.intake;
    const workflow = !!state.intake.workflow;
    const transitioned = renderedWorkflow !== null && workflow !== renderedWorkflow;
    renderedWorkflow = workflow;
    const field = focused?.dataset.intakeField, id = focused?.dataset.id;
    const searchFocus = focused?.hasAttribute('data-intake-search');
    const caret = focused?.type === 'text' || focused?.type === 'search' ? [focused.selectionStart, focused.selectionEnd] : null;
    const scroll = root.scrollTop;
    const disabled = state.busy || !bridge || conflict ? 'disabled' : '';
    const editingDisabled = disabled || state.intake.workflow ? 'disabled' : '';
    root.innerHTML = `<div class="intake-heading"><div><h1>仪器导入与分配</h1><p>先保存 Fig 清单，再将原图分配到蛋白行。原始文件保持原名。</p></div><span class="status-badge ${state.intake.confirmed ? 'ok' : 'pending'}">${state.intake.confirmed ? '已确认' : '待确认'}</span></div>${conflict ? '<div class="intake-conflict" role="alert">项目清单已在后台变化。本地草稿已保留，请核对后使用“放弃草稿并重新载入”获取最新清单。</div>' : ''}<div class="intake-columns">${renderPlan(batch.length ? 'disabled' : editingDisabled)}<div class="intake-allocation">${renderSources(editingDisabled)}${renderBatch(editingDisabled)}</div></div>${renderSummary(disabled)}`;
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
    const replacement = searchFocus ? $('[data-intake-search]', root) : field ? $$('[data-intake-field]', root).find(item => item.dataset.intakeField === field && item.dataset.id === id) : button;
    if (replacement) { replacement.focus({preventScroll: true}); if (caret) replacement.setSelectionRange(...caret); }
    else if (focused || focusAction) summary?.focus({preventScroll: true});
    if (focusAction && state.status && live.textContent !== state.status) live.textContent = state.status;
    return true;
  }

  root.addEventListener('input', event => {
    const field = event.target.dataset.intakeField, id = event.target.dataset.id;
    if (field === 'fig-label') draft.figures.find(item => item.figure_id === id).label = event.target.value;
    if (field === 'lanes') draft.figures.find(item => item.figure_id === id).lane_count = event.target.value === '' ? null : Number(event.target.value);
    if (field === 'protein') draft.proteins.find(item => item.protein_id === id).label = event.target.value;
    if (event.target.hasAttribute('data-intake-search')) { filter = event.target.value; renderActive(); }
    controls();
  });
  root.addEventListener('change', event => {
    const item = event.target;
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
    } else if (action === 'reload') { draft = copyPlan(state.intake); basePlan = planText(state.intake); baseDigest = state.intake.digest; batch = []; selected.clear(); conflict = false; pending = null; }
    else if (action === 'stage') { for (const source_id of selected) if (!batch.some(binding => binding.source_id === source_id)) batch.push({source_id, protein_id: ''}); selected.clear(); }
    else if (action === 'duplicate') batch.splice(Number(item.dataset.index) + 1, 0, {source_id: batch[Number(item.dataset.index)].source_id, protein_id: ''});
    else if (action === 'remove-binding') batch.splice(Number(item.dataset.index), 1);
    else if (action === 'save-plan') { pending = {kind: 'plan', value: planText(draft)}; send('intake_plan', {...guard(), ...copyPlan(draft)}); }
    else if (action === 'assign') { pending = {kind: 'assign', value: batch.map(binding => ({...binding}))}; send('intake_assign', {...guard(), bindings: batch, replace, allowReuse}); }
    else if (action === 'confirm') send('intake_confirm', guard());
    else if (action === 'prepare') send('intake_prepare', guard());
    else if (action === 'edit') send('intake_edit', guard());
    else if (action === 'import') { if (hasDraft()) { toast('请先保存清单、提交对应关系，或放弃草稿，再添加文件夹。'); return; } send('intake_import_folder', guard()); }
    renderActive();
    if (focusAddFigure) $('[data-intake=add-fig]', root)?.focus();
    if (focusFigure) $$('[data-intake=add-protein]', root).find(button => button.dataset.id === focusFigure)?.focus();
  });
  return {sync, renderActive, hasDraft, reset};
})();
