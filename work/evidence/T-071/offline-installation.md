# T071 离线构建与安装验收

- 源码：main710bb85de99e88a970f4d0f5613ca554b705ecf7，干净冻结提交构建；文档收尾分支不重建或替换该产物。
- 命令：`uv run --locked --no-sync python -m tooling.build_runtime_candidate --fig-sequence-test --gcc <既有GCC绝对路径> --iscc <既有Inno绝对路径>`，实际0，2026-10-21T02:19:32+08。四锁定wheel、私有CPython3.12.14；GCC15.2.0与Inno6.7.3的既有二进制摘要与工具链记录一致，没有升级。Inno实际压缩42.859s，编译/安装器0。
- 新安装包361,622,169字节、SHA256760b3ee0d7e9c3d22f8f470185791f3c11b26f051babce2c3d4d94f57df75c94，独立AppId/目录/命名空间。`/VERYSILENT /SUPPRESSMSGBOXES /NORESTART /CURRENTUSER`当前用户安装，真实OS0/74.85s、无timeout/error/residue/所属残留；无需重启。
- 所属观察器先有真实0/17/timeout/拒覆盖控制，PID+创建时间限定所属清理；进程退出null、超时或清理前残留绝不转成成功。最终校验49独立纯控制0，详independent-review.md。

## 安装目录的实际三流程

均由Windows PowerShell5.1.26100.9711调用已安装BioImageWB-Candidate.exe，CWD为TEMP、PATH仅System32，清除开发路径与Qt插件注入；父OS退出和残留独立观察。

| 流程 | 报告与实际父进程 |
|---|---|
| Fig顺序 | 13项齐全、17.734s；父29.92s/退出0，6个观察到的所属PID，残留0、开发模块0 |
| 旧采集组 | 17项齐全、10.156s；父13.30s/退出0，8个所属PID，残留0、开发模块0 |
| 灰度/OCR | 7项齐全、8.687s；父13.13s/退出0，6个所属PID，残留0、开发模块0 |

新顺序流程通过顶部两个Fig各N4/5与有序标签、组内选源、一次Start、各一次修正Continue、全部crop→compose→measure→export、两个真实worker/9槽位、逐目标运行事件、原值uint16裁剪/缺失不为零、完整新输出/重开无续跑和所属资源/窗口销毁。计时仅本机验收，不作性能承诺。

私有runtime由-I直接读取executable/sys.path/发行版本，均在新安装根内；分组/顺序报告isolated_imports=true与wb-fig-sequence-test channel一致。预览GPU offscreen环境会输出GLES上下文回退stderr；不把stderr静默无字样当通过条件，实际13/17/7检查和原OS0才是成功证据。

## 随包PS5.1自检与原失败

实际执行安装目录selfcheck.ps1，39.89s，三份新报告passed/errors空，外层及所属观察OS0、无timeout/error/清理前或清理后残留。最初本地外层helper无BOM UTF8包含中文路径，被PS5.1按ANSI解释，PowerShell -File未找到目标，真实退出-196608、没有产品报告；原4文件完整保存在failed-shipped-encoding-20261021-022306并复制到交付验证first-failure-*。只给本地wrapper补UTF8 BOM，归一化去BOM仍是原受审文本；新SHA dc77c54c15c6263a67fb53729d185dec2edfb11d095117249b6ce463a739d268。产品/随包脚本/安装包没有因此改动，不把失败改成0。

## 载荷、交付及旧成果

finalize实际0，7,751构建文件与安装对应文件逐SHA相同；新桌面BioImage-WB-Fig顺序自动化测试版-T071内有安装包、manifest、逐载荷摘要、SHA256SUMS和验证报告。安装目录允许安装器及运行时创建的额外文件，7,751是构建载荷核对范围，不冒称安装目录总文件数。首次finalize stdout受-I默认编码影响显示路径乱码；实际文件系统目录正确，manifest/清单采用明确UTF8，非产物路径改名或丢失。

旧T069安装器和两个manifest共3SHA、旧规划树10份dirty文件SHA、HEAD/status再次核对一致，原项目/历史结果及其他树保留。真实原图/历史原像素证据见validation和独审，不将本机工程验收外推为干净Win10、物理DPI或科学留出。

最终非作者绑定冻结main710bb与安装器摘要Accepted；41校验成员/37证据副本、302源码文件、四wheel176包文件、7751载荷与1257额外pyc来源编译一致。外部CIM仅采样，两个sequence报告worker PID只采到一个；不宣称采全，产品所属关闭/父OS0及独立当前安装根进程数0分别核验。详independent-review.md。
