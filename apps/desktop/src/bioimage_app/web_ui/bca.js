(() => {
    'use strict';
    const get = (id) => document.getElementById(`bca-${id}`);
    const dialog = get('dialog'),
        form = get('record');
    let bridge = null,
        state = {},
        loadedRecord = false,
        shownRun = '';
    const fixed = {
        method_id: 'pierce25-point-v0-research',
        sop: 'MAN0011430 Rev D',
        sample_volume_ul: 25,
        working_reagent_ul: 200,
        reagent_a_to_b: '50:1',
        mixing_seconds: 30,
        incubation_c: 37,
        incubation_minutes: 30,
        wavelength_nm: 562,
        reading_kind: 'raw_absorbance',
    };
    const titles = {
        plate_id: '板',
        well: '孔',
        role: '类型',
        sample_id: '样本',
        technical_replicate: '技术重复',
        a562: '原始 A562',
        standard_ug_ml: '标准浓度',
        dilution_factor: '预稀释倍数',
        status: '状态',
        reason: '原因',
        method_id: '方法',
        api_version: '版本',
        blank_mean: '空白均值',
        corrected_a562: '扣空白 A562',
        standard_mean: '标准均值',
        standard_residual: '标准残差',
        assayed_ug_ml: '被测浓度 µg/mL',
        original_ug_ml: '原样浓度 µg/mL',
        n_total: '技术孔数',
        n_valid: '有效孔数',
        mean_original_ug_ml: '原样均值 µg/mL',
        sd_original_ug_ml: '技术 SD µg/mL',
    };
    const meanings = {
        research_estimate: '研究估计',
        partial: '部分受限（partial）',
        below_supported_range: '低于支持范围',
        above_supported_range: '高于支持范围',
        not_applicable: '不适用',
        blank: '空白',
        standard: '标准',
        sample: '样本',
        'calibration well': '校准孔',
        'LoQ and chemical accuracy unknown': 'LoQ 与化学准确性未知',
        'technical replicates only; LoQ unknown': '仅技术重复；LoQ 未知',
        'one or more wells outside supported range; no complete summary':
            '至少一孔超出范围，汇总留空',
        'below lowest nonzero standard (25 ug/mL); LoQ unknown': '低于 25 µg/mL；LoQ 未知',
        'above calibration; no extrapolation': '高于 2000 µg/mL；不外推',
    };
    const numeric = new Set([
        'a562',
        'standard_ug_ml',
        'dilution_factor',
        'blank_mean',
        'corrected_a562',
        'standard_mean',
        'standard_residual',
        'assayed_ug_ml',
        'original_ug_ml',
        'mean_original_ug_ml',
        'sd_original_ug_ml',
    ]);
    function table(id, rows) {
        const table = document.createElement('table');
        const head = table.createTHead().insertRow();
        const columns = Object.keys(rows[0] || {}).filter(
            (k) => !['method_id', 'api_version'].includes(k),
        );
        columns.forEach((key) => {
            const th = document.createElement('th');
            th.scope = 'col';
            th.textContent = titles[key] || key;
            head.append(th);
        });
        const body = table.createTBody();
        rows.forEach((row) => {
            const tr = body.insertRow();
            columns.forEach((key) => {
                const cell = tr.insertCell(),
                    value = row[key];
                cell.textContent =
                    value === ''
                        ? '—'
                        : numeric.has(key)
                          ? Number(value).toLocaleString('zh-CN', {
                                maximumSignificantDigits: 7,
                                useGrouping: false,
                            })
                          : meanings[value] || value;
                cell.title = value;
                if (key === 'reason') cell.className = 'result-reason';
            });
        });
        get(id).replaceChildren(table);
    }
    function render(raw) {
        const previousSource = state.source_sha256;
        state = JSON.parse(raw);
        if (!loadedRecord && previousSource && previousSource !== state.source_sha256) {
            form.querySelectorAll('[type=checkbox]').forEach((field) => {
                field.checked = false;
            });
        }
        get('status').textContent = state.message;
        get('status').dataset.tone = state.state === 'failed' ? 'error' : '';
        get('source').textContent =
            state.source ||
            (state.result ? '正在查看已保存项目；选择新 CSV 可开始另一板。' : '尚未选择 CSV');
        if (!loadedRecord) form.elements.source_sha256.value = state.source_sha256 || '';
        get('run').disabled = state.busy || !state.source;
        get('cancel').hidden = !state.running;
        get('new-record').disabled = state.busy;
        // Browsing home retains the live session and form; only app exit cancels it.
        Array.from(form.elements).forEach((field) => {
            field.disabled = state.busy;
        });
        document.querySelectorAll('[data-bca-choose]').forEach((button) => {
            button.disabled =
                state.busy || (button.dataset.bcaChoose === 'export' && !state.result);
        });
        get('results').hidden = !state.result;
        if (state.result) {
            get('result-origin').textContent =
                state.source || state.state !== 'succeeded'
                    ? '以下为先前已保存结果，尚不是本次输入的结果。'
                    : '当前项目的已保存结果';
            if (shownRun !== state.result.run_id) {
                shownRun = state.result.run_id;
                table('samples', state.result.samples);
                table('wells', state.result.wells);
                get('provenance').replaceChildren();
                for (const [title, value] of [
                    [
                        '方法',
                        state.result.provenance.method_id +
                            ' · API ' +
                            state.result.provenance.api_version,
                    ],
                    ['项目', state.result.workspace],
                    ['运行', shownRun],
                    ['CSV SHA256', state.result.source_sha256],
                ]) {
                    const dt = document.createElement('dt'),
                        dd = document.createElement('dd');
                    dt.textContent = title;
                    dd.textContent = value;
                    get('provenance').append(dt, dd);
                }
            }
        }
    }
    document.querySelectorAll('[data-bca-open]').forEach((button) =>
        button.addEventListener('click', () => {
            dialog.showModal();
            bridge?.refresh();
        }),
    );
    document
        .querySelectorAll('[data-bca-choose]')
        .forEach((button) =>
            button.addEventListener('click', () => bridge?.choose(button.dataset.bcaChoose)),
        );
    get('close').addEventListener('click', () => dialog.close());
    get('cancel').addEventListener('click', () => bridge?.cancel());
    get('new-record').addEventListener('click', () => {
        loadedRecord = false;
        form.reset();
        form.elements.source_sha256.value = state.source_sha256 || '';
    });
    get('run').addEventListener('click', () => {
        get('record-panel').open = true;
        if (!form.reportValidity()) return;
        const record = { ...fixed };
        Array.from(form.elements).forEach((field) => {
            record[field.name] = field.type === 'checkbox' ? field.checked : field.value;
        });
        bridge?.run(JSON.stringify(record));
    });
    window.bcaView = {
        connect(value) {
            bridge = value;
            bridge.changed.connect(render);
            bridge.recordLoaded.connect((raw) => {
                const record = JSON.parse(raw);
                loadedRecord = true;
                Array.from(form.elements).forEach((field) => {
                    if (field.type === 'checkbox') field.checked = record[field.name];
                    else field.value = record[field.name];
                });
            });
            bridge.refresh();
        },
    };
})();
