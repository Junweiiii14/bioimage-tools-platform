'use strict';
// One cancellable animation per node. Commands never wait for animation completion.
window.uiMotion = (() => {
  const active = new Map();
  const system = matchMedia('(prefers-reduced-motion: reduce)');
  const preference = () => system.matches ? 'reduced' : document.documentElement.dataset.motion || 'expressive';
  const duration = (ms) => preference() === 'reduced' ? Math.min(ms, 80) : preference() === 'gentle' ? Math.min(ms, 180) : ms;
  function cancel(node) { const old = active.get(node); if (old) { active.delete(node); old.cancel(); } }
  function run(node, frames, ms = 320, done) {
    if (!node) return;
    cancel(node);
    const animation = node.animate(frames, { duration: duration(ms), easing: 'cubic-bezier(.2,.8,.2,1)', fill: 'both' });
    active.set(node, animation);
    animation.finished.then(() => {
      if (active.get(node) !== animation) return;
      active.delete(node); animation.cancel(); done?.();
    }, () => {});
    return animation;
  }
  function enter(node) {
    const moving = preference() === 'expressive';
    run(node, [{opacity:.65, transform:moving?'translateY(8px)':'none'}, {opacity:1,transform:'none'}]);
  }
  function drawer(open, done) {
    const node = document.getElementById('drawer');
    const wasHidden = node.hidden;
    const style = getComputedStyle(node);
    const start = wasHidden ? {opacity:0,transform:preference()==='reduced'?'none':'translateX(28px)'} : {opacity:style.opacity, transform:style.transform};
    node.hidden=false;
    run(node, [start, {opacity:open?1:0, transform:!open&&preference()!=='reduced'?'translateX(24px)':'none'}], open?320:180, done);
  }
  function sync() {
    document.body.classList.toggle('reduce-motion', preference() === 'reduced');
    if (preference() === 'reduced') for (const animation of active.values()) animation.finish();
    document.querySelectorAll('.home-paper').forEach(node=>{node.style.transform='';});
  }
  system.addEventListener('change', sync);
  window.addEventListener('pagehide', () => {for(const node of active.keys())cancel(node);});
  return {run,enter,drawer,cancel,duration,preference,sync};
})();
