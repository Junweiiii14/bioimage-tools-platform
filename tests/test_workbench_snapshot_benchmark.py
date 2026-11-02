"""A benchmark must not confuse stale state or a skipped renderer with completed work."""

import json
import subprocess

import pytest

from tooling.benchmark_workbench_snapshot import (
    CLICK_DRIVER,
    INTERACTION_DRIVER,
    forward_benchmark_request,
    native_target_expression,
)

HARNESS = r"""
const vm = require('node:vm');
const input = JSON.parse(require('node:fs').readFileSync(0, 'utf8'));
const listeners = [], frames = [], sent = [];
let click, sequence = 0, productionRenderCalls = 0;
const initial = {projectId:'synthetic-test', revision:1, rows:[{id:'r1'}]};
const context = {
  state:structuredClone(initial), console,
  crypto:{randomUUID:()=>`unique-nonce-${++sequence}`},
  performance:{now:()=>100},
  requestAnimationFrame:callback=>frames.push(callback),
  document:{body:{append(){}}, createElement:()=>({style:{},
    addEventListener(name, callback){if(name==='click')click=callback;}})},
  boundaryDiagnostics:{report(){}},
  bridge:{stateChanged:{connect:callback=>listeners.push(callback)},
    request:(action, raw)=>sent.push({action, data:JSON.parse(raw)})},
  render(){
    productionRenderCalls++;
    if(input.scenario==='render_throw')throw new Error('controlled renderer failure');
  },
};
context.window=context;
vm.createContext(context);
if(input.scenario!=='no_handler')listeners.push(raw=>{
  const next=JSON.parse(raw);
  context.state=next;
  if(input.scenario!=='state_without_render') {
    try {context.render();} catch(error) {context.boundaryDiagnostics.report('state',error);}
  }
});
vm.runInContext(input.driver,context);
function emit(nonce) {
  const raw=JSON.stringify({...initial,__r09Nonce:nonce});
  listeners.forEach(callback=>callback(raw));
}
function flush(){while(frames.length)frames.shift()();}
click({isTrusted:true,timeStamp:90});
const first=sent.at(-1).data.__r09Nonce;
if(input.scenario==='stale')emit('old-unrelated-click');
else if(input.scenario==='mismatched')emit('wrong-nonce');
else if(input.scenario==='missing_nonce')emit(undefined);
else {
  emit(first);
  if(input.scenario==='duplicate')emit(first);
  if(input.scenario==='late_before_paint')emit('old-before-paint');
}
flush();
const firstSamples=context.r09.samples.length;
if(input.scenario==='second_click_old_receipt') {
  click({isTrusted:true,timeStamp:90});
  emit(first);flush();
}
console.log(JSON.stringify({samples:context.r09.samples.length,firstSamples,
  errors:context.r09.errors,productionRenderCalls,sent}));
"""


