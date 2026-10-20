'use strict';

// Editable acquisition choices are persisted through the same guarded project save.
window.intakeGroups = (() => {
  let identity = '', digest = '', base = '', draft = null, pending = null;
  let conflict = false, filter = '', bulkFigure = '', reuse = false, zoomSource = null;
  const selected = new Set();
  const clone = value => JSON.parse(JSON.stringify(value));
  const text = value => JSON.stringify(value);
  const dirty = () => !!draft && text(draft) !== base;
  const normalizedSave = () => {
    const value = clone(draft), counts = new Map();
    const committed = new Map(JSON.parse(base).groups.map(g=>[g.group_id,g]));
    const sha = id => source(id)?.asset?.sha256 || id;
    value.groups.forEach(g => {if(g.selected_source_id){const key=sha(g.selected_source_id);counts.set(key,(counts.get(key)||0)+1);}});
    value.groups.forEach(g => {const old=committed.get(g.group_id);g.reuse_confirmed=!!(g.selected_source_id && counts.get(sha(g.selected_source_id))>1 && (reuse || (old?.selected_source_id===g.selected_source_id && old?.reuse_confirmed)));});
    return value;
  };
  const source = id => state.intake.sources.find(item => item.source_id === id);
  const figure = id => draft?.figures.find(item => item.figure_id === id);
  const group = id => draft?.groups.find(item => item.group_id === id);
  const observation = id => state.intake.discovery?.observations.find(item=>item.source_id===id);
  const region = g => g?.region_index == null ? null : observation(g.selected_source_id)?.regions[g.region_index];
  function preview(s, target) {
    if (!s.preview) return '<span>预览加载中</span>';
    if (!target) return `<img src="${s.preview}" alt="${escapeText(s.original_name)} 的显示预览">`;
    return `<svg class="grouped-source-preview" viewBox="0 0 ${s.width} ${s.height}" role="img" aria-label="${escapeText(s.original_name)} 与所选目标区域"><image href="${s.preview}" width="${s.width}" height="${s.height}"/><rect x="${target.x0}" y="${target.y0}" width="${target.x1-target.x0}" height="${target.y1-target.y0}" fill="none" stroke="var(--accent)" stroke-width="2" vector-effect="non-scaling-stroke"/></svg>`;
  }
  function regionControl(g, disabled) {
    if (!g.selected_source_id) return '';
    const regions=observation(g.selected_source_id)?.regions || [];
    if (!regions.length) return '<p class="intake-help">尚无目标区域候选；可先识别来源，或在裁剪阶段手动画范围。</p>';
    const saved=JSON.parse(base).groups.find(item=>item.group_id===g.group_id);
    const savedFigure=JSON.parse(base).figures.find(f=>f.figure_id===saved?.figure_id);
    const changed=saved?.selected_source_id!==g.selected_source_id || savedFigure?.lane_count!==figure(g.figure_id)?.lane_count;
    return `<label class="grouped-region">目标区域（未审核）<select data-group-field="region" data-id="${escapeText(g.group_id)}" ${disabled} ${changed?'disabled':''}><option value="">不选候选，使用原图定位或手动复核</option>${regions.map((r,i)=>`<option value="${i}" ${g.region_index===i?'selected':''}>区域 ${i+1} · 原图 (${r.x0}, ${r.y0})–(${r.x1}, ${r.y1})</option>`).join('')}</select><small>${changed?'原图或 N 有修改；先保存，再选择当前区域。':'仅传递原图坐标建议；裁剪阶段仍须核对 Marker 和全部槽位。'}</small></label>`;
  }
  const groupName = item => `采集组 ${String(draft.groups.indexOf(item)+1).padStart(2,'0')}`;
  const groupDirectory = item => {
    const path = source(item.source_ids[0])?.relative_path || '';
    return path.includes('/') ? path.slice(0,path.lastIndexOf('/')) : '当前导入目录';
  };
  const guard = () => ({projectId:state.projectId, sessionEpoch:state.sessionEpoch, digest});
  const locked = () => state.busy || !bridge || conflict || (!!state.intake?.workflow && !state.intake.workflow.editing);
  function reset() {
    identity = ''; digest = ''; base = ''; draft = null; pending = null;
    conflict = false; filter = ''; bulkFigure = ''; reuse = false; selected.clear();
    zoomSource = null;
    const dialog = document.querySelector('#grouped-image-dialog');
    if (dialog?.open) dialog.close();
  }
  function sync() {
    const next = state.intake?.grouped_draft;
    if (!next) { reset(); return; }
    const key = `${state.sessionEpoch}:${state.projectId}`;
    if (identity !== key) {
      reset(); identity = key; draft = clone(next); base = text(next); digest = state.intake.digest;
      return;
    }
    if (pending && text(next) === pending.expected) {
      if (text(draft) === pending.draft) draft = clone(next);
      base = text(next); digest = state.intake.digest; pending = null; conflict = false;
    }
    if (state.intake.digest !== digest) {
      if (dirty()) conflict = true;
      else { draft = clone(next); base = text(next); digest = state.intake.digest; conflict = false; }
    }
    const dialog = document.querySelector('#grouped-image-dialog'), zoom = state.intake.zoom;
    if (dialog?.open && zoom?.sourceId === zoomSource && zoom.preview) {
      const img=dialog.querySelector('img'), svgImage=dialog.querySelector('image');
      if(img)img.src=zoom.preview;
      if(svgImage)svgImage.setAttribute('href',zoom.preview);
      dialog.querySelector('p').textContent = '原图显示预览；裁剪复核阶段使用原图坐标。';
    }
  }
  const visible = () => draft.groups.filter(item => !filter || item.source_ids.some(id => {
    const s = source(id); return s?.relative_path.toLowerCase().includes(filter.toLowerCase());
  }) || item.protein_label.toLowerCase().includes(filter.toLowerCase()));
  function readiness() {
    if (!draft?.groups.some(item => item.figure_id !== null)) return '请选择采集组并归入 Fig。';
    for (const item of draft.groups) {
      if (item.figure_id === null) {
        if (item.selected_source_id !== null) return '已选裁剪原图仍未归入 Fig。';
        continue;
      }
      const f = figure(item.figure_id);
      if (!f?.label.trim() || !Number.isInteger(f.lane_count) || f.lane_count < 1 || f.lane_count > 96)
        return '请填写 Fig 名称与 1–96 的样本槽位数 N。';
      if (!item.protein_label.trim() || !item.selected_source_id) return '请补齐已归 Fig 的蛋白名称与裁剪原图。';
    }
    return '';
  }
  function suggestions(f) {
    const records = state.intake.discovery?.observations || [];
    return draft.groups.filter(g => g.figure_id === f.figure_id && g.selected_source_id).map(g => {
      const observation = records.find(r => r.source_id === g.selected_source_id);
      const counts = [...new Set((observation?.regions || []).flatMap(r => r.lane_counts))];
      return counts.length ? `${g.protein_label || '未命名组'}：${counts.join(' / ')}` : '';
    }).filter(Boolean);
  }
  function controls(root) {
    const save = root.querySelector('[data-group-action="save"]');
    if (!save) return;
    save.disabled = locked() || !dirty();
    root.querySelector('[data-group-action="confirm"]').disabled = locked() || dirty() || !!readiness() || state.intake.confirmed;
    const prepare = root.querySelector('[data-group-action="prepare"]');
    if (prepare) prepare.disabled = locked() || dirty();
    root.querySelector('[data-group-status]').textContent = conflict ? '后台输入已变化；本地草稿保留，请重新载入后核对。' : dirty() ? '草稿有修改，保存后可关闭并继续。' : state.intake.confirmed ? '清单已确认，可以准备执行计划。' : readiness() || '来源与固定 N 已填齐，核对后确认清单。';
  }
  function render(root) {
    if (!draft) return false;
    const focused = root.contains(document.activeElement) ? document.activeElement : null;
    const field = focused?.dataset.groupField, id = focused?.dataset.id;
    const action = focused?.dataset.groupAction, searchFocus = focused?.hasAttribute('data-group-search');
    const caret = ['text','search'].includes(focused?.type) ? [focused.selectionStart, focused.selectionEnd] : null;
    const scroll = root.scrollTop, disabled = locked() ? 'disabled' : '';
    const options = current => `<option value="">待归 Fig</option>${draft.figures.map(f => `<option value="${escapeText(f.figure_id)}" ${current===f.figure_id?'selected':''}>${escapeText(f.label || '未命名 Fig')}</option>`).join('')}`;
    root.innerHTML = `<div class="intake-heading"><div><h1>采集组与 Fig</h1><p>先将采集组归入 Fig，再填写蛋白名并选择裁剪原图。N 包含空槽，不含 Marker。</p></div><button class="button subtle" data-group-action="import" ${disabled} ${dirty()||state.intake.workflow?'disabled':''}>添加图片文件夹</button></div>
      ${state.intake.workflow?.editing?'<p class="intake-help">正在修改执行后的分组。保存会使受影响裁剪、Fig 与输出过期；确认清单后再继续处理，历史修订和文件保留。</p>':''}
      ${conflict?'<p class="intake-conflict" role="alert">后台清单已改变。本地草稿保留，请核对后重新载入。</p>':''}
      ${state.intake.issues?.length?`<details class="intake-conflict" aria-label="导入失败文件"><summary>${state.intake.issues.length} 个文件读取失败；成功读取的原图仍可继续</summary><ul>${state.intake.issues.map(issue=>`<li>${escapeText(issue)}</li>`).join('')}</ul></details>`:''}
      <section class="grouped-figures" aria-label="Fig 与固定样本槽位"><div class="intake-section-heading"><h2>Fig 与 N</h2><button class="text-button" data-group-action="add-fig" ${disabled}>添加 Fig</button></div><div class="grouped-fig-grid">${draft.figures.map(f => `<fieldset class="grouped-fig"><legend>${escapeText(f.label || '未命名 Fig')}</legend><label>Fig 名称<input type="text" maxlength="120" data-group-field="fig-label" data-id="${escapeText(f.figure_id)}" value="${escapeText(f.label)}" ${disabled}></label><label>样本槽位 N<input type="number" min="1" max="96" step="1" placeholder="待推断或填写" data-group-field="lanes" data-id="${escapeText(f.figure_id)}" value="${f.lane_count ?? ''}" ${disabled}></label><p>${suggestions(f).length?`算法候选（未确认）：${escapeText(suggestions(f).join('；'))}`:'同 Fig 只共享数量；每行独立定位。'}</p></fieldset>`).join('') || '<p class="intake-empty">添加 Fig 后，可一次归入多个采集组。N 未知时可以先保存草稿。</p>'}</div></section>
      <div class="grouped-toolbar"><label class="grouped-search">查找采集组<input type="search" data-group-search value="${escapeText(filter)}" placeholder="文件名、目录或蛋白名"></label><button class="button subtle" data-group-action="select-visible" ${disabled}>选择当前显示组</button><button class="text-button" data-group-action="clear-selection" ${disabled}>取消选组</button><label>将 ${selected.size} 组归入<select data-group-field="bulk-fig" ${disabled}>${options(bulkFigure)}</select></label><button class="button primary" data-group-action="assign" ${disabled} ${!selected.size?'disabled':''}>批量归 Fig</button><button class="text-button" data-group-action="discover" ${disabled} ${dirty()||state.intake.workflow||!state.intake.sources.length?'disabled':''}>识别来源与 N 建议</button></div>
      <p class="intake-help">${draft.groups.length} 个采集组 · ${state.intake.sources.length} 张图。组内图片并列，辅助图跟随本组标注；只有所选原图进入裁剪。</p>
      <div class="grouped-grid">${visible().map(g => `<section class="grouped-card" data-group-id="${escapeText(g.group_id)}"><div class="grouped-card-title"><h3>${escapeText(groupName(g))}</h3><p>${escapeText(groupDirectory(g))}</p></div><div class="grouped-card-heading"><label><input type="checkbox" aria-label="选择${escapeText(groupName(g))} · ${escapeText(groupDirectory(g))}" data-group-select="${escapeText(g.group_id)}" ${selected.has(g.group_id)?'checked':''} ${disabled}>选择此组</label><label>所属 Fig<select data-group-field="figure" data-id="${escapeText(g.group_id)}" ${disabled}>${options(g.figure_id)}</select></label></div><label class="grouped-protein">蛋白名称<input type="text" maxlength="120" data-group-field="protein" data-id="${escapeText(g.group_id)}" value="${escapeText(g.protein_label)}" placeholder="由实验人员填写" ${disabled}></label><div class="grouped-images">${g.source_ids.map(id => {
        const s = source(id); if (!s) return '';
        return `<div class="grouped-image ${g.selected_source_id===id?'chosen':''}"><button class="grouped-zoom" data-group-action="zoom" data-id="${escapeText(id)}" aria-label="放大 ${escapeText(s.original_name)}">${preview(s,g.selected_source_id===id?region(g):null)}</button><label><input type="radio" name="group-${escapeText(g.group_id)}" data-group-source="${escapeText(id)}" data-id="${escapeText(g.group_id)}" ${g.selected_source_id===id?'checked':''} ${disabled}>用于裁剪</label><strong>${escapeText(s.original_name)}</strong><small>${escapeText(s.relative_path)}</small><small>${s.width} × ${s.height} · ${s.bit_depth} 位</small></div>`;
      }).join('')}</div>${regionControl(g,disabled)}<div class="grouped-card-footer"><span>${escapeText(figure(g.figure_id)?.label || '待归 Fig')} · ${escapeText(g.protein_label || '蛋白待命名')}${g.selected_source_id?' · 已选裁剪源':' · 未选裁剪源'}</span><button class="text-button" data-group-action="unpick" data-id="${escapeText(g.group_id)}" ${disabled} ${!g.selected_source_id?'disabled':''}>取消裁剪源</button></div></section>`).join('') || '<p class="intake-empty">没有匹配的采集组；清除筛选可查看全部。</p>'}</div>
      <footer class="grouped-save"><p data-group-status role="status"></p><label><input type="checkbox" data-group-reuse ${reuse?'checked':''} ${disabled}>明确允许相同原图内容用于多个蛋白</label><div><button class="text-button" data-group-action="reload" ${state.busy?'disabled':''}>放弃修改并重新载入</button><button class="button subtle" data-group-action="save">保存分组草稿</button><button class="button primary" data-group-action="confirm">确认清单与对应关系</button>${state.intake.confirmed&&!state.intake.workflow?'<button class="button primary" data-group-action="prepare">准备执行计划</button>':''}</div></footer>`;
    controls(root); root.scrollTop = scroll;
    const replacement = searchFocus ? root.querySelector('[data-group-search]') : field ? [...root.querySelectorAll('[data-group-field]')].find(e => e.dataset.groupField===field && e.dataset.id===id) : action ? [...root.querySelectorAll('[data-group-action]')].find(e => e.dataset.groupAction===action && e.dataset.id===id && !e.disabled) : null;
    if (replacement) { replacement.focus({preventScroll:true}); if (caret) replacement.setSelectionRange(...caret); }
    return true;
  }
  function bind(root) {
    root.addEventListener('input', event => {
      const el = event.target;
      if (el.hasAttribute('data-group-search')) { filter = el.value; render(root); return; }
      if (locked()) return;
      const f = figure(el.dataset.id), g = group(el.dataset.id);
      if (el.dataset.groupField==='fig-label' && f) f.label = el.value;
      if (el.dataset.groupField==='lanes' && f) {
        f.lane_count = el.value === '' ? null : Number(el.value);
        draft.groups.filter(item => item.figure_id===f.figure_id).forEach(item => item.region_index=null);
      }
      if (el.dataset.groupField==='protein' && g) g.protein_label = el.value;
      controls(root);
    });
    root.addEventListener('change', event => {
      if (locked()) return;
      const el = event.target, g = group(el.dataset.id);
      if (el.dataset.groupSelect) { if(el.checked)selected.add(el.dataset.groupSelect);else selected.delete(el.dataset.groupSelect); }
      if (el.dataset.groupField==='bulk-fig') bulkFigure = el.value;
      if (el.dataset.groupField==='figure' && g) { g.figure_id = el.value || null; g.region_index=null; }
      if (el.dataset.groupField==='region' && g && !el.disabled) g.region_index=el.value===''?null:Number(el.value);
      if (el.dataset.groupSource && g) { g.selected_source_id=el.dataset.groupSource; g.region_index=null; g.reuse_confirmed=false; }
      if (el.hasAttribute('data-group-reuse')) reuse=el.checked;
      render(root);
    });
    root.addEventListener('click', event => {
      const button = event.target.closest('[data-group-action]');
      if (!button || button.disabled || !draft) return;
      const action = button.dataset.groupAction;
      if (action==='zoom') {
        const s = source(button.dataset.id); if (!s?.preview) return;
        let dialog = document.querySelector('#grouped-image-dialog');
        if (!dialog) { dialog=document.createElement('dialog');dialog.id='grouped-image-dialog';document.body.append(dialog); }
        const owner=draft.groups.find(g=>g.selected_source_id===s.source_id);
        dialog.innerHTML=`<form method="dialog"><button class="button subtle">关闭预览</button></form><h2>${escapeText(s.original_name)}</h2>${preview(s,region(owner))}<p>显示预览；目标框采用原图坐标，裁剪阶段仍须复核。</p>`;
        zoomSource = s.source_id;
        if (!dialog.open) dialog.showModal();
        if (!locked()) send('intake_preview',{...guard(),sourceId:s.source_id});
        return;
      }
      if (action==='reload' && !state.busy) { draft=clone(state.intake.grouped_draft);base=text(draft);digest=state.intake.digest;pending=null;conflict=false;selected.clear();reuse=false;render(root);return; }
      if (locked()) return;
      if (action==='add-fig') { const id=crypto.randomUUID();draft.figures.push({figure_id:id,label:`Fig ${draft.figures.length+1}`,lane_count:null});bulkFigure=id; }
      if (action==='select-visible') visible().forEach(item => selected.add(item.group_id));
      if (action==='clear-selection') selected.clear();
      if (action==='assign') { draft.groups.filter(item=>selected.has(item.group_id)).forEach(item=>{item.figure_id=bulkFigure||null;item.region_index=null;});selected.clear(); }
      if (action==='unpick') { const g=group(button.dataset.id);g.selected_source_id=null;g.region_index=null;g.reuse_confirmed=false; }
      if (action==='save' && dirty()) { pending={draft:text(draft),expected:text(normalizedSave())};send('intake_grouping',{...guard(),grouping:clone(draft),allowReuse:reuse}); }
      if (action==='confirm' && !dirty() && !readiness()) send('intake_confirm',guard());
      if (action==='prepare' && !dirty() && state.intake.confirmed) send('intake_prepare',guard());
      if (action==='discover' && !dirty()) send('intake_discover',guard());
      if (action==='import' && !dirty()) send('intake_import_folder',guard());
      render(root);
    });
  }
  return {sync,reset,render,bind,hasDraft:dirty};
})();
