'use strict';

// Presentation only. Every measurement is sent to the existing original-pixel worker.
const manualQuant = {
  active: false,
  pendingImport: false,
  draft: null,
  drawing: null,
  submittedRevision: null,
  profileView: 'all',
  profileBinding: null,
  profileKey: null,

  current() {
    const source = row(), quant = quantData();
    if (!source) return null;
    const key = [state.projectId, source.id, source.sourceId, quant?.revision].join(':');
    if (this.draft?.key !== key) {
      this.draft = {
        key, roi: source.roi ? {...source.roi} : null,
        n: source.lanes, polarity: quant?.polarity || 'dark',
        empty: (source.emptyLanes || []).join(',')
      };
    }
    return this.draft;
  },

  sync() {
    if (this.submittedRevision !== null && state.quant?.revision !== this.submittedRevision) {
      this.active = false;
      this.submittedRevision = null;
      this.draft = null;
    } else if (!state.busy) {
      this.submittedRevision = null;
    }
    if (this.drawing && this.drawing.id !== row()?.id) this.drawing = null;
    if (this.profileBinding && this.profileBinding !== [state.projectId, row()?.id, row()?.sourceId].join(':')) this.closeProfiles();
  },

  isSetup() {
    return quantDetail && (this.active || !quantData()?.lanes?.length);
  },

  render() {
    const draft = this.current(), source = row();
    const disabled = state.busy || !bridge ? 'disabled' : '';
    $('#inspector-title').textContent = '独立灰度分析';
    $('#review-badge').textContent = state.busy ? '正在计算' : '原图测量';
    $('#review-badge').className = 'status-badge';
    $('#inspector-content').innerHTML = source ? `
      <section class="inspect-section">
        <h3>测量区域</h3>
        <p>在原图拖出矩形。无需先自动裁图或生成拼图。</p>
        <button class="button subtle full" data-manual-quant-draw ${disabled}>${icon('focus')}重新选择区域</button>
        <p>${draft.roi ? `${draft.roi.width} × ${draft.roi.height} 原图像素` : '尚未选择；请在左侧原图上拖出区域。'}</p>
        <details><summary>精确坐标与键盘输入</summary>
          <button class="text-button" data-manual-quant-whole ${disabled}>使用全图作为起始区域</button>
          <div class="quant-fields">${[['x','左边 x',0],['y','上边 y',0],['width','宽度',source.width],['height','高度',source.height]].map(([key,label,fallback]) => `<label class="quant-field">${label}<input type="number" data-manual-quant-coordinate="${key}" min="0" step="1" value="${draft.roi?.[key] ?? fallback}" ${disabled}></label>`).join('')}</div>
        </details>
        <div class="quant-fields">
          <label class="quant-field">泳道数 N<input data-manual-quant-field="n" type="number" min="1" max="96" step="1" value="${draft.n}" ${disabled}></label>
          <label class="quant-field">信号极性<select data-manual-quant-field="polarity" ${disabled}><option value="dark" ${draft.polarity === 'dark' ? 'selected' : ''}>暗条带</option><option value="light" ${draft.polarity === 'light' ? 'selected' : ''}>亮条带</option></select></label>
        </div>
        <label class="quant-field">排除泳道（可留空）<input data-manual-quant-field="empty" value="${escapeText(draft.empty)}" placeholder="例如 2, 5" ${disabled}></label>
      </section>
      <section class="inspect-section"><p>点击计算即确认本次测量区域和泳道数。使用原始像素；背景直线、积分边界和质量原因可在曲线中查看与调整。</p></section>
    ` : '<section class="inspect-section"><p>添加 TIFF 原图后，在这里独立测量灰度。</p><button class="button primary" data-action="quant_import">选择原图</button></section>';
    $('#inspector-action').innerHTML = `<button class="button primary full" data-manual-quant-run ${disabled || !draft?.roi ? 'disabled' : ''}>${icon('curve')}计算当前原图</button><button class="text-button" data-action="quant_import">添加测量原图</button>`;
    $('#quant-profile').hidden = false;
    $('#quant-profile').innerHTML = '<div class="quant-empty"><h3>从原图选择测量区域</h3><p>矩形高度与宽度可自由选择，不改变原图，也不调整拼图模板。</p></div>';
  },

  detailActions() {
    const disabled = state.busy || !bridge ? 'disabled' : '';
    $('#inspector-action').innerHTML = `
      <button class="button primary full" data-manual-quant-run ${disabled}>${icon('curve')}计算当前原图</button>
      <button class="button subtle full" data-quant-profiles ${state.busy || !(quantData()?.lanes || []).some(lane => lane.profile?.length) ? 'disabled' : ''}>全部泳道曲线</button>
      <button class="button subtle full" data-manual-quant-open ${disabled}>${icon('focus')}测量区域与泳道</button>
      <button class="text-button" data-mode="results">${icon('table')}查看灰度结果</button>
      ${state.montage ? '<button class="text-button" data-quant-overview>查看 Fig 整组</button>' : ''}
    `;
  },

  overlay(actualZoom) {
    const layer = $('#quant-lanes'), source = row(), box = this.current()?.roi;
    layer.hidden = mode !== 'quant';
    layer.innerHTML = !box || !source ? '' : `<div class="quant-target-draft" style="left:${box.x / source.width * 100}%;top:${box.y / source.height * 100}%;width:${box.width / source.width * 100}%;height:${box.height / source.height * 100}%;border-width:${1.5 / actualZoom}px"></div>`;
  },

  submit(resetBounds = false) {
    if (state.busy || !bridge) return;
    const source = row(), quant = quantData(), draft = this.current();
    if (!source || !draft?.roi) return toast('请先在原图上拖出测量区域。');
    const n = Number(draft.n);
    const emptyLanes = draft.empty.trim() ? draft.empty.split(/[,，]/).map(value => Number(value.trim())) : [];
    if (!Number.isInteger(n) || n < 1 || n > 96) return toast('泳道数须为 1–96 的整数。');
    if (emptyLanes.some(value => !Number.isInteger(value) || value < 1 || value > n) || new Set(emptyLanes).size !== emptyLanes.length) return toast('排除泳道须为不重复的 1–N 整数。');
    if (draft.roi.width < n || draft.roi.height < 2 || draft.roi.height > 4096) return toast('区域须容纳全部泳道，高度须为 2–4096 原图像素。');
    this.submittedRevision = quant?.revision;
    send('quant_target', {
      projectId: state.projectId, id: source.id, sourceId: source.sourceId,
      revision: quant?.revision, roi: draft.roi, n, polarity: draft.polarity, emptyLanes, resetBounds
    });
  },

  point(event, rect, source) {
    return {
      x: Math.max(0, Math.min(source.width, Math.round((event.clientX - rect.left) / rect.width * source.width))),
      y: Math.max(0, Math.min(source.height, Math.round((event.clientY - rect.top) / rect.height * source.height)))
    };
  },

  chart(lane, band, editable = false) {
    if (!lane?.profile?.length) return '<p>当前泳道暂无已提交曲线。</p>';
    const bands = editable ? [band] : (lane.bands || []);
    const endpoints = bands.flatMap(item => [item?.baselineStart, item?.baselineEnd]).filter(finiteQuantValue);
    const g = profileGeometry(lane, endpoints.length ? {baselineStart: Math.min(...endpoints), baselineEnd: Math.max(...endpoints)} : null);
    const curve = g.values.map((value, index) => `${index ? 'L' : 'M'}${g.x(index)},${g.y(value)}`).join(' ');
    let area = '', baseline = '', points = '';
    for (const band of bands) {
      if (!hasQuantBounds(band, g.values.length)) continue;
      const {start, end, baselineStart: a, baselineEnd: b} = band;
      const envelope = g.values.slice(start, end + 1).map((value, offset) => `${g.x(start + offset)},${g.y(Math.max(value, a + (b - a) * offset / (end - start)))}`).join(' ');
      area += `<polygon class="quant-fill" points="${g.x(start)},${g.y(a)} ${envelope} ${g.x(end)},${g.y(b)}"/>`;
      baseline += `<path class="quant-boundaries" d="M${g.x(start)},28V156 M${g.x(end)},28V156"/><path class="quant-baseline" d="M${g.x(start)},${g.y(a)}L${g.x(end)},${g.y(b)}"/>`;
      let peak = start, largest = -Infinity;
      for (let index = start; index <= end; index++) {
        const residual = g.values[index] - (a + (b - a) * (index - start) / (end - start));
        if (residual > largest) {largest = residual; peak = index;}
      }
      points += `<circle class="quant-profile-peak" cx="${g.x(peak)}" cy="${g.y(g.values[peak])}" r="3"><title>区域内最高点 y=${peak}</title></circle>`;
      if (editable) points += [['start',start,166],['end',end,166],['baselineStart',start,g.y(a)],['baselineEnd',end,g.y(b)]].map(([key,x,y]) => `<circle data-quant-point="${key}" cx="${g.x(x)}" cy="${y}" r="6" tabindex="0" role="slider" aria-label="${({start:'积分起点',end:'积分终点',baselineStart:'起点封底',baselineEnd:'终点封底'})[key]}" aria-valuenow="${band[key]}" aria-valuemin="${key.startsWith('baseline') ? g.min : 0}" aria-valuemax="${key.startsWith('baseline') ? g.max : g.values.length - 1}" class="quant-point ${key.startsWith('baseline') ? 'baseline-point' : ''}"/>`).join('');
    }
    return `<svg class="quant-chart" viewBox="0 0 680 196" preserveAspectRatio="none" aria-label="泳道 ${lane.lane} 灰度曲线"><path class="quant-axis" d="M44,28V156H656"/><text x="38" y="31" text-anchor="end">${number(g.max)}</text><text x="38" y="158" text-anchor="end">${number(g.min)}</text><text x="44" y="190">0</text><text x="656" y="190" text-anchor="end">${g.values.length - 1} y</text>${area}<path class="quant-curve" d="${curve}"/>${baseline}${points}</svg>`;
  },

  profilePanel() {
    const dialog = $('#quant-profiles-dialog');
    return dialog?.open && this.profileView === 'single' ? $('#quant-profile-single') : null;
  },

  openProfiles() {
    if (!quantData()?.lanes?.length) return toast('计算当前原图后即可查看全部泳道曲线。');
    this.profileView = 'all';
    this.profileBinding = [state.projectId, row()?.id, row()?.sourceId].join(':');
    this.profileKey = null;
    $('#quant-profiles-dialog').showModal();
    this.refreshProfiles();
  },

  closeProfiles() {
    const dialog = $('#quant-profiles-dialog');
    if (dialog?.open) dialog.close();
    this.profileBinding = null;
    this.profileKey = null;
    renderQuant();
  },

  refreshProfiles(force = false) {
    const dialog = $('#quant-profiles-dialog'), quant = quantData();
    if (!dialog?.open || !quant) return;
    const key = [quant.rowId, quant.revision, quant.status, state.busy, this.profileView, quantLane, quantBand].join(':');
    if (!force && key === this.profileKey) return;
    this.profileKey = key;
    $('#quant-profiles-title').textContent = `${row()?.name || '当前原图'} · 灰度峰与积分区域`;
    $('#quant-profile-view').value = this.profileView;
    $('#quant-profile-lane').innerHTML = (quant.lanes || []).map(lane => `<option value="${lane.lane}" ${lane.lane === quantLane ? 'selected' : ''}>泳道 ${lane.lane}</option>`).join('');
    const selected = quantSelection();
    $('#quant-profile-band-label').hidden = this.profileView !== 'single' || (selected.lane?.bands?.length || 0) < 2;
    $('#quant-profile-band').innerHTML = (selected.lane?.bands || []).map(band => `<option value="${escapeText(band.id)}" ${band.id === selected.band?.id ? 'selected' : ''}>${escapeText(band.label || band.id)}</option>`).join('');
    $('#quant-profiles-all').hidden = this.profileView !== 'all';
    $('#quant-profiles-single-wrap').hidden = this.profileView !== 'single';
    if (this.profileView === 'all') {
      $('#quant-profiles-all').innerHTML = (quant.lanes || []).map(lane => `<section class="quant-profile-row"><button class="text-button" data-profile-select="${lane.lane}">泳道 ${lane.lane} · 单泳道细调${icon('chevron')}</button>${this.chart(lane, lane.bands?.[0])}</section>`).join('');
    } else {
      const {lane, band} = quantSelection();
      $('#quant-profile-single').innerHTML = this.chart(lane, band, true);
      $('#quant-profile-fields').innerHTML = [['start','积分起点 y'],['end','积分终点 y'],['baselineStart','起点封底'],['baselineEnd','终点封底']].map(([key,label]) => `<label class="quant-field">${label}<input type="number" data-quant-field="${key}" value="${finiteQuantValue(band?.[key]) ? band[key] : ''}" step="${key.startsWith('baseline') ? '.1' : '1'}" ${state.busy || !bridge ? 'disabled' : ''}></label>`).join('');
    }
    const reasons = new Map();
    for (const lane of quant.lanes || []) for (const band of lane.bands || []) {
      if (!band.reason) continue;
      if (!reasons.has(band.reason)) reasons.set(band.reason, new Set());
      reasons.get(band.reason).add(lane.lane);
    }
    $('#quant-profiles-quality').innerHTML = reasons.size ? `<summary>质量说明（${reasons.size} 类）</summary><ul>${[...reasons].map(([reason,lanes]) => `<li>泳道 ${[...lanes].join(', ')}：${escapeText(reason)}</li>`).join('')}</ul>` : '<summary>质量说明</summary><p>未发现当前检查能识别的质量问题；这不等于已证明实验准确性。</p>';
  }
};

