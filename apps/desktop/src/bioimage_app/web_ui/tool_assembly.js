'use strict';
window.toolAssembly = (() => {
    let bridge;
    let states = {};
    const selectors = {
        wb: '[data-page="wb"], [data-module-open]',
        nuclei: '[data-nuclei-open]',
        bca: '[data-bca-open]',
    };
    const panel = document.createElement('details');
    panel.className = 'workflow-entry';
    panel.innerHTML =
        '<summary>工具启用设置</summary><p>更改在下次启动生效；当前任务、原图和历史成果不会改变。工具安装由环境维护者准备。</p><div id="tool-enablement"></div><p id="tool-enablement-note" role="status"></p>';
    document.querySelector('.tool-catalogue').parentElement.append(panel);
    function render(raw) {
        states = JSON.parse(raw);
        const container = document.getElementById('tool-enablement');
        container.replaceChildren();
        for (const [key, value] of Object.entries(states)) {
            const label = document.createElement('label');
            const input = document.createElement('input');
            input.type = 'checkbox';
            input.checked = value.nextEnabled;
            input.disabled = value.state === 'missing';
            input.addEventListener('change', () => bridge.setEnabled(key, input.checked));
            label.append(input, document.createTextNode(value.message + ' · 下次启动启用 '));
            container.append(label);
            if (value.state !== 'enabled') {
                document.querySelectorAll(selectors[key]).forEach((button) => {
                    const hint = button.querySelector('.tool-readiness');
                    if (hint) hint.textContent = value.message + ' · 查看准备说明';
                });
            }
        }
        document.getElementById('tool-enablement-note').textContent = Object.values(states).some(
            (value) =>
                value.state !== 'missing' && (value.state === 'enabled') !== value.nextEnabled,
        )
            ? '设置已保存，重启后生效。'
            : '';
    }
    document.addEventListener(
        'click',
        (event) => {
            for (const [key, selector] of Object.entries(selectors)) {
                if (
                    event.target.closest(selector) &&
                    states[key] &&
                    states[key].state !== 'enabled'
                ) {
                    event.preventDefault();
                    event.stopImmediatePropagation();
                    panel.open = true;
                    document.getElementById('tool-enablement-note').textContent =
                        states[key].message +
                        '。请由维护者安装，或启用后重启；已有项目和成果保持原样。';
                    panel.scrollIntoView({ block: 'nearest' });
                    return;
                }
            }
        },
        true,
    );
    return {
        connect(value) {
            bridge = value;
            bridge.changed.connect(render);
            bridge.failed.connect((message) => {
                document.getElementById('tool-enablement-note').textContent = message;
            });
            bridge.refresh();
        },
    };
})();
