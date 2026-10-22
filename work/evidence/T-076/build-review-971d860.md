# T076 build metadata incremental review — Accepted

- Reviewed range: `893e0ad3c8bbf0b63c46b72b1fe8396e34e001af..971d860dec6686abfb72935bfdd22ab0c5b3e93f`.
- Verified branch/HEAD: `codex/t076-platform-home-scroll`, `971d860dec6686abfb72935bfdd22ab0c5b3e93f`; tracked worktree clean at review start.
- Scope: build/installer metadata and documentation of the user's newly explicit installation authorization. The user approved the home styling and requested applying it in the software. Actual installation/delivery evidence will receive a separate review.

## Findings

No actionable regression found in this increment. **Accepted for the reviewed metadata/documentation changes and the explicitly planned installation into a distinct `/DIR`.** This is not installation acceptance or approval to overwrite the old directory.

## Checks and evidence

- The increment changes ten files: three build/installer text files and seven task/product/design/handoff documents. `git diff --name-only 893e0ad..971d860 -- apps/desktop/src packages tools tests` is empty. In addition, `git diff --exit-code d3aff15..971d860 -- apps/desktop/src tests packages tools` returned 0: the independently accepted T076 product/UI and tests are unchanged.
- `tooling/windows_ui_system_test.iss` changes only `AppVersion` to `0.14.0-T076-{#BuildCommit}`, installer filename to `BioImage-WB-x64-T076-Test-{#BuildCommit}-Setup`, and executable version metadata to `0.14.0.76`.
- AppId remains `BioImageTools.WB.UISystemTest`. Builder distribution identity, channel `wb-ui-system-test`, settings namespace `UISystemTest`, desktop/Start-menu shortcut names, and `AppUserModelID` are unchanged. Reusing the existing UI test channel is deliberate; no other candidate channel is selected by the diff.
- `build_runtime_candidate.py` changes only the help string to remove the stale T075 label. Its clean-commit requirement, immutable output directory creation, locked dependency/wheel flow and payload assembly logic remain unchanged. The in-progress build manifest inspected under `.local/releases/runtime-971d860dec66/` identifies commit `971d860dec6686abfb72935bfdd22ab0c5b3e93f` and channel `wb-ui-system-test`; this observation is not a claim that build or installation has completed.
- The installer continues to target `{app}` for payloads and shortcuts. There is no new install/uninstall delete rule, no automatic closure of other applications (`CloseApplications=no` / `RestartApplications=no`), and no product/schema/dependency/permission change. Desktop and Start-menu entries continue to be managed by the existing installer.
- Read the full installer script/readme, related builder selection and manifest code, and every task/product/design/handoff diff. These consistently record that installation was newly authorized, must preserve the old directory/projects, and still needs actual resource/runtime checks and independent review. Earlier preview-only evidence is kept as the completed earlier phase rather than presented as installation proof.
- `git diff --check 893e0ad..971d860` returned 0. No full test suite, installation, uninstallation or product mutation was performed by this reviewer. Only this requested local review report was written.

## Installation boundary for the next review

The unchanged installer does **not** automatically choose a distinct directory for every build. `DefaultDirName` remains the common UI-test path; `UsePreviousAppDir` is unspecified and defaults to `yes`, so the same AppId can reuse the registered prior installation directory. The old comment about separate identity applies to separation from other distributions, not per-build isolation within UISystemTest. The official Inno documentation confirms [previous-directory reuse](https://jrsoftware.org/ishelp/topic_setup_usepreviousappdir.htm) and the [fully qualified `/DIR` override](https://jrsoftware.org/ishelp/topic_setupcmdline.htm).

Therefore the already planned explicit `/DIR` targeting a verified new absolute directory is necessary to preserve `C:/Users/70236/AppData/Local/Programs/BioImage WB 界面系统测试版 5c56f55`. The intended shared shortcuts/uninstall registration may move to the new directory; preserving old installed files is a different claim from retaining a separate uninstall registration for every version. No code change is requested for this explicitly scoped local installation workflow.

The follow-up installation review should verify the executed command/log and resolved target, actual new payload identity/resources, current desktop/Start-menu targets and uninstall registration, preservation of the old directory, and real execution from the newly installed runtime. Clean Win10, physical DPI/IME/latency, scientific holdout and historical native/GPU UNKNOWNs remain outside this metadata acceptance. Final-head CI remains separately required by the task.