document.addEventListener('click', event => {
  if (!(event.target instanceof Element)) return;
  if (event.target.closest('[data-manual-quant-run]')) manualQuant.submit();
  if (event.target.closest('[data-quant-profiles]')) manualQuant.openProfiles();
  if (event.target.closest('[data-close-quant-profiles]')) manualQuant.closeProfiles();
  const profile = event.target.closest('[data-profile-select]');
  if (profile) {
    quantLane = Number(profile.dataset.profileSelect);
    quantBand = null;
    manualQuant.profileView = 'single';
    manualQuant.refreshProfiles(true);
  }
  if (event.target.closest('[data-manual-quant-reset]')) manualQuant.submit(true);
  if (event.target.closest('[data-manual-quant-whole]') && !state.busy) {
    const source = row();
    manualQuant.current().roi = {x: 0, y: 0, width: source.width, height: source.height};
    renderQuant();
  }
  if (event.target.closest('[data-manual-quant-open]') && !state.busy) {
    manualQuant.active = true;
    focusCrop = false;
    zoom = 1;
    render();
  }
  if (event.target.closest('[data-manual-quant-draw]') && !state.busy) {
    manualQuant.current().roi = null;
    focusCrop = false;
    zoom = 1;
    render();
  }
});

document.addEventListener('change', event => {
  const input = event.target;
  if (!(input instanceof HTMLSelectElement)) return;
  if (input.id === 'quant-profile-view') manualQuant.profileView = input.value;
  else if (input.id === 'quant-profile-lane') {quantLane = Number(input.value); quantBand = null;}
  else if (input.id === 'quant-profile-band') quantBand = input.value;
  else return;
  manualQuant.refreshProfiles(true);
});

