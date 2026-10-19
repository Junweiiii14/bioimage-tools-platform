# E0/T-053 验证

2026-10-19，本地Win11 10.0.26200、Python3.12.14、Qt6.12.0，产品65ff278。授权规划已保存为c57bfcf，E0无产品代码改动。

| 实际操作 | 退出码 | 结果/限制 |
|---|---|---|
| gh auth status、main API、PR list | 0 | main43d520f；PR16 MERGED，产品依赖PR仍OPEN；未发送评论/消息或修改远端 |
| dev.py context T-053（架构/模块图修改后重载） | 0 | 当前规则与基线已读，回执随任务保存 |
| dev.py doctor | 0 | Python/锁定开发依赖匹配 |
| dev.py smoke-env | 0 | uint16 TIFF/QProcess/离屏Qt，只有环境证据 |
| Start-BioImage.ps1 --verify-launch | 0 | checkout/module/interface全部指向本工作树 |
| pytest tests/test_desktop_entry.py tools/wb/tests/test_instrument_intake.py -q | 0 | 28 passed / 5.33s，原始进程正常退出 |
| 20次新进程 -I -c import wb_tool.api | 20次均0 | p50=1394.7985ms，p95最近秩=1737.0734ms；原始样本及锁SHA在import-baseline.json；不是GUI启动 |
| dev.py policy、git diff --check | 0 | 文档/规则边界核验，不代表新主流程通过 |

首次源码搜索误写不存在project_assets.py，rg退出2；已改为真实模块定位，没有据空结果改代码。私有目录只做只读格式/数量盘点，未冻结仪器来源与科学标注，不宣称真实留出已建。

本轮不重复801全门禁：无产品修改，入口/清单28项已验证。T051历史Qt异常不关闭。独立文档审查绑定本轮提交，结论另记；E1公共接口变更将运行完整门禁及wheel。
