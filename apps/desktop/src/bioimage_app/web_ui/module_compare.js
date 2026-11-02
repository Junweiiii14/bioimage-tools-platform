(() => {
    'use strict';
    const dialog = document.querySelector('#module-compare-dialog');
    const status = document.querySelector('#module-status');
    let bridge = null;
    let current = { busy: false, state: 'idle', tables_json: {}, files: {}, workspace: '' };
    let view = 'differences';
    let closing = false;
    const states = {
        valid: '有效',
        invalid: '无效',
        quality_review: '待复核',
        excluded: '已排除',
        not_detected: '未检出',
    };
    const columns = {
        differences: [
            ['sample_id', '样本'],
            ['metric', '指标'],
            ['baseline_value', '旧入口'],
            ['module_value', '独立模块'],
            ['difference', '差值'],
            ['module_status', '状态'],
            ['module_reason', '原因'],
        ],
        measurements: [
            ['sample_id', '样本'],
            ['metric', '指标'],
            ['value', '有效信号'],
            ['raw_integral_for_review', '原始积分'],
            ['status', '状态'],
            ['reason', '原因'],
        ],
    };
    function send(action, data = {}) {
        bridge?.request(action, JSON.stringify(data));
    }
    function render() {
        const busy = current.busy;
        status.textContent =
            current.message ||
            (bridge ? '选择固定样例并运行对照。' : '请在桌面工作台运行；网页预览不会执行计算。');
        status.dataset.tone =
            current.state === 'failed' ? 'error' : current.quality === 'issues' ? 'warning' : '';
        document.querySelector('#module-case').disabled = busy;
        document.querySelector('#module-run').disabled = busy || !bridge;
        document.querySelector('#module-open').disabled = busy || !bridge;
        document.querySelector('#module-cancel').hidden = !busy;
        document.querySelector('#module-reopen').disabled = busy || !current.workspace || !bridge;
        document.querySelector('#module-folder').disabled =
            busy || current.state !== 'succeeded' || !bridge;
        document.querySelector('#module-close').textContent = busy ? '取消并关闭' : '关闭';
        dialog
            .querySelectorAll('[data-module-view]')
            .forEach((button) =>
                button.setAttribute('aria-pressed', String(button.dataset.moduleView === view)),
            );
        const table = document.querySelector('#module-table');
        table.replaceChildren();
        const raw = current.tables_json?.[view];
        document.querySelector('#module-empty').hidden = !!raw;
        document.querySelector('#module-table-wrap').hidden = !raw;
        document.querySelector('#module-count').textContent = '';
        if (raw) {
            const data = JSON.parse(raw);
            if (
                !Array.isArray(data.columns) ||
                !Array.isArray(data.rows) ||
                data.rows.length > 200 ||
                !data.rows.every(
                    (row) =>
                        Array.isArray(row) &&
                        row.length === data.columns.length &&
                        row.every((cell) => typeof cell === 'string'),
                )
            )
                throw new TypeError('Invalid comparison table');
            const head = table.createTHead().insertRow();
            columns[view].forEach(([, label]) => {
                const th = document.createElement('th');
                th.scope = 'col';
                th.textContent = label;
                head.append(th);
            });
            const body = table.createTBody();
            data.rows.forEach((row) => {
                const tr = body.insertRow();
                columns[view].forEach(([key]) => {
                    const value = row[data.columns.indexOf(key)] ?? '';
                    tr.insertCell().textContent = key.endsWith('status')
                        ? states[value] || value
                        : value || '—';
                });
            });
            document.querySelector('#module-count').textContent =
                `${data.total_rows} 项测量${data.total_rows > 200 ? ' · 显示前 200 项' : ''}`;
        }
        const run = current.run;
        document.querySelector('#module-provenance').hidden = !run;
        document.querySelector('#module-workspace').textContent = current.workspace || '—';
        document.querySelector('#module-run-id').textContent = run?.run_id || '—';
        document.querySelector('#module-pid').textContent = run?.pid ? String(run.pid) : '未启动';
        document.querySelector('#module-method').textContent =
            'profile_integral@1 · legacy_bounds@1';
        if (closing && !busy) {
            closing = false;
            dialog.close();
        }
    }
    function receive(raw) {
        try {
            const next = JSON.parse(raw);
            if (
                typeof next.busy !== 'boolean' ||
                typeof next.state !== 'string' ||
                typeof next.message !== 'string'
            )
                throw new TypeError('Invalid comparison state');
            current = next;
            render();
        } catch {
            document.querySelector('#module-table').replaceChildren();
            status.textContent = '对照状态读取失败。请关闭后重新打开工程核验。';
            status.dataset.tone = 'error';
        }
    }
    function close() {
        if (current.busy) {
            closing = true;
            send('cancel');
        } else dialog.close();
    }
    document.querySelector('[data-module-open]').addEventListener('click', () => {
        closing = false;
        if (!dialog.open) dialog.showModal();
        render();
        send('refresh');
    });
    document
        .querySelector('#module-run')
        .addEventListener('click', () =>
            send('run', { case: document.querySelector('#module-case').value }),
        );
    document.querySelector('#module-open').addEventListener('click', () => send('open'));
    document.querySelector('#module-reopen').addEventListener('click', () => send('reopen'));
    document.querySelector('#module-folder').addEventListener('click', () => send('folder'));
    document.querySelector('#module-cancel').addEventListener('click', () => send('cancel'));
    document.querySelector('#module-close').addEventListener('click', close);
    dialog.addEventListener('cancel', (event) => {
        event.preventDefault();
        close();
    });
    dialog.querySelectorAll('[data-module-view]').forEach((button) =>
        button.addEventListener('click', () => {
            view = button.dataset.moduleView;
            render();
        }),
    );
    window.moduleComparison = {
        connect(value) {
            if (!value) return;
            bridge = value;
            bridge.stateChanged.connect(receive);
            send('refresh');
        },
    };
})();
