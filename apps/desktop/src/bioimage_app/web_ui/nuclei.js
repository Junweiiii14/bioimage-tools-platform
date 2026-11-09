(() => {
    'use strict';
    const get = (id) => document.getElementById(`nuclei-${id}`);
    const dialog = get('dialog');
    let bridge = null,
        state = {},
        overlay = false;
    function image() {
        const node = get('image');
        const url = overlay ? state.overlay : state.original;
        if (url && node.getAttribute('src') !== url) node.src = url;
        node.alt = overlay ? '原像素坐标实例轮廓（仅显示）' : '原图预览';
        const zoom = get('zoom').value;
        node.style.width = zoom === 'fit' ? '' : `${node.naturalWidth * Number(zoom)}px`;
        node.classList.toggle('actual-size', zoom !== 'fit');
        get('original').setAttribute('aria-pressed', String(!overlay));
        get('overlay').setAttribute('aria-pressed', String(overlay));
    }
    function render(raw) {
        const previousRun = state.run_id;
        state = JSON.parse(raw);
        if (!state.overlay) overlay = false;
        else if (state.run_id !== previousRun) overlay = true;
        get('status').textContent = state.message;
        get('status').dataset.tone = state.state === 'failed' ? 'error' : '';
        get('run').disabled = state.busy || !state.source;
        get('cancel').hidden = !state.running;
        document.getElementById('nuclei-readiness').textContent =
            state.worker && state.model ? '已配置 · 运行前核验' : '首次使用需准备环境';
        document.querySelectorAll('[data-nuclei-choose]').forEach((button) => {
            button.disabled =
                state.busy ||
                (['export', 'intensity'].includes(button.dataset.nucleiChoose) &&
                    state.count === null);
        });
        get('overlay').disabled = !state.overlay;
        get('image-section').hidden = !state.original;
        get('count').textContent = state.count === null ? '尚无结果' : `已保存核数 ${state.count}`;
        get('source').textContent = state.source || '已保存原图 · 原像素坐标';
        get('workspace').textContent = state.workspace || '分析后自动保存';
        get('sha').textContent = state.source_sha256 || '';
        get('run-id').textContent = state.run_id || '尚未提交';
        get('worker').textContent = state.worker || '尚未设置';
        get('model').textContent = state.model || '尚未设置';
        if (state.state === 'failed' && (!state.worker || !state.model))
            get('settings').hidden = false;
        image();
    }
    document.querySelectorAll('[data-nuclei-open]').forEach((button) => {
        button.addEventListener('click', () => {
            dialog.showModal();
            bridge?.refresh();
        });
    });
    document.querySelectorAll('[data-nuclei-choose]').forEach((button) => {
        button.addEventListener('click', () => bridge?.choose(button.dataset.nucleiChoose));
    });
    get('run').addEventListener('click', () => bridge?.run());
    get('cancel').addEventListener('click', () => bridge?.cancel());
    get('close').addEventListener('click', () => dialog.close());
    get('help').addEventListener('click', () => bridge?.help());
    get('settings-toggle').addEventListener('click', () => {
        get('settings').hidden = !get('settings').hidden;
    });
    get('original').addEventListener('click', () => {
        overlay = false;
        image();
    });
    get('overlay').addEventListener('click', () => {
        overlay = true;
        image();
    });
    get('zoom').addEventListener('change', image);
    get('image').addEventListener('load', image);
    window.nucleiView = {
        connect(value) {
            bridge = value;
            bridge.changed.connect(render);
            bridge.refresh();
        },
    };
})();
