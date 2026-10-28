# R06 构建入口与工件哈希

状态：本地实现及定向验证完成，待父任务提交与绑定独审；未进行本轮完整产品构建、安装或发布。源码基线918598c，工作期间主任务已提交05c1a16；仅修改构建入口、工具锁、独立完整性模块及对应测试。

## 核验与实现

旧入口不读toolchain-lock，直接运行传入GCC/windres/Inno；依赖导出`--no-hashes`再与四本地wheel混装。新增`runtime_integrity.verify_toolchain`在创建输出目录或复制运行库前消费固定仓库锁；四工具先比摘要，全部通过才运行版本探针，附带Python/GCC完整树和Inno签名已核文件验证。详见[r06-provenance.md](r06-provenance.md)。无接受任意外部锁或观察hash自动入信任的选项。

第三方依赖继续通过`uv export --locked --no-dev --no-editable --no-emit-workspace`，保留全部锁哈希；`uv pip install --require-hashes --only-binary=:all:`单独安装。四产品wheel使用固定uv内置uv_build及`--require-build-hashes`构建，单独冻结摘要和file-URI requirements，先验证集合与SHA，再`--no-deps --no-index --require-hashes`安装。随后`uv pip check`核验完整依赖；不会将本地项目目录混入第三方hash模式。未改uv.lock/产品依赖或科学行为。

manifest保留既有schema1/2与发行身份字段，新增`build_inputs_contract=verified-runtime-inputs@1`、工具/来源身份、导出requirements及本地requirements SHA、模型摘要。`app/payload-files.json`含schema1、源码commit、所有相对路径的SHA/size；只排除根部两个manifest以避免自引用，嵌套同名文件仍收录。build-manifest保存其SHA。安装器构建前写入app内manifest，安装器完成后外层build-manifest增加实际安装器摘要，保持既有流程。

R12c条件结论：仍有多种独立试验发行及实验室通道；本次工具/依赖核验共用入口即可，AppId/安装目录/QSettings/启动器/卸载保留数据不需要变更。现有profile分支和iss未修改，暂缓发行配置抽象；只有新增/删除活跃通道或已复现身份漂移再启动。

## 验证（Windows，Python3.12.14，uv0.13.0）

- `uv run --locked --no-sync pytest tests/test_runtime_integrity.py -q --tb=short`：**14 passed / 1.29s / exit0**。
- 四工具错SHA均在任何版本探针执行前拒绝；Python标准库、GCC支持库、Inno引擎变更拒绝；摘要正确但版本文本/退出码不符拒绝；正确受控身份回执包含准确锁/文件/树身份。
- 实际builder主入口错GCC时，输出目录尚未创建且copytree未调用。把同一测试加载的builder替换为Git 918598c原始文件，得到**1 failed / 13 deselected / 0.56s / exit1**：已到运行库复制。旧码实验只对copytree设禁止触发器，无真实复制/打包，临时探针位于.local/T082，未替换产品文件。
- 本地四wheel集合增删/内容变化拒绝；真实uv安装结构合法但ZIP注释变化后的wheel时报告Hash mismatch、exit非零。恢复准确bytes后，真实uv使用require-hashes/no-deps/no-index安装四个合成wheel，exit0且4个dist-info存在。只用pytest临时目录。
- 首个wheel负例通过尾部追加bytes触发了uv的ZIP结构拒绝，不能证明hash路径；已改为合法ZIP comment变更后得到Hash mismatch，未放宽断言。首个旧码探针因PowerShell嵌套引号错误未收集测试；改为保存UTF-8脚本后才得到上述有效red。
- 实际`uv export`保留哈希，exit0；实际`uv build --require-build-hashes --package tool-contracts --wheel ...`成功构建0.1.0单wheel、exit0（仅CLI配方探针，不是准确产品commit构建）。0.13.0没有`uv build --locked`选项，未使用虚构选项；内置uv_build由已核uv二进制提供。该版本的require-build-hashes为实验选项，版本固定且实际执行通过。
- 全部真实已核工具/运行库preflight在缓存GCC及本轮Inno副本上exit0。原工具路径消失的fail-closed证据见provenance；无无效重复重试。
- 三个相关Python文件Ruff check/format与严格Pyright全部exit0；git diff --check通过。最终全门禁和准确提交独审待办。

下一步：父任务集成独审；干净冻结提交后完整候选构建与R07安装验证应复用payload清单，并关联准确安装器SHA。源码/工具探针不能填成目标Win10或科学适用性通过。
