"""A benchmark must not confuse stale state or a skipped renderer with completed work."""

import json
import subprocess

import pytest

from tooling.benchmark_workbench_snapshot import CLICK_DRIVER, forward_benchmark_request

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
