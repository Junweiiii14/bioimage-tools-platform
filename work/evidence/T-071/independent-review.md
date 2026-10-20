# T071 独立审查

## 纯核心增量 edb5a5e

- 非作者审查者 `/root/t064_independent_review`；绑定 edb5a5ed7c5cdbcc98eb034e35dcb3ac6c8b6a97，比较基线 0a966e84c7c07ca26dd71fade4dfe27e6bb4e435。
- 结论：Accepted；未发现可证实的 P0–P2。归档副本与共享工作树隔离，禁止 PySide/pytestqt 导入；未修改共享产品/Git。
- 四个核心测试文件加九个独立反例，共 40 passed / 6.55s，实际退出 0，包含 80 个 Hypothesis 输入。
- 验证新组不继承排除、异常整批暂停、旧策略继续其他 Fig、部分修订保留其他 Fig 已完成证据、标签调整复用同原值运行（合成证据）。
- 隔离比较基线与被审提交的五种旧格式：manifest 1/2/3（grouping 1）及 workflow 1/2，完整 JSON 和 intake/workflow 摘要逐字节相同；比较器与两个子进程实际退出 0。
- 本地细节 `.local/t071-independent-edb5a5e/review.log`。此审查不覆盖后续单一启动、CAS、网页导航、安装诊断与打包；最终产品提交仍需独审。
