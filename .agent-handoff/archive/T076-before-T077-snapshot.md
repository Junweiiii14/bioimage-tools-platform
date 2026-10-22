# 当前恢复指针

- 唯一当前任务 [T076](../work/tasks/T-076-platform-home-scroll.md)：用户批准工具入口优先的平台首页与整个 Fig 曲线矩阵滚动，最新版实现及同源 HTML。普通本轮任务未新建 goal；此前 T075 goal 已完成，不重开。
- 活动树 `C:/Users/70236/.codex/worktrees/wb-ui-system/bioimage-tools-platform`，分支 `codex/t076-platform-home-scroll`，最新基线 T075 `7fcb8192ada7acf5695e74f23cbe010ffd862966`。ResearchVault 旧 dirty 树、原图、历史、旧预览/安装保持。
- 产品 `d3aff15d53bf04c822976af0dd6b261f2b4dd6a1`，实现平台/WB/项目分层，保留草稿的浏览；矩阵双向滚动、固定对象名、编辑返回、预览手动折叠。独审首轮两个问题（首页导入追加旧项目、连续快照丢定位）已修，原审查者 21 项 / 19.06s / 0，Accepted。
- 作者最终 56 项 / 37.80s / 0；Ruff/格式/Pyright/提交策略通过。静态 12 图有限 ship（1440/960、四主题、WB、末格、编辑底部）；实际字体 Noto。原生硬件/物理延迟没有被 PNG 证明。代码/视觉报告和初次失败见 work/evidence/T-076。
- 桌面 `C:/Users/70236/Desktop/BioImage-平台首页预览-T076-d3aff15`，首页预览.html / 多条带矩阵预览.html；36 文件源码/wheel/预览相等，直接 file 入口和两处程序化指针反馈烟测通过。用户已验收首页并追加实际安装：971d860已安装到Programs/BioImage WB 界面系统测试版 971d860，现用桌面/开始菜单/卸载注册已更新；旧目录保留。
- 安装检查：私有runtime19项26.97s/0，PS5.1主链19检查11.343s/0，7782载荷/36资源一致。12图10张逐像素相等、2张仅文件按钮边缘19像素且RGB差≤2；records相等。用户可见T076窗口已启动并响应，不关闭。安装证据见work/evidence/T-076/installation.md，桌面交付BioImage-工具平台-T076-971d860。
- 安装交付独审971d860 Accepted；最后步骤：最终增量复核及草稿 PR37（base codex/t075-ui-system）当前 HEAD 四必要 CI 全成功。实时结果 `.local/t076-final-ci.json` 并复制桌面；任务已写明成功谓词，不为纯状态反复提交。失败则继续处理，不能将旧 CI 充当本轮。不得合并/公开发布。
- 先核本地/远端 HEAD 和 CI；安装候选保持971d860，UI保持 d3aff15 所审状态时无需重跑无关全量或视觉抛光。最终仅启动等待测试/证据提交的有限复核不能代替产品独审。Linux首轮1201过1败，跨窗口测试改等真实宿主快照；Windows单项4.18s/0。产品/包装仍等同971d860。
- T075 历史：7fcb819 的 CI182 两平台 1192、全部 wheel/四检查 success，最终交付独审 Accepted、goal complete。冻结安装产品 5c56f55；安装 `%LOCALAPPDATA%/Programs/BioImage WB 界面系统测试版 5c56f55`，桌面 T075-5c56f55。无需为 T076 重建或删除。
- 科学留出、干净 Win10、物理 DPI/IME、既有 native UNKNOWN 保留。T076 初始GPU canvas/曲线失败与历史CI180关闭/角度问题不被后继成功抹除。HTTP预览服务曾被自动审批拒绝，未绕过；使用本地文件预览。
