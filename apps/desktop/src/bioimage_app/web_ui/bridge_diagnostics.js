'use strict';

// Diagnostic metadata only: never forward exception messages, JSON, image bytes
// or full URLs. The desktop sink validates and limits this envelope again.
const boundaryDiagnostics = (() => {
    let channel = null;
    const failed = new Set();
    function report(action, failure, context = {}) {
        if (failed.has(action)) return;
        failed.add(action);
        const event = {
            action,
            phase: context.phase || 'render',
            requestId: context.requestId || '',
            operation: context.operation || '',
            sessionEpoch: context.sessionEpoch,
            revision: context.revision,
            exception: 'Error',
            stack: [],
        };
        try {
            if (failure instanceof Error) {
                event.exception = failure.name;
                event.stack = (failure.stack || '')
                    .split('\n')
                    .slice(1)
                    .flatMap((line) => {
                        const match = line.match(
                            /(?:[/\\])([a-z_]{1,40}\.js):([0-9]{1,7}):([0-9]{1,7})/,
                        );
                        return match ? [match.slice(1).join(':')] : [];
                    })
                    .slice(0, 8);
            }
            channel?.reportUiFailure(JSON.stringify(event));
        } catch {
            // A failed diagnostic transport must not replace the original error.
        }
        toast('界面更新失败，编辑已保留。请重试当前操作；持续失败时提供本机会话日志。');
    }
    function recovered(action) {
        if (!failed.delete(action)) return;
        try {
            channel?.reportUiFailure(JSON.stringify({ action, recovered: true }));
        } catch {
            // Recovery is already valid even when diagnostic transport is unavailable.
        }
    }
    function connect(next) {
        channel = next;
        channel.diagnosticNotice?.connect((message) => toast(message));
    }
    return { report, recovered, connect };
})();

// These objects contain local numeric/form edits plus methods. Gestures are
// cancelled on rollback; no DOM node, image or scientific snapshot is cloned.
function checkpointManualEditor(editor) {
    const saved = structuredClone(
        Object.fromEntries(
            Object.entries(editor).filter(
                ([key, value]) =>
                    typeof value !== 'function' && !['drawing', 'dragging'].includes(key),
            ),
        ),
    );
    return () => {
        Object.assign(editor, saved);
        if ('drawing' in editor) editor.drawing = null;
        if ('dragging' in editor) editor.dragging = null;
        if ('profileKey' in editor) editor.profileKey = null;
    };
}

function channelObject(raw) {
    const value = typeof raw === 'string' ? JSON.parse(raw) : raw;
    if (!value || typeof value !== 'object' || Array.isArray(value))
        throw new TypeError('Invalid channel object');
    return value;
}

function requireStateIdentity(value) {
    if (
        typeof value.projectId !== 'string' ||
        !value.projectId ||
        !Number.isSafeInteger(value.sessionEpoch) ||
        value.sessionEpoch < 0 ||
        !Number.isSafeInteger(value.revision) ||
        value.revision < 0
    )
        throw new TypeError('Invalid state identity');
}

function requireProjectState(value) {
    requireStateIdentity(value);
    if (
        !Array.isArray(value.rows) ||
        !Array.isArray(value.cells) ||
        value.rows.some((row) => !row || typeof row !== 'object' || typeof row.id !== 'string') ||
        value.cells.some((cell) => !cell || typeof cell !== 'object')
    )
        throw new TypeError('Invalid project collection');
}
