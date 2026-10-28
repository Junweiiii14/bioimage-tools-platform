# R11 安装态旧项目工具准备

`tooling/verify_installed_legacy.py` 的prepare阶段直接复用仓库已有schema1–6合成夹具及bb5601a独立renderer金样，输出新的fixture目录和manifest SHA；不生成新的预期答案。verify阶段以显式私有解释器`-I -B`执行，只用公开产品API，核对准确runtime/site路径、独立固定fixture SHA、读取/保存schema身份、固定RGB/完整manifest、归档检查、恢复资产集合/摘要与恢复后重渲染、原图及输入不变。新的报告目录不能在输入/产品/整个安装根内部；旧报告不覆盖。

初版开发运行库六schema自验exit0不能证明检查充分。非作者预审 **Request changes**：①只保护runtime子目录而漏安装根；②只检查恢复项目/原ZIP，漏恢复资产损坏。受控模拟安装根和真实stage后损坏反例都曾被错误接受。随后加入整个安装根绑定保护、恢复资产摘要及重渲染，并要求fixture独立SHA，明确development-self-check与installed-runtime报告范围。

非作者修后预审 **Accepted**，绑定工具文件SHA256 `e967eee81343dcd9fa0490fbda5b226fcdd0786a3c6ffafb7f7c46382be668d2`。命令`.venv/Scripts/python.exe -I -B .local/T082/r11/legacy-review-probes/run.py` **exit0/2.21s**；结果在该目录`run-d342e4de0b634c759d3cf8ba05f6066e/result.json`。安装内输出在mkdir前拒绝；真实恢复后损坏资产在schema1失败并留failed报告；错误pin不创建输出；正常六schema通过，原输入与工具源码不变。这些均为开发运行库探针，不是实际安装证据。

相同关键行为已固化为`tests/test_installed_legacy_verifier.py`，真正`-I -B`子进程执行；额外检查重用旧报告失败且旧字节保持。**4 passed/6.70s/exit0**（`.local/T082/r11/legacy-regression.txt`）；Ruff/严格Pyright通过。测试中模拟安装根仅用于拒绝路径，不冒充真实产品安装。原预审问题和结果保留，不重写为初版通过。

## 冻结后运行方式

先在干净开发检出生成新夹具，单独记录输出SHA和准确提交：

```powershell
uv run --locked --no-sync python -m tooling.verify_installed_legacy prepare --fixtures $taskFixtures
```

R07真实候选/安装载荷验证通过后、启动其他会产生缓存的诊断之前，执行：

```powershell
& $taskPrivatePython -I -B tooling/verify_installed_legacy.py verify --fixtures $taskFixtures --fixtures-sha256 $taskFixtureSHA --output $taskLegacyReport --runtime $taskPrivatePython --site-packages $taskInstalledSite --installation-root $taskInstallRoot
```

`$taskPrivatePython`必须等于`$taskInstallRoot/runtime/python.exe`，site必须等于该根的`runtime/Lib/site-packages`。报告和夹具都放安装根外的新目录。执行后按R07再次核payload，无新增未冻结缓存再启动双流程。旧fixture、失败/成功报告与归档都保留。开发自验必须显式用`--development-self-check`替代安装根，报告会标开发范围，不能列为R11已安装通过。