@pytest.mark.parametrize(
    ("scenario", "expected"),
    [
        ("no_handler", 0),
        ("state_without_render", 0),
        ("render_throw", 0),
        ("stale", 0),
        ("mismatched", 0),
        ("missing_nonce", 0),
        ("late_before_paint", 0),
        ("second_click_old_receipt", 1),
        ("duplicate", 1),
        ("happy", 1),
    ],
)
def test_refresh_requires_matching_receipt_and_successful_production_render(
    scenario: str, expected: int
) -> None:
    result = subprocess.run(
        ["node", "-e", HARNESS],
        input=json.dumps({"driver": CLICK_DRIVER, "scenario": scenario}),
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert observed["samples"] == expected, observed
    if scenario == "no_handler":
        assert observed["productionRenderCalls"] == 0
    if scenario in {"happy", "duplicate"}:
        assert observed["errors"] == []
    if scenario == "second_click_old_receipt":
        first, second = (item["data"]["__r09Nonce"] for item in observed["sent"])
        assert first != second


@pytest.mark.parametrize("fail", [False, True])
def test_nonce_forwarding_keeps_original_snapshot_and_restores_after_failure(fail: bool) -> None:
    class Source:
        def __init__(self) -> None:
            self.calls = 0
            self.value: dict[str, object] = {"projectId": "original", "rows": []}

        def snapshot(self) -> dict[str, object]:
            self.calls += 1
            return self.value

    source = Source()
    original = source.snapshot
    requests: list[tuple[str, str]] = []
    observed: list[dict[str, object]] = []
    payload = '{"__r09Nonce":"r09-unique-current-click"}'

    def request(action: str, raw: str) -> None:
        requests.append((action, raw))
        observed.append(source.snapshot())
        if fail:
            raise RuntimeError("controlled real request failure")

    if fail:
        with pytest.raises(RuntimeError, match="controlled real request failure"):
            forward_benchmark_request(source, request, "refresh", payload)
    else:
        forward_benchmark_request(source, request, "refresh", payload)
    assert requests == [("refresh", payload)]
    assert source.calls == 1
    assert observed == [
        {"projectId": "original", "rows": [], "__r09Nonce": "r09-unique-current-click"}
    ]
    assert "__r09Nonce" not in source.value
    assert source.snapshot == original
    assert source.snapshot() == {"projectId": "original", "rows": []}


@pytest.mark.parametrize(
    ("action", "payload"),
    [
        ("refresh", "{}"),
        ("refresh", "bad json"),
        ("select", '{"__r09Nonce":"r09-not-a-refresh"}'),
        ("refresh", '{"__r09Nonce":42}'),
    ],
)
def test_unmarked_requests_do_not_stamp_snapshot_or_rewrite_real_validation(
    action: str, payload: str
) -> None:
    class Source:
        def snapshot(self) -> dict[str, object]:
            return {"original": True}

    source = Source()
    original = source.snapshot

    def request(forwarded_action: str, forwarded_payload: str) -> None:
        assert (forwarded_action, forwarded_payload) == (action, payload)
        assert source.snapshot == original
        assert source.snapshot() == {"original": True}

    forward_benchmark_request(source, request, action, payload)


INTERACTION_HARNESS = r"""
const vm=require('node:vm');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const frames=[]; let capture,clock=100;
const drawer={hidden:input.scenario==='already_open',
  getAnimations:()=>input.scenario==='never_settled' ? [{playState:'running'}] : []};
drawer.hidden=!drawer.hidden;
const status={textContent:'正在执行'};
const context={state:{projectId:'real-observer-fixture',revision:1,selectedId:'row-1'},
  performance:{now:()=>clock+=16},requestAnimationFrame:callback=>frames.push(callback),
  boundaryDiagnostics:{report(){}},document:{documentElement:{dataset:{theme:'forest'}},
    addEventListener:(_,callback)=>capture=callback,
    activeElement:{closest:()=>drawer.hidden ? null : drawer},
    querySelector:selector=>selector==='#drawer' ? drawer :
      selector==='#module-status' ? status : (drawer.hidden ? null : {})
  }};
context.window=context;vm.createContext(context);vm.runInContext(input.driver,context);
Object.assign(context.p006,{pending:true,armed:true,selector:'button',kind:'settings'});
capture({isTrusted:input.scenario!=='untrusted',timeStamp:90,target:{closest:()=>({})}});
if(input.scenario!=='missing_action')drawer.hidden=false;
if(input.scenario==='stale')context.state.revision++;
if(input.scenario==='boundary_error')
  context.boundaryDiagnostics.report('controlled renderer failure');
let flushed=0;
while(frames.length){if(++flushed>1000)throw new Error('Observer did not stop');frames.shift()();}
console.log(JSON.stringify(context.p006));
"""


@pytest.mark.parametrize(
    "scenario,expected",
    [
        ("happy", 1),
        ("already_open", 0),
        ("untrusted", 0),
        ("missing_action", 0),
        ("stale", 0),
        ("boundary_error", 0),
        ("never_settled", 0),
    ],
)
def test_native_interaction_observer_cannot_accept_stale_or_unrendered_receipts(
    scenario: str, expected: int
) -> None:
    result = subprocess.run(
        ["node", "-e", INTERACTION_HARNESS],
        input=json.dumps({"driver": INTERACTION_DRIVER, "scenario": scenario}),
        text=True,
        capture_output=True,
        timeout=10,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    observed = json.loads(result.stdout)
    assert len(observed["samples"]) == expected
    if expected:
        assert observed["samples"][0]["trusted"] is True and observed["errors"] == []
    else:
        assert observed["errors"]


@pytest.mark.parametrize(
    "condition", ["visible", "missing", "offscreen", "moving", "disabled", "hidden", "occluded"]
)
def test_native_target_waits_for_real_stationary_visible_geometry(condition: str) -> None:
    script = r"""
const vm=require('node:vm');
const input=JSON.parse(require('node:fs').readFileSync(0,'utf8'));
const rect={x:10,y:20,left:10,top:20,right:110,bottom:60,width:100,height:40};
if(input.condition==='offscreen')rect.right=1100;
const drawer={getAnimations:()=>input.condition==='moving' ? [{playState:'running'}] : []};
const element={disabled:input.condition==='disabled', getBoundingClientRect:()=>rect,
  closest:selector=>selector==='#drawer' ? drawer : null,contains:()=>false};
const context={innerWidth:1000,innerHeight:800,
  getComputedStyle:()=>({visibility:input.condition==='hidden' ? 'hidden' : 'visible'}),
  document:{querySelectorAll:()=>input.condition==='missing' ? [] : [element],
    elementFromPoint:()=>input.condition==='occluded' ? {} : element}};
console.log(vm.runInNewContext(input.expression,context));
"""
    result = subprocess.run(
        ["node", "-e", script],
        input=json.dumps(
            {"condition": condition, "expression": native_target_expression("button")}
        ),
        text=True,
        capture_output=True,
        check=False,
        timeout=10,
    )
    assert result.returncode == 0, result.stderr
    assert json.loads(result.stdout) == ([60, 40] if condition == "visible" else None)