document.getElementById('quant-profiles-dialog').addEventListener('close', () => {
  manualQuant.profileBinding = null;
  manualQuant.profileKey = null;
  renderQuant();
});

document.addEventListener('input', event => {
  const input = event.target;
  if (!(input instanceof HTMLInputElement || input instanceof HTMLSelectElement)) return;
  const draft = manualQuant.current();
  if (!draft) return;
  if (input.dataset.manualQuantField) draft[input.dataset.manualQuantField] = input.value;
  if (input.dataset.manualQuantCoordinate) {
    const source = row();
    draft.roi ||= {x: 0, y: 0, width: source.width, height: source.height};
    draft.roi[input.dataset.manualQuantCoordinate] = Number(input.value);
    document.querySelectorAll('[data-manual-quant-run]').forEach(button => {button.disabled = state.busy || !bridge;});
    fitImage();
  }
});

const manualQuantViewport = document.getElementById('image-viewport');
manualQuantViewport.addEventListener('pointerdown', event => {
  const source = row();
  if (mode !== 'quant' || !manualQuant.isSetup() || state.busy || !bridge || !source?.preview) return;
  const rect = $('#image-transform').getBoundingClientRect();
  if (event.clientX < rect.left || event.clientX >= rect.right || event.clientY < rect.top || event.clientY >= rect.bottom) return;
  const start = manualQuant.point(event, rect, source);
  manualQuant.drawing = {id: source.id, rect, start, previous: manualQuant.current().roi};
  event.preventDefault();
  manualQuantViewport.setPointerCapture(event.pointerId);
});

manualQuantViewport.addEventListener('pointermove', event => {
  const drawing = manualQuant.drawing, source = row();
  if (!drawing || !source || source.id !== drawing.id || state.busy) return;
  const end = manualQuant.point(event, drawing.rect, source);
  manualQuant.current().roi = {
    x: Math.min(drawing.start.x, end.x), y: Math.min(drawing.start.y, end.y),
    width: Math.abs(end.x - drawing.start.x), height: Math.abs(end.y - drawing.start.y)
  };
  focusCrop = false;
  fitImage();
});

manualQuantViewport.addEventListener('pointerup', () => {
  if (!manualQuant.drawing) return;
  manualQuant.drawing = null;
  renderQuant();
});

manualQuantViewport.addEventListener('pointercancel', () => {
  if (!manualQuant.drawing) return;
  manualQuant.current().roi = manualQuant.drawing.previous;
  manualQuant.drawing = null;
  renderQuant();
});
