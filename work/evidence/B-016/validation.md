# B016发布候选验证

基线4d6ee6ce364780cad24ef09b808740846937714c；独立worktree bioimage-plan-sync，分支codex/b016-plan-v42-sync；Windows/PowerShell/Node/Edge。

- context --task B-016 --scope docs --scope work/evidence/B-016 --scope work/tasks/B-016-plan-v42-sync.md --record：退出0。使用规划树既有Python环境调用本worktree的dev.py；已读规则，未改现行规则。
- MARKED_MODULE_PATH指向已安装marked17.0.5，与renderer现有锁定版本一致；node docs/plans/renderer/build-v42.cjs：退出0，5份HTML。
- node work/evidence/B-016/verify_documents.cjs：退出0；5份文档的1440/390宽度、目录锚点、链接、检索、菜单、打印样式均通过，无脚本错误/外网请求；详细结果同目录html-validation.json。
- Python检查新增/改动Markdown链接（排除代码块）：缺失0。git diff --check：退出0。
- 保留原方案语义，调整可移植链接/发布说明；不更改产品/测试/依赖锁/门禁、P卡/registry或开发handoff。工程规则待接入文本放独立附录，不替换当前规则。
- 未运行本机产品全量、科学方法验证或独立产品审查；文档检查不代表产品已通过。草稿PR不合并，最终接入需要按当时main重新核对。

开发状态检查：PR53的323d59f，规则/环境成功，双平台CI运行；聊天正在修复独审暂停竞态，最终提交可能继续变化。没有发送开发消息或写bioimage-v0。

规则校验：python -m tooling.rule_context check --base 4d6ee6ce364780cad24ef09b808740846937714c --head 4c79342退出0。提交hook policy通过。GitHub草稿PR54已创建，尚未合并，远端CI不在本轮本机通过声明内。
