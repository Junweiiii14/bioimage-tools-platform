'use strict';

// Drafts remain bound to project/session/source/row/lane/band, never to list position.
window.intakeQuant = (() => {
    const drafts = new Map();
    let selected = null,
        drag = null,
        selectionKey = null,
        matrixAnchor = null,
        pendingEditor = null;
    let previewCollapsed = false;
    const fields = ['start', 'end', 'baselineStart', 'baselineEnd'];
    const values = (band) => Object.fromEntries(fields.map((k) => [k, band?.[k]]));
    const key = (lane, band) =>
        [state.projectId, state.sessionEpoch, row()?.id, row()?.sourceId, lane.lane, band.id].join(
            ':',
        );
    const geometry = (lane) => JSON.stringify([lane.roi, lane.targetRoi]);
    function entry(lane, band) {
        const id = key(lane, band),
            actual = values(band);
        let item = drafts.get(id);
        if (item && (item.sourceId !== row()?.sourceId || item.geometry !== geometry(lane)))
            item = null;
        if (
            item &&
            !item.submitted &&
            item.revision !== quantData()?.revision &&
            fields.some((k) => actual[k] !== item.original[k])
        )
            item = null;
        if (item?.submitted && fields.every((k) => actual[k] === item.value[k]))
            item.revision = quantData().revision;
        if (
            item?.submitted &&
            !state.busy &&
            quantData()?.status === 'ready' &&
            fields.every((k) => actual[k] === item.value[k])
        ) {
            drafts.delete(id);
            item = null;
        }
        return { id, item, actual };
    }
    function selection() {
        const lane = quantData()?.lanes?.find((l) => l.lane === selected),
            band = lane?.bands?.[0];
        if (!lane || !band) return null;
        const result = entry(lane, band);
        return { lane: lane.profile?.length ? lane : result.item?.lane || lane, band, ...result };
    }
    function change(next) {
        const s = selection();
        if (!s || state.busy) return;
        const item = s.item || {
            value: s.actual,
            original: s.actual,
            sourceId: row().sourceId,
            geometry: geometry(s.lane),
            undo: [],
            redo: [],
            revision: quantData().revision,
            lane: structuredClone(s.lane),
            rowId: row().id,
            project: state.projectId,
            epoch: state.sessionEpoch,
        };
        item.undo.push({ ...item.value });
        item.redo = [];
        item.value = { ...item.value, ...next };
        item.submitted = false;
        drafts.set(s.id, item);
    }
    function markup(lanes, protein, editorOnly = false) {
        const context = [state.projectId, state.sessionEpoch, protein?.protein_id].join(':');
        if (context !== selectionKey) {
            selected = null;
            drag = null;
            selectionKey = context;
        }
        const current = quantData();
        if (!protein || current?.rowId !== protein.protein_id)
            return '<section class="intake-profile-panel"><p>等待所选蛋白的已提交曲线…</p></section>';
        lanes = [...lanes];
        for (const lane of current.lanes || []) {
            const band = lane.bands?.[0];
            if (band && entry(lane, band).item && !lanes.some((l) => l.lane === lane.lane))
                lanes.push(lane);
        }
        const applicable = new Set(
            lanes.flatMap((l) =>
                l.bands?.[0] && entry(l, l.bands[0]).item ? [entry(l, l.bands[0]).id] : [],
            ),
        );
        const stale = [...drafts].filter(
            ([id, item]) =>
                item.project === state.projectId &&
                item.epoch === state.sessionEpoch &&
                item.rowId === protein.protein_id &&
                !applicable.has(id),
        );
        const warning = stale.length
            ? '<p role="status">有旧来源或旧范围的调整草稿，未应用到当前曲线。</p><button class="text-button" data-iq-action="discard-stale">丢弃过期草稿</button>'
            : '';
        const chosen = lanes.find((l) => l.lane === selected);
        const cards = lanes
            .map((lane) => {
                const band = lane.bands?.[0];
                if (!band) return '';
                const { item, actual } = entry(lane, band),
                    effective = { ...band, ...(item?.value || actual) };
                const shown = !lane.profile?.length && item ? item.lane : lane;
                return `<button class="intake-curve-card" data-iq-lane="${lane.lane}" aria-pressed="${lane.lane === selected}"><strong>泳道 ${lane.lane}</strong>${manualQuant.chart({ ...shown, bands: [effective] }, effective, false)}<span>0–${Math.max(0, shown.profile.length - 1)} y 像素 · 点击调整</span></button>`;
            })
            .join('');
        const visible = chosen ? [chosen] : [];
        const body = visible
            .map((lane) => {
                const band = lane.bands?.[0];
                if (!band) return '';
                const { item, actual } = entry(lane, band),
                    effective = { ...band, ...(item?.value || actual) };
                const editable = !!chosen;
                return `<section class="intake-quant-lane"><h3>泳道 ${lane.lane} · 封底调整</h3><p>拖动橙色圆点调整封底，拖动底部圆点调整积分范围；也可输入下方数值。</p>${manualQuant.chart({ ...(!lane.profile?.length && item ? item.lane : lane), bands: [effective] }, effective, editable).replaceAll('data-quant-point', 'data-iq-point')}
      ${
          editable
              ? `<div class="quant-fields">${fields.map((k) => `<label class="quant-field">${{ start: '积分起点 y', end: '积分终点 y', baselineStart: '起点封底', baselineEnd: '终点封底' }[k]}<input type="number" data-iq-field="${k}" value="${effective[k] ?? ''}" step="${k.startsWith('baseline') ? '.1' : '1'}" ${state.busy ? 'disabled' : ''}></label>`).join('')}</div>
      <div class="intake-stage-actions"><button class="button subtle" data-iq-action="undo" ${!item?.undo.length || state.busy ? 'disabled' : ''}>撤销</button><button class="button subtle" data-iq-action="redo" ${!item?.redo.length || state.busy ? 'disabled' : ''}>重做</button><button class="button subtle" data-iq-action="discard" ${!item || state.busy ? 'disabled' : ''}>放弃调整</button><button class="button primary" data-iq-action="save" ${!item || state.busy || !bridge ? 'disabled' : ''}>保存并重算</button></div><p role="status">${item ? '调整草稿尚未完成重算；当前结果不代表此草稿。' : '已提交曲线；坐标为泳道内原像素位置。'}</p>`
              : ''
      }
      ${qualityContent([{ reason: band.reason, label: '泳道 ' + lane.lane }])}</section>`;
            })
            .join('');
        if (editorOnly)
            return (
                warning +
                (body
                    ? `<section class="intake-figure-editor"><header><strong>${escapeText(row()?.fig || '')} · 蛋白 ${escapeText(protein.label)} · 泳道 ${selected}</strong><button class="text-button" data-iq-action="all">收起调整</button></header>${body}</section>`
                    : '')
            );
        return `<section class="intake-profile-panel"><header><strong>${escapeText(row()?.fig || '')} · 蛋白 ${escapeText(protein.label)} · ${lanes.length} 条泳道</strong><button class="text-button" data-iq-action="all">全部泳道概览</button></header><p class="intake-curve-help">每张图对应一条泳道，横轴为条带高度 y（原像素）。各图独立纵轴；点选曲线调整该泳道的峰底与积分范围。</p>${warning}<div class="intake-curve-overview">${cards}</div>${body || (!cards ? '<p>等待已提交的原像素曲线。</p>' : '<p>点击上方任意泳道曲线开始调整。</p>')}</section>`;
    }
    function figureMarkup(fig, members, quant) {
        if (!fig) return '<section class="intake-profile-panel"><p>等待 Fig 曲线。</p></section>';
        const rows = quant?.group?.rows || [],
            n = fig.lane_count || 0;
        const protein = members.find((p) => p.protein_id === row()?.id);
        const selectedLanes = rows.find((r) => r.rowId === protein?.protein_id)?.lanes || [];
        const editor = protein ? markup(selectedLanes, protein, true) : '';
        const columns = Array.from(
            { length: n },
            (_, i) =>
                `<strong class="intake-curve-column" data-iq-column="${i + 1}">泳道 ${i + 1}</strong>`,
        ).join('');
        const matrix = members
            .map((p) => {
                const lanes = rows.find((r) => r.rowId === p.protein_id)?.lanes || [];
                return (
                    `<strong class="intake-curve-protein" data-iq-protein="${escapeText(p.protein_id)}">${escapeText(p.label)}</strong>` +
                    Array.from({ length: n }, (_, i) => {
                        const lane = lanes.find((l) => l.lane === i + 1),
                            band = lane?.bands?.[0];
                        if (
                            !band ||
                            !lane.profile?.length ||
                            !lane.profile.every(Number.isFinite)
                        ) {
                            const pending = [...drafts.values()].some(
                                (d) =>
                                    d.project === state.projectId &&
                                    d.epoch === state.sessionEpoch &&
                                    d.rowId === p.protein_id &&
                                    d.lane?.lane === i + 1,
                            );
                            return pending
                                ? `<button class="intake-curve-missing" data-iq-row="${escapeText(p.protein_id)}" data-iq-lane="${i + 1}">暂无已提交曲线 · 处理草稿</button>`
                                : '<div class="intake-curve-missing">等待该泳道已提交曲线</div>';
                        }
                        return `<button class="intake-curve-card" data-iq-row="${escapeText(p.protein_id)}" data-iq-lane="${lane.lane}" aria-label="${escapeText(fig.label)} · 蛋白 ${escapeText(p.label)} · 泳道 ${lane.lane}，调整封底" aria-pressed="${p.protein_id === row()?.id && lane.lane === selected}">${manualQuant.chart(lane, band, false)}<span>泳道 ${lane.lane} · 0–${lane.profile.length - 1} y 像素${band.reason ? ' · 需复核' : ''}</span></button>`;
                    }).join('')
                );
            })
            .join('');
        return `<section class="intake-profile-panel"><header><strong>${escapeText(fig.label)} · ${members.length} 个蛋白 × ${n} 条泳道</strong><button class="text-button" data-iq-action="all">整组概览</button></header><p class="intake-curve-help">行对应蛋白，列对应泳道 · Shift + 滚轮横向浏览 · 各格纵轴独立</p><div class="intake-figure-curves-scroll" tabindex="0" role="region" aria-label="${escapeText(fig.label)} 曲线矩阵，可左右滚动"><div class="intake-figure-curves" style="grid-template-columns:88px repeat(${n},minmax(150px,1fr))"><strong class="intake-curve-corner">蛋白</strong>${columns}${matrix}</div></div>${editor}</section>`;
    }
    function highlight(cell) {
        const matrix = document.querySelector('.intake-figure-curves');
        if (!matrix) return;
        matrix
            .querySelectorAll('.matrix-hover')
            .forEach((el) => el.classList.remove('matrix-hover'));
        if (!cell) return;
        const rowId = cell.dataset.iqRow,
            lane = cell.dataset.iqLane;
        matrix
            .querySelectorAll('[data-iq-row],[data-iq-protein],[data-iq-column]')
            .forEach((el) => {
                if (
                    el.dataset.iqRow === rowId ||
                    el.dataset.iqProtein === rowId ||
                    el.dataset.iqLane === lane ||
                    el.dataset.iqColumn === lane
                )
                    el.classList.add('matrix-hover');
            });
    }
    document.addEventListener('pointerover', (event) => {
        const cell = event.target.closest('.intake-figure-curves [data-iq-row]');
        if (cell && !cell.contains(event.relatedTarget)) highlight(cell);
    });
    document.addEventListener('pointerout', (event) => {
        if (
            event.target.closest('.intake-figure-curves') &&
            !event.relatedTarget?.closest?.('.intake-figure-curves')
        )
            highlight(null);
    });
    document.addEventListener('focusin', (event) => {
        const cell = event.target.closest('.intake-figure-curves [data-iq-row]');
        if (cell) highlight(cell);
    });
    const refresh = () => window.intakeWorkspace.renderActive();
    const context = () => [state.projectId, state.sessionEpoch].join(':');
    // The selected protein may arrive in a later snapshot. Reveal only the matching
    // editor, and never let a queued reveal move a different page or selection.
    function afterRender() {
        const pending = pendingEditor;
        if (
            !pending ||
            pending.context !== context() ||
            pending.row !== row()?.id ||
            selected !== Number(pending.lane)
        )
            return;
        requestAnimationFrame(() => {
            if (
                pendingEditor !== pending ||
                matrixAnchor !== pending ||
                pending.context !== context() ||
                pending.row !== row()?.id ||
                selected !== Number(pending.lane) ||
                mode !== 'quant' ||
                !platformHome.inProject()
            )
                return;
            const editor = document.querySelector('.intake-figure-editor');
            const main = document.querySelector('.intake-measure-main'),
                heading = main?.querySelector('.canvas-heading');
            if (!main || !editor) return;
            pendingEditor = null;
            const bounds = main.getBoundingClientRect(),
                box = editor.getBoundingClientRect(),
                inset = (heading?.offsetHeight || 60) + 24;
            const top =
                box.top < bounds.top + inset || box.bottom > bounds.bottom
                    ? main.scrollTop + box.top - bounds.top - inset
                    : main.scrollTop;
            main.scrollTo({
                top,
                behavior: uiMotion.preference() === 'reduced' ? 'instant' : 'smooth',
            });
        });
    }
    document.addEventListener(
        'wheel',
        (event) => {
            if (drag) {
                event.preventDefault();
                return;
            }
            const scroll = event.target.closest('.intake-figure-curves-scroll');
            if (
                !scroll ||
                !event.shiftKey ||
                event.ctrlKey ||
                !event.deltaY ||
                Math.abs(event.deltaX) > Math.abs(event.deltaY)
            )
                return;
            event.preventDefault();
            scroll.scrollLeft +=
                event.deltaY *
                (event.deltaMode === 1 ? 20 : event.deltaMode === 2 ? scroll.clientWidth : 1);
        },
        { passive: false },
    );
    document.addEventListener('click', (event) => {
        const lane = event.target.closest('[data-iq-lane]');
        if (lane && !lane.disabled) {
            const scroll = document.querySelector('.intake-figure-curves-scroll'),
                main = document.querySelector('.intake-measure-main');
            matrixAnchor = {
                context: context(),
                row: lane.dataset.iqRow || row()?.id,
                lane: lane.dataset.iqLane,
                x: scroll?.scrollLeft || 0,
                y: main?.scrollTop || 0,
            };
            pendingEditor = matrixAnchor;
            selected = Number(lane.dataset.iqLane);
            const target = lane.dataset.iqRow;
            if (target && target !== row()?.id) {
                selectionKey = [state.projectId, state.sessionEpoch, target].join(':');
                select(target);
            } else refresh();
            return;
        }
        const action = event.target.closest('[data-iq-action]')?.dataset.iqAction;
        if (!action) return;
        if (action === 'toggle-preview') {
            previewCollapsed = !previewCollapsed;
            refresh();
            document
                .querySelector('[data-iq-action="toggle-preview"]')
                ?.focus({ preventScroll: true });
            return;
        }
        if (action === 'all') {
            selected = null;
            pendingEditor = null;
            const anchor = matrixAnchor;
            refresh();
            requestAnimationFrame(() => {
                if (
                    !anchor ||
                    anchor !== matrixAnchor ||
                    anchor.context !== context() ||
                    mode !== 'quant' ||
                    !platformHome.inProject()
                )
                    return;
                const scroll = document.querySelector('.intake-figure-curves-scroll'),
                    main = document.querySelector('.intake-measure-main');
                const cell = document.querySelector(
                    `[data-iq-row="${CSS.escape(anchor.row)}"][data-iq-lane="${anchor.lane}"]`,
                );
                if (!cell) return;
                if (scroll) scroll.scrollLeft = anchor.x;
                if (main) main.scrollTo({ top: anchor.y, behavior: 'instant' });
                cell.focus({ preventScroll: true });
            });
            return;
        }
        if (action === 'discard-stale' && !state.busy) {
            const valid = new Set(
                (quantData()?.lanes || []).flatMap((l) =>
                    l.bands?.[0] && entry(l, l.bands[0]).item ? [entry(l, l.bands[0]).id] : [],
                ),
            );
            for (const [id, item] of drafts)
                if (item.rowId === row()?.id && !valid.has(id)) drafts.delete(id);
            refresh();
            return;
        }
        const s = selection();
        if (!s?.item || state.busy) return;
        const item = s.item;
        if (action === 'discard') drafts.delete(s.id);
        if (action === 'undo' && item.undo.length) {
            item.redo.push(item.value);
            item.value = item.undo.pop();
        }
        if (action === 'redo' && item.redo.length) {
            item.undo.push(item.value);
            item.value = item.redo.pop();
        }
        if (action === 'save') {
            const v = item.value;
            if (
                fields.some((k) => !Number.isFinite(v[k])) ||
                !Number.isInteger(v.start) ||
                !Number.isInteger(v.end) ||
                v.start < 0 ||
                v.start >= v.end ||
                v.end >= s.lane.profile.length ||
                v.baselineStart < 0 ||
                v.baselineEnd < 0
            )
                return toast('请使用泳道内的整数积分边界和非负有限封底。');
            if (item.revision !== quantData().revision && !item.submitted)
                return toast('参数已变化，请放弃旧调整后重新核对。');
            item.submitted = true;
            send('quant_edit', { ...quantIdentity(), lane: s.lane.lane, bandId: s.band.id, ...v });
        }
        refresh();
    });
    document.addEventListener('change', (event) => {
        const input = event.target;
        if (!input.matches('[data-iq-field]')) return;
        if (input.value === '' || !Number.isFinite(Number(input.value)))
            return toast('请输入有效数值');
        change({ [input.dataset.iqField]: Number(input.value) });
        refresh();
    });
    document.addEventListener('pointerdown', (event) => {
        const point = event.target.closest('[data-iq-point]'),
            s = selection();
        if (!point || !s || state.busy || !bridge) return;
        event.preventDefault();
        const band = { ...s.band, ...(s.item?.value || s.actual) };
        drag = {
            id: s.id,
            geometry: geometry(s.lane),
            revision: quantData()?.revision,
            key: point.dataset.iqPoint,
            rect: point.closest('svg').getBoundingClientRect(),
            g: profileGeometry(s.lane, band),
            band,
        };
        document.body.setPointerCapture(event.pointerId);
    });
    const sameDrag = (s, d) =>
        s &&
        s.id === d.id &&
        geometry(s.lane) === d.geometry &&
        quantData()?.revision === d.revision;
    function pointerValue(event, d, s) {
        const x = ((event.clientX - d.rect.left) / d.rect.width) * 680,
            y = ((event.clientY - d.rect.top) / d.rect.height) * 196;
        let value = d.key.startsWith('baseline')
            ? Math.max(0, d.g.min + ((156 - y) / 128) * d.g.span)
            : Math.round(((x - 44) / 612) * (s.lane.profile.length - 1));
        if (d.key === 'start') value = Math.max(0, Math.min(d.band.end - 1, value));
        if (d.key === 'end')
            value = Math.max(d.band.start + 1, Math.min(s.lane.profile.length - 1, value));
        return value;
    }
    document.addEventListener('pointermove', (event) => {
        if (!drag) return;
        const s = selection();
        if (!sameDrag(s, drag) || state.busy) {
            drag = null;
            refresh();
            return;
        }
        const svg = document.querySelector('.intake-quant-lane .quant-chart');
        if (svg) {
            const band = { ...drag.band, [drag.key]: pointerValue(event, drag, s) };
            svg.outerHTML = manualQuant
                .chart({ ...s.lane, bands: [band] }, band, true)
                .replaceAll('data-quant-point', 'data-iq-point');
        }
    });
    document.addEventListener('pointerup', (event) => {
        if (!drag) return;
        const d = drag;
        drag = null;
        const s = selection();
        if (!sameDrag(s, d) || state.busy) {
            refresh();
            return;
        }
        change({ [d.key]: pointerValue(event, d, s) });
        refresh();
    });
    document.addEventListener('pointercancel', () => {
        drag = null;
        refresh();
    });
    document.addEventListener('keydown', (event) => {
        const point = event.target.closest('[data-iq-point]'),
            s = selection();
        if (
            !point ||
            !s ||
            event.isComposing ||
            state.busy ||
            !['ArrowLeft', 'ArrowRight', 'ArrowUp', 'ArrowDown'].includes(event.key)
        )
            return;
        event.preventDefault();
        const k = point.dataset.iqPoint,
            v = s.item?.value || s.actual;
        let value =
            v[k] +
            (['ArrowLeft', 'ArrowDown'].includes(event.key) ? -1 : 1) * (event.shiftKey ? 10 : 1);
        value =
            k === 'start'
                ? Math.max(0, Math.min(v.end - 1, value))
                : k === 'end'
                  ? Math.max(v.start + 1, Math.min(s.lane.profile.length - 1, value))
                  : Math.max(0, value);
        change({ [k]: value });
        refresh();
        document.querySelector(`[data-iq-point="${k}"]`)?.focus();
    });
    return {
        checkpoint: () => {
            const saved = structuredClone({
                drafts,
                selected,
                selectionKey,
                matrixAnchor,
                pendingEditor,
                previewCollapsed,
            });
            return () => {
                ({ selected, selectionKey, matrixAnchor, pendingEditor, previewCollapsed } = saved);
                drafts.clear();
                saved.drafts.forEach((value, key) => drafts.set(key, value));
                drag = null;
            };
        },
        markup,
        figureMarkup,
        afterRender,
        previewCollapsed: () => previewCollapsed,
        hasDraft: () => drafts.size > 0,
        reset: () => {
            drafts.clear();
            selected = null;
            drag = null;
            selectionKey = null;
            matrixAnchor = null;
            pendingEditor = null;
        },
        selectedLane: () => selected,
    };
})();
