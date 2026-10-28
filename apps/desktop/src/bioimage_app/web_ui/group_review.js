'use strict';

// Display-only group review. Every applied edit uses the original-pixel worker.
window.groupReview = (() => {
    const esc = escapeText;
    let manual = false,
        selection = null,
        draft = null,
        dragging = null;
    let contentKey = '',
        repaint = false,
        navigationKey = '',
        pendingFocus = false,
        tableFilter = 'all';
    let zoomLevel = 1,
        pan = null,
        pendingSelection = null;
    const root = document.createElement('section');
    root.id = 'gr-workspace';
    root.hidden = true;
    root.setAttribute('aria-label', '全组灰度审核');
    $('.workspace').append(root);
    const job = document.createElement('section');
    job.id = 'gr-progress';
    job.hidden = true;
    job.setAttribute('aria-label', '定量进度');
    job.innerHTML =
        '<div class="gr-job-top"><strong role="status" aria-live="polite"></strong><span></span><button class="button subtle" data-action="cancel">取消处理</button></div><div class="gr-track" role="progressbar" aria-label="当前阶段进度"><i></i></div><div class="gr-stages"><span>识别与规划</span><span>泳道定量</span><span>保存与核验</span></div>';
    $('.workspace').before(job);
    const back = document.createElement('button');
    back.className = 'button subtle gr-return';
    back.textContent = '返回全组审核';
    back.hidden = true;
    $('.source-panel .panel-heading').after(back);
    back.onclick = () => {
        manual = false;
        manualQuant.active = false;
        contentKey = '';
        render();
    };
    const group = () => state.quant?.group;
    function sizeTicks() {
        $$('.gr-curve>svg,#gr-edit-curve', root).forEach((svg) => {
            const r = svg.getBoundingClientRect(),
                v = svg.viewBox.baseVal,
                scale = Math.min(r.width / v.width, r.height / v.height);
            if (scale > 0) svg.style.setProperty('--gr-tick-size', `${11 / scale}px`);
        });
    }
    new ResizeObserver(() => requestAnimationFrame(sizeTicks)).observe(root);
    const chosen = () => {
        const protein = group()?.rows.find((r) => r.rowId === selection?.rowId);
        const lane = protein?.lanes.find((l) => l.lane === selection?.lane);
        const band = lane?.bands.find((b) => b.id === selection?.bandId) || lane?.bands[0];
        return { protein, lane, band };
    };
    const readyToEdit = () => !!bridge && !state.busy && selection?.rowId === state.quant?.rowId;
    const validBounds = (b, n) =>
        b &&
        [b.start, b.end, b.baselineStart, b.baselineEnd].every(Number.isFinite) &&
        b.start >= 0 &&
        b.end < n &&
        b.start < b.end;
    const identity = () => ({
        ...quantIdentity(),
        figure: group()?.figure,
        revision: state.quant?.revision,
    });
    function groups() {
        const map = new Map();
        const byId = new Map(state.rows.map((r) => [r.id, r]));
        for (const id of state.quant?.rowOrder || state.rows.map((r) => r.id)) {
            const r = byId.get(id);
            if (!r) continue;
            if (!map.has(r.fig)) map.set(r.fig, []);
            map.get(r.fig).push(r);
        }
        return [...map];
    }
    function navigation() {
        const key = JSON.stringify([
            state.projectId,
            state.sessionEpoch,
            state.quant?.revision,
            group()?.figure,
            search,
            state.quant?.reviewedGroups,
        ]);
        if (key === navigationKey) return;
        navigationKey = key;
        const all = groups(),
            reviewed = new Set(state.quant?.reviewedGroups || []);
        $('#source-count').textContent = all.length;
        $('#source-list').innerHTML =
            `<div class="gr-nav-title">Fig 分组 <small>${reviewed.size} / ${all.length} 已审核</small></div>` +
            all
                .filter(
                    ([f, rs]) =>
                        !search ||
                        (f + ' ' + rs.map((r) => r.protein).join(' '))
                            .toLowerCase()
                            .includes(search.toLowerCase()),
                )
                .map(
                    ([f, rs]) =>
                        `<button class="gr-group ${f === group()?.figure ? 'selected' : ''}" data-gr-group="${esc(rs[0].id)}" aria-pressed="${f === group()?.figure}"><strong>${esc(f)}<small>${reviewed.has(f) ? '已审核' : '待审核'}</small></strong><span>${rs.length} 个蛋白 · ${rs.reduce((n, r) => n + r.lanes, 0)} 条泳道</span></button>`,
                )
                .join('');
    }
    function geometry(lane, bands, large = false) {
        const values = lane.profile || [],
            w = large ? 640 : 260,
            h = large ? 210 : 135;
        let lo = 0,
            hi = 1;
        for (const v of [
            ...values,
            ...bands.flatMap((b) => [b.baselineStart, b.baselineEnd]).filter(Number.isFinite),
        ]) {
            lo = Math.min(lo, v);
            hi = Math.max(hi, v);
        }
        const span = hi - lo || 1;
        hi += span * 0.06;
        return {
            w,
            h,
            lo,
            hi,
            x: (i) => 48 + (i / Math.max(1, values.length - 1)) * (w - 60),
            y: (v) => 12 + ((hi - v) / (hi - lo)) * (h - 36),
        };
    }
    function curve(lane, large = false) {
        const values = lane.profile || [],
            bands = lane.bands.map((b) =>
                large && draft && b.id === selection?.bandId ? { ...b, ...draft } : b,
            );
        const G = geometry(lane, bands, large),
            { w, h, x, y } = G;
        if (!values.length)
            return {
                viewBox: `0 0 ${w} ${h}`,
                body: `<text x="${w / 2}" y="${h / 2}" text-anchor="middle">等待当前参数的曲线</text>`,
            };
        const lines = bands
            .filter((b) => b.included && validBounds(b, values.length))
            .map((b) => {
                const baseline = (i) =>
                    b.baselineStart +
                    ((b.baselineEnd - b.baselineStart) * (i - b.start)) / (b.end - b.start);
                const points = values
                    .slice(b.start, b.end + 1)
                    .map((v, i) => `${x(b.start + i)},${y(Math.max(v, baseline(b.start + i)))}`)
                    .join(' ');
                const editable = large && b.id === selection?.bandId;
                return `<polygon class="gr-area" points="${x(b.start)},${y(b.baselineStart)} ${points} ${x(b.end)},${y(b.baselineEnd)}"/><path class="gr-guide" d="M${x(b.start)} ${y(b.baselineStart)}V${h - 24} M${x(b.end)} ${y(b.baselineEnd)}V${h - 24}"/><path class="gr-baseline" d="M${x(b.start)} ${y(b.baselineStart)}L${x(b.end)} ${y(b.baselineEnd)}"/>${[0, 1].map((side) => `<circle class="gr-endpoint" ${editable ? `data-gr-end="${side}"` : ''} cx="${x(side ? b.end : b.start)}" cy="${y(side ? b.baselineEnd : b.baselineStart)}" r="${large ? 5 : 3}"/>`).join('')}`;
            })
            .join('');
        return {
            viewBox: `0 0 ${w} ${h}`,
            body: `<path class="gr-axis" d="M48 12V${h - 24}H${w - 12}"/>${lines}<path class="gr-line" d="${values.map((v, i) => (i ? 'L' : 'M') + x(i).toFixed(2) + ',' + y(v).toFixed(2)).join(' ')}"/><g class="gr-ticks"><text x="1" y="18">${Math.round(G.hi)}</text><text x="1" y="${h - 24}">${Math.round(G.lo)}</text><text x="48" y="${h - 6}">0</text><text x="${w - 12}" y="${h - 6}" text-anchor="end">${values.length - 1} y</text></g>`,
        };
    }
    function sourceImages() {
        const bySource = new Map();
        for (const p of group().rows) {
            if (!bySource.has(p.sourceId)) bySource.set(p.sourceId, []);
            bySource.get(p.sourceId).push(p);
        }
        return [...bySource]
            .map(([id, proteins]) => {
                const r = state.rows.find((r) => r.sourceId === id),
                    lanes = proteins.flatMap((p) => p.lanes.map((l) => ({ p, l }))),
                    boxes = lanes.map(({ l }) => l.roi);
                if (!r || !boxes.length) return '';
                const left = Math.min(...boxes.map((b) => b.x)),
                    top = Math.min(...boxes.map((b) => b.y)),
                    right = Math.max(...boxes.map((b) => b.x + b.width)),
                    bottom = Math.max(...boxes.map((b) => b.y + b.height));
                const x = Math.max(0, left - 145),
                    y = Math.max(0, top - 35),
                    w = Math.min(r.width, right + 20) - x,
                    h = Math.min(r.height, bottom + 25) - y;
                return `<div class="gr-source"><svg class="gr-image" viewBox="${x} ${y} ${w} ${h}" data-gr-view="${x},${y},${w},${h}" role="group" aria-label="${esc(group().figure)} 全部泳道框"><image href="${esc(r.preview || '')}" width="${r.width}" height="${r.height}"/>${lanes.map(({ p, l }) => `<rect class="gr-box" data-gr-row="${esc(p.rowId)}" data-gr-lane="${l.lane}" x="${l.roi.x}" y="${l.roi.y}" width="${l.roi.width}" height="${l.roi.height}" tabindex="0" role="button" aria-label="${esc(p.protein)} 泳道 ${l.lane}"/>`).join('')}</svg>${!r.preview ? '<p>正在载入原图预览；点击本原图曲线可加载。</p>' : ''}<small>${esc(r.name)}</small></div>`;
            })
            .join('');
    }
    function card(protein, lane) {
        const svg = curve(lane),
            included = lane.bands.filter((b) => b.included),
            warning = included.some(quantHasQuality),
            value = included.length === 1 ? included[0].signal : null;
        return `<button class="gr-curve" data-gr-row="${esc(protein.rowId)}" data-gr-lane="${lane.lane}" aria-label="${esc(protein.protein)}，泳道 ${lane.lane}，调整积分"><span class="gr-lane-title"><strong>泳道 ${lane.lane}</strong><small>${warning ? '需复核' : '待审核'}</small></span><svg viewBox="${svg.viewBox}" aria-hidden="true">${svg.body}</svg><span class="gr-lane-meta"><span>${included.length > 1 ? included.length + ' 个积分区间' : '灰度积分'}</span><strong>${value == null ? '—' : value.toFixed(2)}</strong></span></button>`;
    }
    function review() {
        const g = group(),
            count = g.rows.reduce((n, r) => n + r.lanes.length, 0),
            reviewed = state.quant.reviewedGroups?.includes(g.figure);
        root.innerHTML = `<header class="gr-heading"><div><h1>${esc(g.figure)}</h1><p>${g.rows.length} 个蛋白 · ${count} 条泳道 · 全组审核</p></div><div class="gr-actions"><span class="gr-review-state">${reviewed ? '已审核' : '待审核'}</span><button class="button subtle" data-gr-action="next">下一组</button><button class="button primary" data-gr-action="confirm">本组已审核，下一组</button></div></header><div class="gr-layout"><aside class="gr-image-panel"><div class="gr-section-heading"><h2>全组选框</h2><label><input type="checkbox" id="gr-boxes" checked> 显示选框</label></div><div id="gr-images">${sourceImages()}</div><div class="gr-image-tools"><button class="button subtle" data-gr-action="out" aria-label="缩小原图">−</button><button class="button subtle" data-gr-action="fit">适应</button><button class="button subtle" data-gr-action="in" aria-label="放大原图">+</button></div><p class="gr-selection-note">点击选框或曲线，展开积分调整</p><p class="gr-muted">滚轮缩放 · 拖动图像平移</p><div class="gr-image-actions"><button class="button subtle" data-gr-action="manual">手动泳道工具</button><button class="button subtle" data-gr-action="reset">重新自动封底（本组）</button></div><details class="gr-help"><summary>积分与封底说明</summary><p>绿色为原图逐行剖面，橙色为直线封底。浅绿色仅表示封底线上方的积分区域。UB 保留整段拖尾积分，可手动修改范围。</p><p>重新封底会替换本组当前积分范围和封底线并重算；历史结果保留。</p></details></aside><div class="gr-proteins"><div class="gr-section-heading"><h2>全组定量曲线</h2><span class="gr-legend"><i></i>原图曲线 <i></i>直线封底</span></div>${g.rows.map((p) => `<section class="gr-protein" data-gr-protein="${esc(p.rowId)}"><header><h3>${esc(p.protein || '未命名蛋白')}</h3><span>${p.lanes.length} 条泳道</span><button class="text-button" data-gr-manual="${esc(p.rowId)}">手动框选</button></header><div class="gr-lane-grid ${p.lanes.length > 4 ? 'many' : ''}">${p.lanes.map((l) => card(p, l)).join('') || '<p>尚未配置泳道，请手动框选或重新自动分组。</p>'}</div><div class="gr-editor-slot"></div></section>`).join('')}</div></div>`;
        zoomLevel = 1;
        highlight();
        editor();
    }
    function highlight() {
        $$('[data-gr-row]', root).forEach((el) =>
            el.classList.toggle(
                'selected',
                el.dataset.grRow === selection?.rowId &&
                    Number(el.dataset.grLane) === selection?.lane,
            ),
        );
    }
    function editor() {
        $$('.gr-editor-slot', root).forEach((el) => el.replaceChildren());
        const { protein, lane, band } = chosen();
        if (!lane || !band) return;
        selection.bandId = band.id;
        const slot = $$('.gr-protein', root)
            .find((el) => el.dataset.grProtein === protein.rowId)
            ?.querySelector('.gr-editor-slot');
        if (!slot) return;
        const b = draft ? { ...band, ...draft } : band,
            svg = curve(lane, true),
            disabled = !readyToEdit() ? 'disabled' : '';
        slot.innerHTML = `<div class="gr-editor"><header><h3>${esc(protein.protein)} · 泳道 ${lane.lane}</h3><button class="text-button" data-gr-action="close">收起调整</button></header><p class="gr-muted">拖动橙色端点调整范围和封底高度；也可输入精确数值。</p><label class="gr-band-label">积分区间 <select id="gr-band" ${disabled}>${lane.bands.map((b) => `<option value="${esc(b.id)}" ${b.id === band.id ? 'selected' : ''}>${esc(b.id)}${b.included ? '' : '（已排除）'}</option>`).join('')}</select></label><svg id="gr-edit-curve" viewBox="${svg.viewBox}" aria-label="积分边界与封底曲线">${svg.body}</svg><div class="gr-fields">${[
            ['start', '起点 y'],
            ['end', '终点 y'],
            ['baselineStart', '左端封底灰度'],
            ['baselineEnd', '右端封底灰度'],
        ]
            .map(
                ([field, label]) =>
                    `<label>${label}<input data-gr-field="${field}" type="number" value="${Number.isFinite(b[field]) ? Number(b[field]).toFixed(field === 'start' || field === 'end' ? 0 : 2) : ''}" step="${field === 'start' || field === 'end' ? 1 : 0.1}" ${disabled}></label>`,
            )
            .join(
                '',
            )}</div><footer><span>${state.busy ? '后台处理中，完成后可修改' : selection.rowId !== state.quant?.rowId ? '正在载入当前蛋白…' : draft ? '范围草稿，应用后后台重算' : '当前积分 ' + (band.signal == null ? '—' : band.signal.toFixed(2))}</span><button class="button primary" data-gr-action="apply" ${disabled || !draft ? 'disabled' : ''}>应用并重算</button></footer><details class="gr-help"><summary>质量与检测依据</summary><p>${esc(band.reason || '当前记录没有附加质量说明。')}</p></details></div>`;
        requestAnimationFrame(sizeTicks);
        if (pendingFocus) {
            pendingFocus = false;
            requestAnimationFrame(() =>
                slot.scrollIntoView({ block: 'nearest', behavior: 'auto' }),
            );
        }
    }
    function choose(rowId, lane, bandId) {
        selection = { rowId, lane, bandId };
        draft = null;
        pendingFocus = true;
        if (bridge && state.selectedId !== rowId)
            send('quant_select', { id: rowId, overview: false });
        highlight();
        editor();
    }
    function results() {
        const rows = (state.quant?.table || []).filter(
                (r) => tableFilter === 'all' || r.groupName === group()?.figure,
            ),
            max = Math.max(0, ...rows.flatMap((r) => r.values.map((v) => v.lane))),
            byGroup = new Map();
        for (const r of rows) {
            if (!byGroup.has(r.groupName)) byGroup.set(r.groupName, []);
            byGroup.get(r.groupName).push(r);
        }
        root.innerHTML = `<header class="gr-heading"><div><h1>灰度分析</h1><p>按 Fig 分组 · 两位小数 · 缺失结果留空</p></div><div class="gr-actions"><select id="gr-table-filter" aria-label="结果范围"><option value="all" ${tableFilter === 'all' ? 'selected' : ''}>全部分组</option><option value="current" ${tableFilter === 'current' ? 'selected' : ''}>当前分组</option></select><button class="button subtle" data-gr-export="csv">CSV</button><button class="button primary" data-gr-export="xlsx">导出 Excel</button></div></header><div class="gr-table-wrap"><table class="gr-table"><thead><tr><th>组序</th><th>Fig</th><th>蛋白 / 条带</th>${Array.from({ length: max }, (_, i) => `<th>泳道 ${i + 1}</th>`).join('')}</tr></thead><tbody>${[
            ...byGroup,
        ]
            .map(([f, rs]) =>
                rs
                    .map(
                        (r, i) =>
                            `<tr class="${i === 0 ? 'group-start' : ''}">${i === 0 ? `<td rowspan="${rs.length}" class="gr-order">${esc(r.groupOrder)}</td><td rowspan="${rs.length}" class="gr-fig">${esc(f)}</td>` : ''}<td class="gr-label">${esc(r.label)}</td>${Array.from(
                                { length: max },
                                (_, n) => {
                                    const v = r.values.find((v) => v.lane === n + 1);
                                    return `<td>${v?.signal == null ? '' : `<button data-gr-value="${esc(r.rowId)}" data-gr-lane="${n + 1}" data-gr-band="${esc(v.bandId || r.band)}" title="查看曲线与封底">${v.signal.toFixed(2)}</button>${quantHasQuality(v) ? '<sup aria-label="质量需复核">*</sup>' : ''}`}</td>`;
                                },
                            ).join('')}</tr>`,
                    )
                    .join(''),
            )
            .join(
                '',
            )}</tbody></table></div><p class="gr-table-note">${byGroup.size} 组 · ${rows.length} 行。* 表示质量需复核；显示原始积分不等于判定为有效信号。</p>${qualityDetails(rows.flatMap((r) => r.values.filter((v) => v.reason).map((v) => ({ reason: v.reason, label: `${r.groupName} / ${r.label} / 泳道 ${v.lane}` }))))}`;
    }
    function updateControls() {
        const configured =
            group()?.rows.length &&
            group().rows.every((p) => p.lanes.length && p.lanes.every((l) => l.profile?.length));
        $$(
            '[data-gr-action="confirm"],[data-gr-action="reset"],[data-gr-action="manual"],[data-gr-manual],[data-gr-export]',
            root,
        ).forEach(
            (el) =>
                (el.disabled =
                    !!state.busy || !bridge || (el.dataset.grAction === 'confirm' && !configured)),
        );
    }
    function renderActive() {
        const active =
            !state.intake?.figureEnabled &&
            ((mode === 'quant' && !manual && group()?.rows.some((r) => r.lanes.length)) ||
                (mode === 'results' && state.quant?.table?.length));
        document.body.classList.toggle('gr-active', !!active);
        root.hidden = !active;
        job.hidden = !state.busy || !['quant', 'results'].includes(mode);
        back.hidden = mode !== 'quant' || !manual;
        if (!active) {
            contentKey = '';
            navigationKey = '';
            return false;
        }
        navigation();
        if (pendingSelection && state.projectId !== pendingSelection.projectId)
            pendingSelection = null;
        if (pendingSelection && group()?.rows.some((r) => r.rowId === pendingSelection.rowId)) {
            selection = pendingSelection;
            pendingSelection = null;
            pendingFocus = true;
        }
        const key = JSON.stringify([
            state.projectId,
            state.sessionEpoch,
            state.quant?.revision,
            group()?.figure,
            mode,
            tableFilter,
            state.quant?.table?.length,
            state.quant?.resultRuns,
            state.quant?.reviewedGroups,
            [...new Set(state.rows.filter((r) => r.preview).map((r) => r.sourceId))],
        ]);
        if (key !== contentKey || repaint) {
            root.scrollTop = 0;
            if (key !== contentKey) {
                draft = null;
                if (!group()?.rows.some((r) => r.rowId === selection?.rowId)) selection = null;
            }
            contentKey = key;
            repaint = false;
            dragging = null;
            if (mode === 'results') results();
            else {
                review();
                requestAnimationFrame(sizeTicks);
            }
        } else if (selection && !dragging && !draft) editor();
        updateControls();
        return true;
    }
    function progress(patch) {
        state = { ...state, ...patch };
        const p = patch.progress || {},
            busy = !!patch.busy;
        $('#operation-status').textContent = patch.status || '就绪';
        $('#status-dot').classList.toggle('busy', busy);
        $('#cancel-button').hidden = !busy;
        $('#save-status').innerHTML = icon(busy ? 'curve' : 'check') + (busy ? '处理中' : '已就绪');
        job.hidden = !busy || !['quant', 'results'].includes(mode);
        updateControls();
        if (!busy) return;
        const phase = p.phase,
            index = phase === 'partition' || phase === 'planning' ? 0 : phase === 'save' ? 2 : 1;
        $('.gr-stages', job).hidden = ![
            'partition',
            'planning',
            'measure',
            'restore',
            'save',
        ].includes(phase);
        const known = index === 1 && Number.isInteger(p.total) && p.total > 0;
        $('.gr-job-top strong', job).textContent = known
            ? `${phase === 'restore' ? '核验曲线' : '正在定量'} · ${p.finished} / ${p.total} 条蛋白行`
            : index === 2
              ? '正在保存并核验结果'
              : p.label || '正在处理';
        $('.gr-job-top span', job).textContent = known
            ? `${p.label || ''}${p.failed ? ' · ' + p.failed + ' 行未完成' : ''}`
            : '完成后将更新审核曲线';
        const track = $('.gr-track', job),
            fill = $('i', track);
        track.classList.toggle('indeterminate', !known);
        if (known) {
            track.setAttribute('aria-valuenow', String(p.finished));
            track.setAttribute('aria-valuemax', String(p.total));
            fill.style.transform = `scaleX(${p.finished / p.total})`;
        } else {
            track.removeAttribute('aria-valuenow');
            fill.style.removeProperty('transform');
        }
        $$('.gr-stages span', job).forEach((el, i) => el.classList.toggle('current', i === index));
    }
    function manualMode(rowId = state.selectedId) {
        manual = true;
        manualQuant.active = false;
        quantDetail = true;
        manualLanes.toolsOpen = true;
        if (bridge && rowId !== state.selectedId)
            send('quant_select', { id: rowId, overview: false });
        render();
    }
    function next() {
        const all = groups(),
            i = all.findIndex(([f]) => f === group()?.figure),
            r = all[(i + 1) % all.length]?.[1][0];
        if (r) send('quant_select', { id: r.id, overview: false });
    }
    function apply() {
        const { lane, band } = chosen();
        if (!readyToEdit() || !draft || !lane) return;
        const b = { ...band, ...draft };
        if (!validBounds(b, lane.profile.length))
            return toast('请输入有效范围：起点小于终点，且在当前泳道内。');
        send('quant_edit', {
            ...quantIdentity(),
            id: selection.rowId,
            sourceId: state.quant.sourceId,
            revision: state.quant.revision,
            lane: selection.lane,
            bandId: selection.bandId,
            ...draft,
        });
        draft = null;
    }
    document.addEventListener('click', (e) => {
        const nav = e.target.closest('[data-gr-group]');
        if (nav) {
            send('quant_select', { id: nav.dataset.grGroup, overview: false });
            return;
        }
        const value = e.target.closest('[data-gr-value]');
        if (value) {
            manual = false;
            pendingSelection = {
                projectId: state.projectId,
                rowId: value.dataset.grValue,
                lane: Number(value.dataset.grLane),
                bandId: value.dataset.grBand,
            };
            state.selectedId = pendingSelection.rowId;
            quantLane = pendingSelection.lane;
            quantBand = pendingSelection.bandId;
            quantDetail = true;
            switchMode('quant');
            return;
        }
        const el = e.target.closest('[data-gr-row]');
        if (el && el.classList.contains('gr-curve')) {
            choose(el.dataset.grRow, Number(el.dataset.grLane));
            return;
        }
        const m = e.target.closest('[data-gr-manual]');
        if (m) {
            manualMode(m.dataset.grManual);
            return;
        }
        const exp = e.target.closest('[data-gr-export]');
        if (exp) {
            send('quant_export', { format: exp.dataset.grExport });
            return;
        }
        const action = e.target.closest('[data-gr-action]')?.dataset.grAction;
        if (action === 'next') next();
        if (action === 'manual') manualMode();
        if (action === 'confirm') send('quant_review_group', identity());
        if (action === 'reset') send('quant_reset_group', identity());
        if (action === 'close') {
            selection = null;
            draft = null;
            highlight();
            editor();
        }
        if (action === 'apply') apply();
        if (['fit', 'in', 'out'].includes(action))
            zoomImage(action === 'fit' ? 1 : zoomLevel * (action === 'in' ? 1.25 : 0.8));
    });
    document.addEventListener('change', (e) => {
        if (e.target.id === 'gr-boxes')
            $$('.gr-box', root).forEach(
                (el) => (el.style.visibility = e.target.checked ? 'visible' : 'hidden'),
            );
        if (e.target.id === 'gr-table-filter') {
            tableFilter = e.target.value;
            contentKey = '';
            renderActive();
        }
        if (e.target.id === 'gr-band') {
            selection.bandId = e.target.value;
            draft = null;
            editor();
        }
        if (e.target.matches('[data-gr-field]')) {
            const v = Number(e.target.value),
                field = e.target.dataset.grField;
            if (
                e.target.value === '' ||
                !Number.isFinite(v) ||
                (['start', 'end'].includes(field) && !Number.isInteger(v))
            )
                return toast('请输入有效数值；积分起止点使用整数像素。');
            draft = { ...draft, [field]: v };
            editor();
        }
    });
    function zoomImage(value) {
        zoomLevel = Math.max(1, Math.min(8, value));
        $$('.gr-image', root).forEach((svg) => {
            const [x, y, w, h] = svg.dataset.grView.split(',').map(Number),
                nw = w / zoomLevel,
                nh = h / zoomLevel;
            svg.setAttribute('viewBox', `${x + (w - nw) / 2} ${y + (h - nh) / 2} ${nw} ${nh}`);
        });
    }
    root.addEventListener(
        'wheel',
        (e) => {
            if (e.target.closest('.gr-image')) {
                e.preventDefault();
                zoomImage(zoomLevel * (e.deltaY < 0 ? 1.12 : 1 / 1.12));
            }
        },
        { passive: false },
    );
    root.addEventListener('pointerdown', (e) => {
        const point = e.target.closest('[data-gr-end]'),
            svg = e.target.closest('.gr-image');
        if (point && readyToEdit()) {
            const { lane, band } = chosen();
            if (!lane.profile.length || !validBounds({ ...band, ...draft }, lane.profile.length))
                return;
            e.preventDefault();
            const chart = $('#gr-edit-curve');
            chart.setPointerCapture(e.pointerId);
            dragging = {
                side: Number(point.dataset.grEnd),
                svg: chart,
                old: draft,
                band: { ...band, ...draft },
                geometry: geometry(
                    lane,
                    lane.bands.map((b) => (b.id === band.id ? { ...b, ...draft } : b)),
                    true,
                ),
                revision: state.quant.revision,
                projectId: state.projectId,
                sessionEpoch: state.sessionEpoch,
                rowId: selection.rowId,
            };
        } else if (svg) {
            pan = {
                svg,
                x: e.clientX,
                y: e.clientY,
                box: svg.getAttribute('viewBox').split(' ').map(Number),
                moved: false,
                rowId: e.target.dataset.grRow,
                lane: Number(e.target.dataset.grLane),
            };
            svg.setPointerCapture(e.pointerId);
        }
    });
    root.addEventListener('pointermove', (e) => {
        if (pan) {
            const { svg, box, x, y } = pan,
                rect = svg.getBoundingClientRect(),
                scale = Math.min(rect.width / box[2], rect.height / box[3]);
            pan.moved ||= Math.hypot(e.clientX - x, e.clientY - y) > 4;
            if (pan.moved)
                svg.setAttribute(
                    'viewBox',
                    `${box[0] - (e.clientX - x) / scale} ${box[1] - (e.clientY - y) / scale} ${box[2]} ${box[3]}`,
                );
            return;
        }
        if (!dragging) return;
        const d = dragging;
        if (
            state.busy ||
            state.projectId !== d.projectId ||
            state.sessionEpoch !== d.sessionEpoch ||
            state.quant.revision !== d.revision ||
            selection.rowId !== d.rowId
        ) {
            dragging = null;
            draft = null;
            editor();
            return;
        }
        const { lane } = chosen(),
            G = d.geometry,
            rect = d.svg.getBoundingClientRect(),
            scale = Math.min(rect.width / G.w, rect.height / G.h),
            px = (e.clientX - rect.left - (rect.width - G.w * scale) / 2) / scale,
            py = (e.clientY - rect.top - (rect.height - G.h * scale) / 2) / scale;
        const max = 2 ** (state.rows.find((r) => r.id === selection.rowId)?.bitDepth || 8) - 1,
            x = Math.round(((px - 48) / (G.w - 60)) * (lane.profile.length - 1)),
            y = Math.max(0, Math.min(max, G.hi - ((py - 12) / (G.h - 36)) * (G.hi - G.lo)));
        draft = d.side
            ? {
                  ...draft,
                  end: Math.max(d.band.start + 1, Math.min(lane.profile.length - 1, x)),
                  baselineEnd: y,
              }
            : { ...draft, start: Math.max(0, Math.min(d.band.end - 1, x)), baselineStart: y };
        d.svg.innerHTML = curve(lane, true).body;
        $$('[data-gr-field]', root).forEach((input) => {
            const v = draft[input.dataset.grField];
            if (v != null)
                input.value = Number(v).toFixed(
                    ['start', 'end'].includes(input.dataset.grField) ? 0 : 2,
                );
        });
    });
    root.addEventListener('pointerup', () => {
        if (dragging) {
            dragging = null;
            editor();
        }
        if (pan) {
            const was = pan;
            if (!pan.moved && pan.rowId) choose(pan.rowId, pan.lane);
            setTimeout(() => {
                if (pan === was) pan = null;
            }, 0);
        }
    });
    root.addEventListener('pointercancel', () => {
        if (dragging) {
            draft = dragging.old;
            dragging = null;
            editor();
        }
        pan = null;
    });
    document.addEventListener('keydown', (e) => {
        if ((e.key === 'Enter' || e.key === ' ') && e.target.matches('.gr-box')) {
            e.preventDefault();
            choose(e.target.dataset.grRow, Number(e.target.dataset.grLane));
        }
    });
    function checkpoint() {
        const saved = structuredClone({
            contentKey,
            manual,
            selection,
            draft,
            pendingFocus,
            tableFilter,
            zoomLevel,
            pendingSelection,
        });
        return () => {
            ({
                contentKey,
                manual,
                selection,
                draft,
                pendingFocus,
                tableFilter,
                zoomLevel,
                pendingSelection,
            } = saved);
            repaint = true;
            navigationKey = '';
            dragging = null;
            pan = null;
        };
    }
    return { renderActive, progress, manualMode, hasDraft: () => !!draft, checkpoint };
})();
