# 用户追加的成熟算法复用准则

2026-11-05，上游转达用户明确要求写入库内正式方案并同步HTML/Git/main，不只停留聊天。P013任务卡已扩充文档范围，context --scope . --record --integration重新运行退出0并读取；旧回执保留在4ebb14d及之前提交，本次仅更新真实source_head，不改规则/门禁。

实际修改 `docs/plans/research-platform-rd.md` 第5节、`docs/plans/workflow-development.md` 第3节及同名HTML。覆盖新研发/基线继续优化之前先检索成熟实现/官方pipeline/预训练模型、适用者直接调用、版本/代码与权重许可、代表性对照/失败/CPU/部署成本、自研证据边界、所有实验模块/算法研发Agent，以及不加繁复审批。既有规则中的“本项目现成实现优先”已改为实证比较，不默认简易自有基线胜出。

检查：`npm run build --prefix docs/plans/renderer` 退出0；五份固定输出中仅两份正文变化，其余Git内容不变。HTML解析检查关键要求文本及相对链接通过；`git diff --check`、`dev.py policy`退出0。未改样式/构建器、产品代码/依赖/测试，不为此启动本机全量。

PR63的4ebb14d仍运行原必需CI，不推送其活动分支新HEAD。此补充先本地提交并立即回传上游，明确尚未main；PR63集成后另走正常PR与必需检查，不能只留下本地补丁。P013最终完成还包括本项main同步与回传。
