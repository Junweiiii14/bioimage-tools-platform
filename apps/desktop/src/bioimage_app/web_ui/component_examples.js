'use strict';
document.querySelectorAll('[data-config]').forEach((control) => {
    control.addEventListener('change', () => {
        document.documentElement.dataset[control.dataset.config] = control.value;
        uiMotion.sync();
    });
});
const receipt = document.getElementById('sample-receipt');
let receiptTimer;
function saveSample(fail) {
    clearTimeout(receiptTimer);
    receipt.textContent = '正在保存示例…';
    receipt.style.color = 'var(--muted)';
    receiptTimer = setTimeout(() => {
        receipt.textContent = fail
            ? '× 演示保存失败，编辑已保留。可点击保存重试。'
            : '✓ 演示回执已收到。';
        receipt.style.color = fail ? 'var(--danger)' : 'var(--accent)';
        uiMotion.enter(receipt);
    }, 450);
}
document.getElementById('sample-save').onclick = () => saveSample(false);
document.getElementById('sample-error').onclick = () => saveSample(true);
document.getElementById('sample-disclosure').onclick = (event) => {
    const button = event.currentTarget;
    const detail = document.getElementById('sample-detail');
    const opening = button.getAttribute('aria-expanded') !== 'true';
    button.setAttribute('aria-expanded', String(opening));
    const start = detail.hidden ? 0 : getComputedStyle(detail).opacity;
    detail.hidden = false;
    uiMotion.run(
        detail,
        [{ opacity: start }, { opacity: opening ? 1 : 0 }],
        opening ? 220 : 180,
        () => {
            detail.hidden = !opening;
        },
    );
};
