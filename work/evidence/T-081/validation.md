# T081 实际入口与提交前验证

基线 `d08b16bc0f632ee08f4d621f255469c416046593`，Win11 10.0.26200 / Python3.12.14 / uv锁定环境。依赖未升级；最终源码提交由PR绑定。原工程只读，新工程和私有诊断仅在ignored `.local/T081`，不随安装包或Git提交。

用户确认原工程N填反后，Fig1=4、Fig2=2，其余5/4保持。真实UI选择与原工程一致的9个 `(1)` 来源，通过真实DOM配置Fig、蛋白、N和点击开始，没有手工确认裁剪。

| 命令与证据 | exit / 真实结果 |
|---|---|
| `uv run --locked --no-sync pytest tools/wb/tests/test_prominent_band_geometry.py tools/wb/tests/test_prominent_crop_integration.py tools/wb/tests/test_common_band_geometry.py tools/wb/tests/test_fixed_lane_frame.py tools/wb/tests/test_intake_crop_barrier.py tools/wb/tests/test_intake_automatic_crop.py tools/wb/tests/test_reliable_geometry_registration.py -q` | 0；94 passed /9.55s，`.local/T081/scoped-regression.log` |
| 仓库Pyright、Ruff check/format、`python dev.py policy` | 均0；0类型错误、348文件格式正常、离线边界通过。首轮新测试类型标注错误已修，无ignore/放宽规则 |
| `uv run --locked --no-sync pytest .local/T081/test_actual_180.py -q --tb=short`（offscreen、disable-gpu） | 0；1 passed /51.95s，`actual-180-ui-test.log`；正常DOM入口4Fig、9crop、4compose、4measure、1export全部done，最终自动进入results |
| `uv run --locked --no-sync python .local/T081/audit_actual_pixels.py` | 0；9个保存原值TIFF逐像素等于各自原图完整窗口，dtype及N槽位保持；`actual-180-ui/original-pixels.json`。初次脚本读错误层级display_frame抛KeyError，按真实schema修正，未改产品或数据 |
| 原图与输出核对 | 39份原始输入SHA不变；每个crop为policy5/grid2且reviewed=false，均有真实原值资产。完整拼图PNG/TIFF、灰度XLSX/CSV、项目恢复ZIP和完整index实际存在；拼图视觉核对含约−17°GAPDH明显主行 |

真实UI收据与截图：`.local/T081/actual-180-ui/accepted.json`、`results.png`、`project.json`。不把旋转展示像素当定量；Fig组保留原图、对应裁图、预览。开发集通过不等于80%独立实验项目准确率。

初次失败保留：算法多轮反例见algorithm-validation；首轮GUI膜边界拒绝与中间态观察器失败见initial-diagnosis。v2/v3绕过正常DOM开始握手的直接桥调用，后端全部done但页面跟随等待失败，原日志/产物保留；正常DOM入口已通过，早期导航顺序精确根因UNKNOWN，未据猜测修改产品导航。短follow trace未在超时前取得栈，不是通过证据。详细命令见workflow-barrier-validation。

尚待：准确提交独审、服务器必需CI、正常PR合入、新包构建/实际安装与交付。全量测试由必需CI执行，不重复本地全量压力测试。干净Win10、全部员工硬件/物理DPI与独立科学留出未验。
