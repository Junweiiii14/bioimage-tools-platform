# CI temporary environment filesystem experiment

## Original observations (2026-10-20 UTC)

- Accepted product PR17/3680790 passed all four checks and merged as main0f358ac; its Windows910/666.50s and Linux910/353.99s both completed all wheels/real OCR/check0.
- Subsequent main0f quality39347983012 Windows118385136180 was cancelled at the unchanged15-minute job limit. Pytest910passed/762.24s, original exit0/u32=0; wheel functional checks through PNG OCR printed passed, but cancellation interrupted TemporaryDirectory cleanup in shutil.rmtree/os.unlink. The whole command did NOT pass. uv cache was D:/a/_temp/setup-uv-cache while wheel environments were C:/Users/RUNNER~1/AppData/Local/Temp/bioimage-wheel-d7i3g7gz, with repeated hardlink-to-full-copy warnings. This supports a performance hypothesis, not proof that unlink or cross-volume copies caused the entire timeout.
- Unmodified closeout306 quality39348436794 Windows118386602218 and Linux118386601821 both SUCCESS, including all wheels and final command0. This confirms variability; later success does not erase main0f failure.
- Older main3b quality39345065707 Windows118375570511 printed702passed/590.48s then actual child3221225477/u32=0xc0000005, outer1, wheels not run. This different historical native failure remains UNKNOWN and is not explained by temporary directory placement.

## Narrow change and acceptance

Foundation diagnostic and full-check steps set TEMP/TMP to GitHub runner.temp and print resolved Python tempfile.gettempdir() and UV_CACHE_DIR after dependency installation. On Windows the intended effect is to place isolated environments on the cache volume and avoid cross-volume full copies. Linux TMPDIR may take precedence; actual diagnostic output is authoritative. No product/test/tooling runtime, dependency/lock, native observer, exit propagation, assertion, timeout or required check changes. Original15-minute budget remains.

Before merge: final-commit non-author review, frozen rules and all four required CI checks. Inspect actual Windows temporary/wheel/cache paths and hardlink warnings, and require complete check --all exit0 after cleanup; absence of warnings alone is insufficient. No local Qt rerun or installer rebuild is warranted for this CI-environment-only change. New CI result is pending at this commit.

Official rationale: [uv cache filesystem performance](https://docs.astral.sh/uv/concepts/cache/) documents same-filesystem linking versus slower copying; [GitHub runner context](https://docs.github.com/en/actions/reference/workflows-and-actions/contexts#runner-context) defines runner.temp as the job temporary directory. These sources support the experiment, not a root-cause conclusion.

## Preserved raw logs

- `.local/t060-main-0f-windows-timeout.txt` SHA256 `5f9719a85e508134db2bbac1b10f1b27b5a029e3856f83c041bc52edaad710b7`.
- `.local/sync008-main-3b-windows-failure.txt` SHA256 `dd558f35c93fc9b30b750378a4fa38ed4d83f2a5bfbfbc9091de8458a85b0412`.
- `.local/t060-closeout-windows-306-ci.txt` SHA256 `f8d41c50750292278dcd50f55bdf6db22065e16102aa1558183301ecc889509a`.
- `.local/t060-closeout-linux-306-ci.txt` SHA256 `428f9e82d4194a3ffc6feb9e3c8a256fdc52c1b2c0978af71a08b63eb682b32a`.

## Configuration validation correction

Initial364c2d1 quality39350159287 failed before creating any jobs (no test or wheel execution); rules39350164339 passed. The initial job-level env used runner.temp where GitHub context availability forbids runner. Corrected to step-level env on the diagnostic and full-check steps, where runner is supported; setup/native preflight steps retain their original environment. See the official context availability table linked above. This is a configuration failure, not a test success; final successor-head review and all four CI checks remain mandatory.
