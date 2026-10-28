'use strict';
window.workbenchAppearance = (() => {
    const themes = [
        ['forest', '墨绿 × 酸橙'],
        ['ember', '炭黑 × 朱砂'],
        ['iris', '深靛 × 冰蓝'],
        ['neutral', '白灰'],
    ];
    let valid = { theme: 'forest', density: 'comfortable', motion: 'expressive' },
        selected = { ...valid },
        pending = null,
        queued = null,
        error = '',
        retryValues = null,
        migrated = false;
    const root = document.documentElement;
    const safeRead = (key) => {
        try {
            return localStorage.getItem(key);
        } catch {
            return null;
        }
    };
    function apply(value) {
        const anchor = root.dataset.density !== value.density ? document.activeElement : null;
        for (const key of ['theme', 'density', 'motion']) root.dataset[key] = value[key];
        window.uiMotion.sync();
        requestAnimationFrame(
            () =>
                anchor?.isConnected &&
                anchor.matches('input,select,button,textarea') &&
                anchor.scrollIntoView({ block: 'nearest', inline: 'nearest' }),
        );
    }
    function syncControls() {
        document
            .querySelectorAll('[data-appearance-theme]')
            .forEach((b) =>
                b.setAttribute(
                    'aria-pressed',
                    String(b.dataset.appearanceTheme === selected.theme),
                ),
            );
        document.querySelectorAll('[data-appearance-field]').forEach((el) => {
            el.value = selected[el.dataset.appearanceField];
        });
        const status = document.getElementById('appearance-status');
        if (status) {
            status.textContent = error || (pending ? '正在保存…' : '已保存到此应用');
            status.dataset.error = String(!!error);
        }
        const retry = document.getElementById('appearance-retry');
        if (retry) retry.hidden = !error;
    }
    function send(value) {
        selected = { ...value };
        error = '';
        apply(selected);
        if (pending) {
            queued = { ...selected };
            syncControls();
            return;
        }
        const requestId = 'appearance-' + Date.now() + '-' + Math.random().toString(36).slice(2);
        pending = { requestId, values: { ...selected } };
        if (
            !window.desktopSession?.request('appearance', {
                schema_version: 1,
                requestId,
                values: pending.values,
            })
        ) {
            try {
                localStorage.setItem('bioimage-appearance-preview-v1', JSON.stringify(selected));
                valid = { ...selected };
            } catch {
                error = '预览设置无法保存。请重试。';
                selected = { ...valid };
                apply(selected);
            }
            pending = null;
        }
        syncControls();
    }
    function receive(snapshot) {
        if (!snapshot || snapshot.schema_version !== 1) return;
        if (pending && snapshot.receipt !== pending.requestId) return;
        const failed = snapshot.error || '';
        if (failed && pending) retryValues = { ...pending.values };
        valid = { ...snapshot.values };
        error = failed;
        pending = null;
        if (!migrated) {
            migrated = true;
            if (!snapshot.configured && safeRead('bioimage-reduced-motion') === 'true') {
                send({ ...valid, motion: 'reduced' });
                return;
            }
        }
        if (queued && !failed) {
            const next = queued;
            queued = null;
            send(next);
            return;
        }
        queued = null;
        selected = { ...valid };
        apply(selected);
        syncControls();
    }
    function thumbnail() {
        // Real component classes and live tokens, not raster swatches.
        return '<span class="theme-mini" aria-hidden="true"><span class="theme-mini-header">BioImage <i></i></span><span class="theme-mini-body"><span class="theme-mini-nav"><b></b><b></b><b></b></span><span class="theme-mini-main"><strong>Fig 1</strong><span class="theme-mini-canvas"><svg viewBox="0 0 120 34"><path d="M5 27H115M5 27V5M7 25C18 25 18 5 26 5S32 25 43 25 53 12 60 12 65 25 78 25 89 5 96 5 100 25 114 25" fill="none" stroke="currentColor" stroke-width="1.6"/></svg></span><span class="button primary">继续</span></span></span></span>';
    }
    function open() {
        openDrawer(
            '外观与交互',
            `<div class="appearance-panel"><section><h3>配色</h3><div class="theme-options">${themes.map(([key, name]) => `<button class="theme-option" data-theme="${key}" data-appearance-theme="${key}" aria-pressed="${selected.theme === key}">${thumbnail()}<span>${name}<span class="theme-check">${icon('check')}</span></span></button>`).join('')}</div></section><section><label class="setting-row"><span>信息密度<small>保留全部内容，调整间距</small></span><select data-appearance-field="density" aria-label="信息密度"><option value="comfortable">舒展</option><option value="compact">紧凑</option></select></label><label class="setting-row"><span>动态效果<small>${matchMedia('(prefers-reduced-motion: reduce)').matches ? '系统已启用减少动态效果' : '切换、展开与悬停的反馈'}</small></span><select data-appearance-field="motion" aria-label="动态效果"><option value="expressive">丰富</option><option value="gentle">轻柔</option><option value="reduced">减少动态效果</option></select></label></section><div class="appearance-receipt"><p id="appearance-status" role="status"></p><button id="appearance-retry" class="text-button" hidden>重试保存</button></div><button class="button subtle full" data-action="shortcut-settings">${icon('sliders')}键盘快捷键</button></div>`,
        );
        syncControls();
    }
    document.addEventListener('click', (event) => {
        const choice = event.target.closest('[data-appearance-theme]');
        if (choice) send({ ...selected, theme: choice.dataset.appearanceTheme });
        if (event.target.closest('#appearance-retry')) send(retryValues || selected);
    });
    document.addEventListener('change', (event) => {
        const field = event.target.dataset.appearanceField;
        if (field) send({ ...selected, [field]: event.target.value });
    });
    valid = {
        theme: root.dataset.theme,
        density: root.dataset.density,
        motion: root.dataset.motion,
    };
    selected = { ...valid };
    apply(valid);
    return { open, receive, values: () => ({ ...selected }), apply };
})();
