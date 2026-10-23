# Independent closeout CI correction review
Verdict: Accepted (source/test/CI delta review).
Exact HEAD: 5c788d35468cfd69d742cadec7e7fbefedddeba7
Base: 1fbf2dcf1e0b73f160ca0ad8185cca2942238c33
Reviewer: /root/t080_final_review (not implementer).

Reviewed test readiness change and foundation timeout 15 to 20 minutes. The test now waits for native opening completion and matching project/session quant route before selecting review. Original overlay timeout, identity and exact one-dispatch assertions remain. qtbot.TimeoutError exists on the actual fixture, checked by probe. Existing CI evidence repeatedly reaches all pytest tests and wheel work near the 15-minute job limit; a five-minute execution allowance preserves every required command, native probe, assertion, subprocess constraint and failure propagation. No product or dependency change is needed; existing installer remains tied to 79b9db9.

Bounded independent probe: actual sessionStateChanged delivery of a delayed quant route after review made the previously visible crop overlay hidden (old branch passed). This confirms the route competition is possible, not that it was the unique original Linux failure cause. New-order artificial-token comparison did not fully pass: its post-500ms stability assertion failed in v2/v3 (each 1 passed, 1 failed). The injected token diverged from the host's token while normal position feedback remained active; the probe is not faithful enough to claim a complete old/new controlled pass or a product regression. No further probe expansion performed. First probe incorrectly stopped the entire opening timer and omitted required lifecycle-cleanup kwargs; it failed with TypeError and native process exit 0xc0000409. All logs retained under ignored package/review-route-delay*.log; these are reviewer harness failures, not successful evidence. Root's five real test cases passed as separately recorded.

Acceptance rests on code-backed readiness correction with preserved assertions and justified job budget. Exact-head full CI remains required and is not claimed passed here. Original Linux root cause remains unobserved. No tracked files were modified by this reviewer.

Probe commands (QTWEBENGINE_CHROMIUM_FLAGS=--disable-gpu, locked environment):
- uv run --locked --no-sync pytest .local/T080/package/test_review_route_delay.py -q -s --tb=short ; process exit -1073740791 (0xc0000409), log .local/T080/package/review-route-delay.log.
- uv run --locked --no-sync pytest .local/T080/package/test_review_route_delay_v2.py -q -s --tb=short ; exit 1, 1 passed/1 failed in 3.90s, log .local/T080/package/review-route-delay-v2.log.
- uv run --locked --no-sync pytest .local/T080/package/test_review_route_delay_v3.py -q -s --tb=short ; exit 1, 1 passed/1 failed in 3.84s, log .local/T080/package/review-route-delay-v3.log.
All owned probe sessions are terminal. No additional probe or Qt run will be started.
