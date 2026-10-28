'use strict';

// Shell navigation is independent of the owned project session. Browsing the platform
// never sends the destructive session('home') command or replaces a tool's draft.
window.platformHome = (() => {
    let view = 'platform';
    const positions = new Map();
    const views = { platform: '#platform-view', wb: '#home-view', project: '#work-view' };
    const hasProject = () => !!state.projectId && (state.rows.length > 0 || !!state.intake);
    const scrollables = () =>
        $$(
            '#platform-view,#home-view,#source-list,#intake-workspace,.intake-measure-main,.intake-figure-list,.intake-measure-inspector,.intake-figure-curves-scroll,.results-scroll,#quant-profile,.inspector-content',
        );
    function remember() {
        positions.set(view, {
            focus: document.activeElement,
            scroll: scrollables().map((el) => ({
                key: el.id ? '#' + el.id : '.' + el.classList[0],
                x: el.scrollLeft,
                y: el.scrollTop,
            })),
        });
    }
    function sync() {
        document.body.dataset.surface = view;
        Object.entries(views).forEach(([key, selector]) => {
            $(selector).hidden = key !== view;
        });
        $('#project-name').textContent = state.projectName;
        $$('[data-resume-project]').forEach((el) => {
            el.hidden = !hasProject();
        });
        $$('[data-current-project-name]').forEach((el) => {
            el.textContent = state.projectName;
        });
        const platform = view === 'platform',
            project = view === 'project';
        $('#breadcrumb-tool').hidden = platform;
        $('#breadcrumb-tool-separator').hidden = platform;
        $('#breadcrumb-project-separator').hidden = !project;
        $('#project-name').hidden = !project;
        $('#platform-open').hidden = !platform;
        $('#session-menu').hidden = platform;
        $('#save-status').hidden = !project;
        $$('.header-actions>[data-action=import],.header-actions>[data-action=export]').forEach(
            (el) => (el.hidden = !project || !!state.intake),
        );
    }
    function show(next, { focus = true } = {}) {
        if (!views[next]) return;
        if (next === 'project' && !hasProject()) next = 'wb';
        const previous = view;
        if (previous !== next) remember();
        view = next;
        sync();
        if (next === 'project') render();
        if (previous === next) return;
        const root = $(views[next]);
        uiMotion.enter(root);
        const saved = positions.get(next);
        for (const item of saved?.scroll || []) {
            const node = $(item.key);
            if (node) {
                node.scrollLeft = item.x;
                node.scrollTop = item.y;
            }
        }
        requestAnimationFrame(() => {
            if (view !== next) return;
            if (focus) {
                const target =
                    saved?.focus?.isConnected && root.contains(saved.focus)
                        ? saved.focus
                        : root.querySelector('h1,h2');
                if (target) {
                    if (!target.matches('button,input,select,a'))
                        target.setAttribute('tabindex', '-1');
                    target.focus({ preventScroll: true });
                }
            }
            if (next === 'project') {
                updateModeIndicator();
                fitImage();
                window.dispatchEvent(new Event('resize'));
            }
        });
    }
    function closed() {
        positions.delete('project');
        show(view === 'platform' ? 'platform' : 'wb');
    }
    document.addEventListener('click', (event) => {
        const button = event.target.closest('[data-page]');
        if (!button) return;
        event.preventDefault();
        show(button.dataset.page);
    });
    sync();
    return {
        show,
        sync,
        closed,
        inProject: () => view === 'project',
        current: () => view,
        checkpoint: () => {
            const previous = view,
                saved = new Map(positions);
            return () => {
                view = previous;
                positions.clear();
                saved.forEach((value, key) => positions.set(key, value));
            };
        },
    };
})();

window.folderDrop = (() => {
    const clear = () =>
        $$('[data-folder-drop].folder-drop-active').forEach((el) =>
            el.classList.remove('folder-drop-active'),
        );
    function target(x, y, hover) {
        clear();
        const el = document.elementFromPoint(x, y)?.closest('[data-folder-drop]');
        const accepted =
            platformHome.current() === 'platform' &&
            !!el &&
            !document.querySelector('dialog[open]');
        if (accepted && hover) el.classList.add('folder-drop-active');
        return accepted;
    }
    function message(text) {
        $('#folder-drop-status').textContent = text;
        toast(text);
    }
    window.addEventListener('blur', clear);
    document.addEventListener('drop', clear);
    return { target, clear, message };
})();
