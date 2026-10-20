# T071 实施验证

基线main6916b3a，规划来源0a966e8，新受管wb-fig-sequence/codex/fig-sequence-automation；Windows、Python3.12.14/uv0.13.0，uv sync --locked --all-groups实际0，第三方锁不变。旧规划稿/工作树与原图/历史/安装保留。

- 编辑前创建T071并实际加载十二scope回执0；七规则与main相同。T070历史回执将在最终显式integration-context中绑定来源提交，不删除回执以通过门禁。
- 初始定向：pytest -q tools/wb/tests/test_intake_grouping.py tools/wb/tests/test_intake_workflow.py tools/wb/tests/test_intake_group_revision.py，24 passed/12.58s，实际0。
- 首增量：加test_intake_sequence.py后30 passed/13.67s，实际0；顺序投影/缺组/余组/来源身份/旧wire/阶段屏障/异常全批暂停。
- 增加80例Hypothesis身份守恒、幂等与JSON往返后，四文件31 passed/6.06s，实际0。Ruff初次仅新测试导入排序1，ruff --fix后0；5文件格式检查0、四用例文件Pyright0。
- 尚未运行完整门禁、实际UI/新真实目录链、独审、PR/服务器检查、构建安装；当前结果不宣告新交互可用或已交付。
