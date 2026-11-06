# P023 构建增量与来源

起始8e05f77构建在首个wheel fail-closed，日志位于.local/releases/runtime-8e05f77ff49b-acceptance-p023-local/tool-contracts.log：uv-build==0.13.6 缺构建哈希。当前各包已固定此版本，旧T082内置后端的前提已不成立。未放宽require-build-hashes，新增Windows x64同版本约束。最小真实uv build探针exit0。

来源（2026-11-06核验）：https://docs.astral.sh/uv/concepts/projects/build/ 解释非内置后端需固定版本及哈希；https://pypi.org/pypi/uv-build/0.13.6/json 给出uv_build-0.13.6-py3-none-win_amd64.whl及SHA256 2a2350fbea9a3cf578481b5efc2d333f0477f26696aa615d312866acd170acf6。未修改任何后端、第三方或科学版本。

构建器补六产品wheel，显式选择三extra的锁定运行依赖；directory-only限独立acceptance身份，不生成/执行安装器，故无需Inno，但Python/uv/GCC/windres原摘要校验完整。安装器模式仍需Inno全套校验。新增身份文件进payload清单，窗口标题显示版本/通道/源码。核重型环境仍外置。

定向15测试exit0；六包断言由旧数量4改为准确包名集合（核/BCA加入），未改篡改拒绝、容差、skip或超时。Pyright首次0 errors/3既有重模型源码warnings。首次git commit因未激活pre-commit未提交，改用uv run --locked --no-sync git commit后原钩子正常通过；未绕过钩子。
